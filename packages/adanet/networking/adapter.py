from time import sleep
import traceback
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from ipaddress import IPv4Network, IPv4Address
from threading import Thread
from typing import Optional, Dict

import netifaces
import psutil
import zmq

from ..constants import \
    IFACE_BANDWIDTH_CHECK_EVERY_SECS, \
    IFACE_LATENCY_CHECK_EVERY_SECS, \
    ZERO, IFACE_BANDWIDTH_OPTIMISM, IFACE_MIN_BANDWIDTH_BYTES_SEC, DEBUG
from ..exceptions import InterfaceNotFoundError
from ..time import Clock
from ..types import Shuttable
from ..types.network import NetworkDevice
from ..types.agent import AgentRole
from ..zeroconf import zc
from ..zeroconf.services import NetworkPeerService


class Adapter(Shuttable, ABC):

    def __init__(self, role: AgentRole, device: NetworkDevice):
        Shuttable.__init__(self)
        # make sure the interface exists
        iface: str = device.interface
        if iface not in netifaces.interfaces():
            raise InterfaceNotFoundError(iface)
        self._role: AgentRole = role
        self._iface: str = iface
        self._key: str = str(uuid.uuid4())
        # internal state
        self._bandwidth_in: float = 0.0
        self._bandwidth_out: float = 0.0
        self._latency: float = 0.0
        self._socket: Optional[zmq.Socket] = None
        self._nm_device: NetworkDevice = device
        # zeroconf
        # TODO: this should be updated when IP changes or IP is assigned/removed
        # TODO: port here should be the one assigned by the kernel to the zmq socket
        self._zeroconf_srv: Optional[NetworkPeerService] = None
        self._zeroconf_peer_srv: Optional[NetworkPeerService] = None
        # workers
        # TODO: make a worker that checks for IP address
        self._bandwidth_in_worker = AdapterBandwidthWorker(
            self, AdapterBandwidthWorker.BandwidthDirection.IN
        )
        self._bandwidth_out_worker = AdapterBandwidthWorker(
            self, AdapterBandwidthWorker.BandwidthDirection.OUT
        )
        self._latency_worker = AdapterLatencyWorker(self)
        # debug
        if DEBUG:
            self._debug_worker = AdapterDebugger(self)

    @property
    def name(self) -> str:
        """
        The name of the interface.

        :return: the name of the interface
        """
        return self._iface

    @property
    def ip_address(self) -> Optional[IPv4Address]:
        """
        The IP address of the interface.

        :return: the IP address of the interface
        """
        addresses = netifaces.ifaddresses(self.name).get(netifaces.AF_INET, {})
        if addresses:
            address = addresses[0]
            ip = address.get("addr", None)
            return IPv4Address(ip) if ip is not None else None
        return None

    @property
    def ip_network(self) -> Optional[IPv4Network]:
        """
        The IP network of the interface.

        :return: the IP network of the interface
        """
        addresses = netifaces.ifaddresses(self.name).get(netifaces.AF_INET, {})
        if addresses:
            address = addresses[0]
            ip = address.get("addr", None)
            if ip is None:
                return None
            # we have a valid IP
            netmask = address.get("netmask")
            return IPv4Network(f"{ip}/{netmask}", strict=False)
        return None

    @property
    def is_active(self) -> bool:
        """
        Tells us whether interface is active and can be used IF it is connected.

        :return: whether the interface is active
        """
        return self._is_active()

    @property
    def has_link(self) -> bool:
        """
        Tells us whether the interface has an active link, e.g. cable plugged in, wifi handshake.
        This does not mean that the interface is connected to the remote counterpart. Use
        `is_connected` for that.

        :return: whether the interface has a working link
        """
        return self._has_link()

    @property
    def is_connected(self) -> bool:
        """
        Tells us whether the interface has an active connection to the remote counterpart.

        :return: whether the interface has a working link
        """
        return self._has_link() and self._is_connected()

    def start(self):
        """
        Activate adapter workers and monitoring.
        """
        # start workers
        self._bandwidth_in_worker.start()
        self._bandwidth_out_worker.start()
        self._latency_worker.start()
        if DEBUG:
            self._debug_worker.start()

    def send(self, channel: str, data: bytes):
        # TODO: implement this
        print(f"SENDING {len(data)}B for '{channel}' through '{self.name}'")

    def update(self, device: NetworkDevice) -> None:
        """
        Updates the internal state given a new network device object from the network manager.
        """
        self._update(device)
        # TODO: re-enable this
        # if self._socket is None:
        #     self.connect()

    def connect(self):
        context = zmq.Context()
        self._socket = context.socket(zmq.PAIR)
        port: int = 0
        # role: server
        if self._role is AgentRole.SHIP:
            # noinspection PyUnresolvedReferences
            port: int = self._socket.bind_to_random_port(f"tcp://{self.ip_address}")
        # role: client
        if self._role is AgentRole.ROBOT:
            server_ip = self._zeroconf_peer_srv.addresses[0]
            server_port = self._zeroconf_peer_srv.port
            self._socket.connect(f"tcp://{server_ip}:{server_port}")
        # advertise service over mDNS
        self._zeroconf_srv = NetworkPeerService(
            self._role, self._key, self._iface, self.ip_address, self.ip_network, port
        )
        zc.register_service(self._zeroconf_srv)

    @property
    def bandwidth_in(self) -> float:
        return self._bandwidth_in

    @property
    def bandwidth_out(self) -> float:
        return self._bandwidth_out

    @property
    def latency(self) -> float:
        return self._latency

    def set_bandwidth_in(self, value: float) -> float:
        """
        Sets a new value for the interface IN bandwidth. Returns the old value.
        :param value: new value for IN bandwidth in bytes/sec
        :return: old value for bandwidth in bytes/sec
        """
        old = self._bandwidth_in
        self._bandwidth_in = value
        return old

    def set_bandwidth_out(self, value: float) -> float:
        """
        Sets a new value for the interface OUT bandwidth. Returns the old value.
        :param value: new value for OUT bandwidth in bytes/sec
        :return: old value for bandwidth in bytes/sec
        """
        old = self._bandwidth_out
        self._bandwidth_out = value
        return old

    @property
    def estimated_bandwidth_in(self) -> float:
        """
        Estimates the current interface IN bandwidth.
        :return: estimated value for bandwidth in bytes/sec
        """
        if (not self._is_active) or (not self.has_link):
            return 0
        # TODO: here we should include the effect of missing transfers from last session to lower optimism and detect ceilings
        # TODO: we shouldn't react so quickly on the registered bandwidth, we should keep some memory of good sessions
        projection: float = 1 + IFACE_BANDWIDTH_OPTIMISM
        return max(IFACE_MIN_BANDWIDTH_BYTES_SEC, self._bandwidth_in * projection)

    @property
    def estimated_bandwidth_out(self) -> float:
        """
        Estimates the current interface OUT bandwidth.
        :return: estimated value for bandwidth in bytes/sec
        """
        if (not self._is_active) or (not self.has_link):
            return 0
        # TODO: here we should include the effect of missing transfers from last session to lower optimism and detect ceilings
        # TODO: we shouldn't react so quickly on the registered bandwidth, we should keep some memory of good sessions
        projection: float = 1 + IFACE_BANDWIDTH_OPTIMISM
        return max(IFACE_MIN_BANDWIDTH_BYTES_SEC, self._bandwidth_out * projection)

    def set_latency(self, value: float) -> float:
        """
        Sets a new value for the interface latency. Returns the old value.
        :param value: new value for latency
        :return: old value for latency
        """
        old = self._latency
        self._latency = value
        return old

    def __del__(self):
        if hasattr(self, "_zeroconf_srv") and self._zeroconf_srv is not None:
            # de-register services
            zc.unregister_service(self._zeroconf_srv)

    # abstract methods

    @abstractmethod
    def _is_active(self) -> bool:
        """
        Tells us whether interface is active and can be used IF it is connected.

        :return: whether the interface is active
        """
        pass

    @abstractmethod
    def _has_link(self) -> bool:
        """
        Tells us whether the interface has an active link, e.g. cable plugged in, wifi handshake.
        This does not mean that the interface is connected to the remote counterpart. Use
        `is_connected` for that.

        :return: whether the interface has a working link
        """
        pass

    @abstractmethod
    def _is_connected(self) -> bool:
        """
        Tells us whether the interface has an active connection to the remote counterpart.

        :return: whether the interface has a working link
        """
        pass

    @abstractmethod
    def _update(self, device: NetworkDevice) -> None:
        """
        Updates the internal state given a new network device object from the network manager.
        """
        pass

    @abstractmethod
    def _setup(self) -> None:
        """
        Sets up the connection to the remote counterpart.
        """
        pass


