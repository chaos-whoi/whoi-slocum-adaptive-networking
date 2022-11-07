import time
import traceback
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from ipaddress import IPv4Network, IPv4Address
from threading import Thread
from time import sleep
from typing import Optional, Dict, Iterable

import netifaces
import psutil
import zmq
from pythonping import ping
from pythonping.executor import Response
from zeroconf import ServiceNameAlreadyRegistered, NonUniqueNameException

from ..constants import \
    IFACE_BANDWIDTH_CHECK_EVERY_SECS, \
    IFACE_PING_CHECK_EVERY_SECS, \
    IFACE_BANDWIDTH_OPTIMISM, \
    IFACE_MIN_BANDWIDTH_BYTES_SEC, \
    DEBUG, \
    ZERO, \
    INFTY, \
    ZMQ_SERVER_PORT
from ..exceptions import InterfaceNotFoundError
from ..time import Clock
from ..types import Shuttable
from ..types.agent import AgentRole
from ..types.message import Message
from ..types.misc import Reminder
from ..types.network import NetworkDevice, IAdapter, INetworkManager
from ..zeroconf import zc
from ..zeroconf.services import NetworkPeerService


class Adapter(Shuttable, IAdapter, ABC):

    def __init__(self, role: AgentRole, device: NetworkDevice, network_manager: INetworkManager,
                 remote: Optional[IPv4Address] = None):
        Shuttable.__init__(self)
        # make sure the interface exists
        iface: str = device.interface
        if iface not in netifaces.interfaces():
            raise InterfaceNotFoundError(iface)
        self._role: AgentRole = role
        self._iface: str = iface
        self._key: str = str(uuid.uuid4())
        self._network_manager: INetworkManager = network_manager
        # internal state
        self._present: bool = True
        self._has_ping: bool = False
        self._connected: bool = False
        self._bandwidth_in: float = 0.0
        self._bandwidth_out: float = 0.0
        self._latency: float = 0.0
        self._port: int = ZMQ_SERVER_PORT
        self._context: zmq.Context = zmq.Context()
        self._socket: Optional[zmq.Socket] = None
        self._device: NetworkDevice = device
        self._remote: Optional[IPv4Address] = remote
        if self._remote:
            print(f"Forcing interface '{device.interface}' to talk to remote IP {self._remote}")
        # role: sink (server)
        if self._role is AgentRole.SINK:
            self.bind()
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
        self._ping_worker = AdapterPingWorker(self)
        self._mailman_worker = AdapterMailman(self)
        # sources listen for heartbeat signal
        self._heartbeat_worker: AdapterHeartbeatWorker = AdapterHeartbeatWorker(self, role)
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
    def device(self) -> NetworkDevice:
        """
        The underlying network device.

        :return: the underlying network device
        """
        return self._device

    @property
    def remote(self) -> Optional[IPv4Address]:
        """
        The IP address of the remote counterpart.

        :return: the IP address of the remote counterpart
        """
        return self._remote

    @property
    def socket(self) -> Optional[zmq.Socket]:
        """
        The established socket between the sides (if any).

        :return: the established socket
        """
        return self._socket

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
        return self._present

    @property
    def has_link(self) -> bool:
        """
        Tells us whether the interface has an active link, e.g. cable plugged in, wifi handshake.
        This does not mean that the interface is connected to the remote counterpart. Use
        `is_connected` for that.

        :return: whether the interface has a working link
        """
        return self.ip_address is not None

    @property
    def has_ping(self) -> bool:
        """
        Tells us whether the interface has an active ping with the other side.
        This does not mean that the interface is connected to the remote counterpart. Use
        `is_connected` for that.

        :return: whether the interface has an established ping
        """
        return self._has_ping

    @property
    def is_connected(self) -> bool:
        """
        Tells us whether the interface has an active connection to the remote counterpart.

        :return: whether the interface has a working link
        """
        return self.has_link and self._connected

    def start(self):
        """
        Activate adapter workers and monitoring.
        """
        # start workers
        self._bandwidth_in_worker.start()
        self._bandwidth_out_worker.start()
        self._ping_worker.start()
        self._heartbeat_worker.start()
        # role: sink (server)
        if self._role is AgentRole.SINK:
            self._mailman_worker.start()
        if DEBUG:
            self._debug_worker.start()

    def lost(self):
        """
        Deactivate adapter workers and monitoring.
        """
        self._present = False
        # TODO: implement this
        # self._bandwidth_in_worker.start()
        # self._bandwidth_out_worker.start()
        # self._latency_worker.start()
        # if DEBUG:
        #     self._debug_worker.start()

    def send(self, message: Message):
        if not self.is_connected or self._socket is None:
            # TODO: mark the message as 'lost'
            return
        # serialize message
        data: bytes = message.serialize()
        # send data to the socket
        self._socket.send(data)

    def recv(self, data: bytes):
        # deserialize message
        message: Message = Message.deserialize(data)
        # send message up to the network manager
        self._network_manager.recv(self.name, message)
        # if this is a server, mark as connected
        if self._role is AgentRole.SINK:
            self.set_connected(True)

    def bind(self):
        self._socket = self._context.socket(zmq.PAIR)
        # noinspection PyUnresolvedReferences
        if self._port == 0:
            address: str = f"tcp://{self.ip_address}"
            print(f"Binding to random port on {address}...")
            self._port = self._socket.bind_to_random_port(address)
        else:
            address: str = f"tcp://{self.ip_address}:{self._port}"
            print(f"Binding to {address}...")
            self._socket.bind(address)
        print(f"Binded to {address}")
        # advertise service over mDNS
        self._zeroconf_srv = NetworkPeerService(
            self._role, self._key, self._iface, self.ip_address, self.ip_network, self._port
        )
        try:
            zc.register_service(self._zeroconf_srv)
        except (ServiceNameAlreadyRegistered, NonUniqueNameException):
            zc.update_service(self._zeroconf_srv)

    def connect(self):
        # no network configuration => no connection
        if self._remote is None and self._zeroconf_peer_srv is None:
            return
        # figure out server IP and port
        if self._remote is not None:
            # static network configuration
            server_ip = self._remote
            server_port = ZMQ_SERVER_PORT
        else:
            # zeroconf network configuration
            server_ip = self._zeroconf_peer_srv.addresses[0]
            server_port = self._zeroconf_peer_srv.port
        # connect
        self._socket = self._context.socket(zmq.PAIR)
        address: str = f"tcp://{server_ip}:{server_port}"
        print(f"Connecting to {address}...")
        self._socket.connect(address)
        print(f"Connected to {address}")

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

    def set_latency(self, value: float) -> float:
        """
        Sets a new value for the interface latency. Returns the old value.
        :param value: new value for latency
        :return: old value for latency
        """
        old = self._latency
        self._latency = value
        return old

    def set_has_ping(self, has_ping: bool):
        self._has_ping = has_ping
        # TODO: what if the interface goes away and then comes back?
        if self._socket is None:
            self.connect()

    def set_connected(self, connected: bool):
        self._connected = connected

    @property
    def estimated_bandwidth_in(self) -> float:
        """
        Estimates the current interface IN bandwidth.
        :return: estimated value for bandwidth in bytes/sec
        """
        if (not self.is_active) or (not self.has_link):
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
        if (not self.is_active) or (not self.has_link):
            return 0
        # TODO: here we should include the effect of missing transfers from last session to lower optimism and detect ceilings
        # TODO: we shouldn't react so quickly on the registered bandwidth, we should keep some memory of good sessions
        projection: float = 1 + IFACE_BANDWIDTH_OPTIMISM
        return max(IFACE_MIN_BANDWIDTH_BYTES_SEC, self._bandwidth_out * projection)

    def __del__(self):
        if hasattr(self, "_zeroconf_srv") and self._zeroconf_srv is not None:
            # de-register services
            zc.unregister_service(self._zeroconf_srv)


