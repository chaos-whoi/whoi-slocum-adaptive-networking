from collections import defaultdict
from ipaddress import IPv4Address
from threading import Thread, Semaphore
from time import sleep
from typing import Set, Dict, Type, Tuple, List, Callable, Optional

from pyroute2 import IPRoute, IW

from . import Adapter
from .adapters.ethernet import EthernetAdapter
from .adapters.ppp import PPPAdapter
from .adapters.wifi import WifiAdapter
from ..asyncio import Task, loop
from ..constants import \
    ALLOW_DEVICE_TYPES, \
    NETWORK_LOG_EVERY_SECS, \
    NETWORK_IFACES_DISCOVERY_EVERY_SECS
from ..time import Clock
from ..types import Shuttable
from ..types.agent import AgentRole
from ..types.message import Message
from ..types.misc import FlowWatch
from ..types.network import NetworkDevice, NetworkDeviceType, INetworkManager, ISwitchboard
from ..types.problem import Problem, Link
from ..types.report import Report


class NetworkManager(Shuttable, INetworkManager, Thread):
    _adapter_classes = {
        "wifi": WifiAdapter,
        "veth": EthernetAdapter,
        "ppp": PPPAdapter,
    }

    def __init__(self, role: AgentRole, problem: Problem):
        Shuttable.__init__(self)
        Thread.__init__(self, daemon=True)
        self._role: AgentRole = role
        self._problem: Problem = problem
        self._switchboard: Optional[ISwitchboard] = None
        self._lock: Semaphore = Semaphore()
        self._adapters: Dict[str, Adapter] = {}
        self._inited: bool = False
        # known links
        self._known_links: Dict[str, Link] = {}
        for link in problem.links:
            self._known_links[link.interface] = link
        # if a problem is given and the 'links' are populated, stick to those links
        self._whitelisted_links: Optional[Set[str]] = None
        if self._problem.links is not None:
            self._whitelisted_links = set()
            for link in self._problem.links:
                self._whitelisted_links.add(link.interface)
        self._ignored_links: Set[str] = set()
        # callbacks
        self._new_iface_cbs: Set[Callable] = set()
        self._lost_iface_cbs: Set[Callable] = set()
        # statistics
        self._interface_flowwatch: Dict[str, FlowWatch] = defaultdict(FlowWatch)
        self._channel_flowwatch: Dict[str, FlowWatch] = defaultdict(FlowWatch)
        # network APIs
        self._ip = IPRoute()
        self._iw = IW()
        # create network monitor task
        self._monitor_task: Task = NetworkMonitorTask(period=Clock.period(NETWORK_LOG_EVERY_SECS))

    @property
    def switchboard(self) -> ISwitchboard:
        return self._switchboard

    @switchboard.setter
    def switchboard(self, switchboard: ISwitchboard):
        self._switchboard = switchboard

    @property
    def adapters(self) -> Set[Adapter]:
        return set(self._adapters.values())

    @property
    def link_statistics(self) -> Dict[str, Dict[str, float]]:
        with self._lock:
            return {
                k: {
                    "counter": vw.counter,
                    "frequency": vw.frequency,
                    "volume": vw.volume,
                    "speed": vw.speed,
                    "connected": int(self._adapters[k].is_connected)
                } for k, vw in self._interface_flowwatch.items()
            }

    @property
    def channel_statistics(self) -> Dict[str, Dict[str, float]]:
        with self._lock:
            return {
                k: {
                    "counter": vw.counter,
                    "frequency": vw.frequency,
                    "volume": vw.volume,
                    "speed": vw.speed,
                } for k, vw in self._channel_flowwatch.items()
            }

    def adapter(self, interface: str) -> Optional[Adapter]:
        return self._adapters.get(interface, None)

    def reset_statistics(self):
        with self._lock:
            for flowwatch in self._interface_flowwatch.values():
                flowwatch.reset()
            for flowwatch in self._channel_flowwatch.values():
                flowwatch.reset()

    def on_new_interface(self, callback: Callable[[Adapter], None]):
        with self._lock:
            self._new_iface_cbs.add(callback)

    def on_interface_lost(self, callback: Callable[[Adapter], None]):
        with self._lock:
            self._lost_iface_cbs.add(callback)

    def send(self, interface: str, message: Message):
        if interface not in self._adapters:
            if self._inited:
                print(f"ERROR: Unknown interface '{interface}'")
            return
        # send data down to the adapter
        self._adapters[interface].send(message)
        # measure data usage for both link and channel
        self._interface_flowwatch[interface].signal(len(message.payload))
        self._channel_flowwatch[message.channel].signal(len(message.payload))

    def recv(self, interface: str, message: Message):
        # send data up to the switchboard
        self._switchboard.recv(message)
        # measure data usage for both link and channel
        self._interface_flowwatch[interface].signal(len(message.payload))
        self._channel_flowwatch[message.channel].signal(len(message.payload))

    def start(self) -> None:
        # activate network monitor
        loop.add_task(self._monitor_task, self)
        # run this thread
        super(NetworkManager, self).start()

    def run(self):
        ignored: Set[str] = set()
        while not self.is_shutdown:
            new_adapters: Set[Adapter] = set()
            lost_adapters: Set[str] = set(self._adapters.keys())
            for dev, devt in self.get_devices():
                # filter devices based on their type
                if devt not in self._adapter_classes:
                    if dev not in ignored:
                        print(f"Ignoring device '{dev}' of (unsupported) type '{devt}'")
                        ignored.add(dev)
                    continue
                # filter devices based on user preferences
                if "all" not in ALLOW_DEVICE_TYPES and devt not in ALLOW_DEVICE_TYPES:
                    if dev not in ignored:
                        print(f"Ignoring device '{dev}' of (excluded) type '{devt}'")
                        ignored.add(dev)
                    continue
                # ---
                with self._lock:
                    if dev not in self._adapters:
                        print(f"Attaching to device '{dev}' of type '{devt}'")
                        device = NetworkDevice(
                            interface=dev,
                            type=NetworkDeviceType(devt)
                        )
                        adapter = self._setup_new_adapter(device)
                        self._adapters[dev] = adapter
                        new_adapters.add(adapter)
                    # mark as NOT lost
                    if dev in lost_adapters:
                        lost_adapters.remove(dev)
            # activate new adapters
            for adapter in new_adapters:
                adapter.start()
            # notify the presence of new adapters
            for adapter in new_adapters:
                for cb in self._new_iface_cbs:
                    cb(adapter)
            # deactivate lost adapters
            for dev in lost_adapters:
                adapter = self._adapters[dev]
                adapter.lost()
            # notify the presence of new adapters
            for dev in lost_adapters:
                adapter = self._adapters[dev]
                print(f"Detaching from device '{dev}' of type '{adapter.device.type.value}'")
                for cb in self._lost_iface_cbs:
                    cb(adapter)
            # mark as inited
            self._inited = True
            # ---
            sleep(NETWORK_IFACES_DISCOVERY_EVERY_SECS)

    def get_devices(self) -> List[Tuple[str, str]]:
        devices: Dict[str, str] = {}
        # get wifi devices
        iw_devs = self._iw.get_interfaces_dict().keys()
        iw_devs_names = []
        for netdev in iw_devs:
            if not netdev:
                continue
            devices[netdev] = "wifi"
            iw_devs_names.append(netdev)
        # get all other devices
        any_devs = self._ip.get_links()
        any_devs_names = []
        for netdev in any_devs:
            if not netdev:
                continue
            name: str = netdev.get_attr('IFLA_IFNAME')
            link = netdev.get_attr('IFLA_LINKINFO')
            if link is not None:
                link = link.get_attr('IFLA_INFO_KIND')
                devices[name] = link
                any_devs_names.append(name)
            elif "eth" in name or "eno" in name:
                # TODO: this is to avoid cases where IPRoute() fails at finding the devices' information
                devices[name] = "veth"
                any_devs_names.append(name)
        # print(f"Generic IP devices found: {any_devs_names}")
        # print(f"Wifi devices found: {iw_devs_names}")
        # if a problem is given and the 'links' are populated, stick to those links
        if self._whitelisted_links is not None:
            for device in list(devices.keys()):
                if device not in self._whitelisted_links:
                    # print out (only once) that we are ignoring this link
                    if self._role is AgentRole.SOURCE and device not in self._ignored_links:
                        print(f"Interface '{device}' of type '{devices[device]}' is not listed in "
                              f"the problem definition, it will not be used.")
                        # mark this device as 'ignored'
                        self._ignored_links.add(device)
                    # remove device from list
                    del devices[device]
        # ---
        # noinspection PyTypeChecker
        return list(devices.items())

    def _setup_new_adapter(self, device: NetworkDevice):
        cls: Type[Adapter] = self._adapter_classes[device.type.value]
        link: Optional[Link] = self._known_links.get(device.interface)
        remote: Optional[IPv4Address] = link.server if link else None
        return cls(role=self._role, device=device, remote=remote, network_manager=self)


class NetworkMonitorTask(Task):

    def step(self, nm: NetworkManager):
        # collect link statistics
        for interface, stats in nm.link_statistics.items():
            Report.log({
                f"link/{interface}": stats
            })
        # collect channel statistics
        for channel, stats in nm.channel_statistics.items():
            Report.log({
                f"channel/{channel.strip('/')}": stats
            })