class IAdapterWorker(Thread, Shuttable):

    def __init__(self, adapter: Adapter, frequency: float, one_shot: bool = False):
        Thread.__init__(self, daemon=True)
        Shuttable.__init__(self)
        # ---
        self._adapter: Adapter = adapter
        self._period: float = (1.0 / frequency) if frequency > 0 else 0
        self._one_shoot: bool = one_shot

    @abstractmethod
    def _step(self):
        pass

    def run(self) -> None:
        last: float = 0.0
        while not self.is_shutdown:
            is_time = Clock.time() - last > self._period
            if is_time:
                last = Clock.time()
                # noinspection PyBroadException
                try:
                    self._step()
                except Exception:
                    print(traceback.format_exc())
            sleep(Clock.period(0.1))


class AdapterBandwidthWorker(IAdapterWorker):
    class BandwidthDirection(Enum):
        IN = "recv"
        OUT = "sent"

    def __init__(self, adapter: Adapter, direction: BandwidthDirection):
        super(AdapterBandwidthWorker, self).__init__(
            adapter,
            frequency=IFACE_BANDWIDTH_CHECK_EVERY_SECS,
        )
        self._direction: AdapterBandwidthWorker.BandwidthDirection = direction
        self._snetio_field: str = f"bytes_{direction.value}"
        # internal state
        self._bytes: float = 0.0
        self._last: float = 0.0

    def _set_bandwidth(self, value: float):
        if self._direction is AdapterBandwidthWorker.BandwidthDirection.IN:
            self._adapter.set_bandwidth_in(value)
        else:
            self._adapter.set_bandwidth_out(value)

    def _step(self):
        # noinspection PyTypeChecker
        net_usage: Dict[str, object] = psutil.net_io_counters(pernic=True)
        # missing interface?
        if self._adapter.name not in net_usage:
            self._set_bandwidth(ZERO)
            return
        # read net usage
        used_overall: float = getattr(net_usage[self._adapter.name], self._snetio_field)
        # first time reading?
        if self._bytes == 0.0:
            self._bytes = used_overall
            self._last = Clock.time()
            return
        # compute used bandwidth
        used_since: float = used_overall - self._bytes
        bw_since: float = used_since / (Clock.time() - self._last)
        self._set_bandwidth(bw_since)
        # move cursors
        self._last = Clock.time()
        self._bytes = used_overall


class AdapterLatencyWorker(IAdapterWorker):

    def __init__(self, adapter: Adapter):
        super(AdapterLatencyWorker, self).__init__(
            adapter,
            frequency=IFACE_LATENCY_CHECK_EVERY_SECS,
        )

    def _step(self):
        # TODO: implement this
        pass


class AdapterDebugger(IAdapterWorker):

    def __init__(self, adapter: Adapter):
        super(AdapterDebugger, self).__init__(adapter, frequency=2.0)

    def _step(self):
        print(f"""
Interface: {self._adapter.name}
  IPv4 address:               {self._adapter.ip_address}
  IPv4 network:               {self._adapter.ip_network}
  Active:                     {self._adapter.is_active}
  Link:                       {self._adapter.has_link}
  Connected:                  {self._adapter.is_connected}
  Bandwidth IN (used):        {self._adapter.bandwidth_in:.0f} B/s
  Bandwidth IN (estimated):   {self._adapter.estimated_bandwidth_in:.0f} B/s
  Bandwidth OUT (used):       {self._adapter.bandwidth_out:.0f} B/s
  Bandwidth OUT (estimated):  {self._adapter.estimated_bandwidth_out:.0f} B/s
-----------------------------------------------""")