class AdapterHeartbeatWorker(Thread, Shuttable):

    def __init__(self, adapter: Adapter, role: AgentRole):
        Thread.__init__(self, daemon=True)
        Shuttable.__init__(self)
        # ---
        self._adapter: Adapter = adapter
        self._role: AgentRole = role

    def run(self) -> None:
        while not self.is_shutdown:
            if self._adapter.socket is None:
                # TODO: use variable here
                time.sleep(1)
                continue
            # noinspection PyBroadException
            try:
                if self._role is AgentRole.SOURCE:
                    self._adapter.socket.recv(copy=False)
                    self._adapter.set_connected(True)

                if self._role is AgentRole.SINK:
                    self._adapter.socket.send(b"x")
                    # TODO: use variable here
                    time.sleep(5)
            except Exception:
                print(traceback.format_exc())


class AdapterMailman(Thread, Shuttable):

    def __init__(self, adapter: Adapter):
        Thread.__init__(self, daemon=True)
        Shuttable.__init__(self)
        # ---
        self._adapter: Adapter = adapter

    def _consume_from_pipe(self):
        data: bytes = self._adapter.socket.recv(copy=False)
        self._adapter.recv(data)

    def run(self) -> None:
        while not self.is_shutdown:
            if self._adapter.socket is None:
                # TODO: use variable here
                time.sleep(1)
                continue
            # noinspection PyBroadException
            try:
                self._consume_from_pipe()
            except Exception:
                print(traceback.format_exc())


