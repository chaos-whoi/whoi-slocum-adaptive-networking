from collections import defaultdict
from threading import Thread, Semaphore
from time import sleep
from typing import Set, Dict, Type, Tuple, List

from pyroute2 import IPRoute, IW

from . import Adapter
from .adapters.ethernet import EthernetAdapter
from .adapters.ppp import PPPAdapter
from .adapters.wifi import WifiAdapter
from ..constants import ALLOW_DEVICE_TYPES
from ..types import Shuttable
from ..types.agent import AgentRole
from ..types.misc import FlowWatch
from ..types.network import NetworkDevice, NetworkDeviceType, NetworkDeviceState


class NetworkManager(Shuttable, Thread):
    _adapter_classes = {
        "wifi": WifiAdapter,
        "veth": EthernetAdapter,
        "ppp": PPPAdapter,
    }

    def __init__(self, role: AgentRole):
        Shuttable.__init__(self)
        Thread.__init__(self, daemon=True)
        self._role: AgentRole = role
        self._lock: Semaphore = Semaphore()
        self._adapters: Dict[str, Adapter] = {}
        self._inited: bool = False
        # statistics
        self._interface_flowwatch: Dict[str, FlowWatch] = defaultdict(FlowWatch)
        self._channel_flowwatch: Dict[str, FlowWatch] = defaultdict(FlowWatch)
        # network APIs
        self._ip = IPRoute()
        self._iw = IW()

    @property
    def link_statistics(self) -> Dict[str, Dict[str, float]]:
        with self._lock:
            return {
                k: {
                    "counter": vw.counter,
                    "frequency": vw.frequency,
                    "volume": vw.volume,
                    "speed": vw.speed,
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

    def reset_statistics(self):
        with self._lock:
            for flowwatch in self._interface_flowwatch.values():
                flowwatch.reset()
            for flowwatch in self._channel_flowwatch.values():
                flowwatch.reset()

    def send(self, interface: str, channel: str, data: bytes):
        if interface not in self._adapters:
            if self._inited:
                print(f"ERROR: Unknown interface '{interface}'")
                return
        # ---
        self._adapters[interface].send(channel, data)
        # measure data usage for both link and channel
        self._interface_flowwatch[interface].signal(len(data))
        self._channel_flowwatch[channel].signal(len(data))

    def run(self):
        ignored: Set[str] = set()
        while not self.is_shutdown:
            new_adapters: Set[Adapter] = set()
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

                        # TODO: remove this
                        # device = NetworkDevice.from_nmcli_output(dev_nmcli)

                        device = NetworkDevice(
                            interface=dev,
                            type=NetworkDeviceType(devt),
                            # TODO: figure this out some other way
                            state=NetworkDeviceState.CONNECTED,
                            # TODO: figure this out some other way
                            connection=""
                        )

                        adapter = self._setup_new_adapter(device)
                        self._adapters[dev] = adapter
                        new_adapters.add(adapter)
                    else:
                        self._adapters[dev].update(device)
            # activate new adapters
            for adapter in new_adapters:
                adapter.start()
            self._inited = True
            # TODO: use a constant here
            sleep(4)

    def get_devices(self) -> List[Tuple[str, str]]:
        devices: Dict[str, str] = {}
        # get wifi devices
        for netdev in self._iw.get_interfaces_dict().keys():
            devices[netdev] = "wifi"
        # get all other devices
        for netdev in self._ip.get_links():
            name: str = netdev.get_attr('IFLA_IFNAME')
            link = netdev.get_attr('IFLA_LINKINFO')
            if link is not None:
                link = link.get_attr('IFLA_INFO_KIND')
                devices[name] = link
        # ---
        # noinspection PyTypeChecker
        return list(devices.items())

    def _setup_new_adapter(self, device: NetworkDevice):
        cls: Type[Adapter] = self._adapter_classes[device.type.value]
        return cls(self._role, device)