class IAdapterWorker(Thread, Shuttable):

    def __init__(self, adapter: Adapter, frequency: float, one_shot: bool = False):
        Thread.__init__(self, daemon=True)
        Shuttable.__init__(self)
        # ---
        self._adapter: Adapter = adapter
        self._reminder: Reminder = Reminder(frequency=frequency, right_away=True)
        self._one_shoot: bool = one_shot

    @abstractmethod
    def _step(self):
        pass

    def run(self) -> None:
        while not self.is_shutdown:
            if self._reminder.is_time():
                # noinspection PyBroadException
                try:
                    self._step()
                except Exception:
                    print(traceback.format_exc())
            # NOTE: this effectively fixes the maximum frequency of these workers to 10Hz
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
        now: float = Clock.time()
        used_overall: float = getattr(net_usage[self._adapter.name], self._snetio_field)

        # DEBUG:
        # print(net_usage[self._adapter.name])
        # DEBUG:

        # first time reading?
        if self._bytes == 0.0:
            self._bytes = used_overall
            self._last = now
            return
        # compute used bandwidth
        used_since: float = used_overall - self._bytes
        bw_since: float = used_since / (now - self._last)
        self._set_bandwidth(bw_since)
        # move cursors
        self._last = now
        self._bytes = used_overall


class AdapterPingWorker(IAdapterWorker):

    def __init__(self, adapter: Adapter):
        super(AdapterPingWorker, self).__init__(
            adapter,
            frequency=1.0 / Clock.period(IFACE_PING_CHECK_EVERY_SECS),
        )

    def _step(self):
        # no link => no connection => no ping needed
        if not self._adapter.has_link:
            self._adapter.set_has_ping(False)
            self._adapter.set_connected(False)
            self._adapter.set_latency(INFTY)
            self._adapter.set_bandwidth_in(0)
            self._adapter.set_bandwidth_out(0)
            return
        # test for connection
        server: Optional[IPv4Address] = self._adapter.remote
        if server is not None:
            responses: Iterable[Response] = ping(str(server), timeout=4, count=2, interval=0)

            # DEBUG:
            # print(responses)
            # DEBUG:

            successes: int = 0
            latency: float = 0
            for response in responses:
                successes += int(response.success)
                latency += response.time_elapsed
            has_ping: bool = successes > 0
            self._adapter.set_has_ping(has_ping)
            if successes > 0:
                # we have at least one success => the adapter is connected, compute average latency
                self._adapter.set_latency(latency / successes)


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
  Ping:                       {self._adapter.has_ping}
  Connected:                  {self._adapter.is_connected}
  Bandwidth IN (used):        {self._adapter.bandwidth_in:.0f} B/s
  Bandwidth IN (estimated):   {self._adapter.estimated_bandwidth_in:.0f} B/s
  Bandwidth OUT (used):       {self._adapter.bandwidth_out:.0f} B/s
  Bandwidth OUT (estimated):  {self._adapter.estimated_bandwidth_out:.0f} B/s
-----------------------------------------------""")
