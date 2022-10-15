import time
from collections import Callable
from enum import IntEnum, Enum
from typing import Set

import dataclasses

from .exceptions import InvalidStateError


class NetworkRole(IntEnum):
    CLIENT = 1
    SERVER = 2


class NetworkDeviceType(Enum):
    ETHERNET = "ethernet"
    WIFI = "wifi"
    PPP = "ppp"


class NetworkDeviceState(IntEnum):
    UNKNOWN = 0
    NOLINK = 10
    DISCONNECTED = 20
    CONNECTED = 30

    @staticmethod
    def from_nmcli_output(state: str):
        if state == "connected":
            return NetworkDeviceState.CONNECTED
        if state == "unavailable":
            return NetworkDeviceState.NOLINK
        if state == "unmanaged":
            return NetworkDeviceState.DISCONNECTED
        if state == "disconnected":
            return NetworkDeviceState.DISCONNECTED
        raise ValueError(f"Unknown network state '{state}'")


@dataclasses.dataclass
class NetworkDevice:
    interface: str
    type: NetworkDeviceType
    state: NetworkDeviceState
    connection: str

    @staticmethod
    def from_nmcli_output(info) -> 'NetworkDevice':
        return NetworkDevice(
            interface=info.device,
            type=NetworkDeviceType(info.device_type),
            state=NetworkDeviceState.from_nmcli_output(info.state),
            connection=info.connection,
        )


class Shuttable:

    def __init__(self):
        self._is_shutdown: bool = False
        self._callbacks: Set[Callable] = set()

    @property
    def is_shutdown(self) -> bool:
        return self._is_shutdown

    def register_shutdown_callback(self, cb: Callable):
        if self.is_shutdown:
            classes = [cls.__name__ for cls in type(self).__class__.__subclasses__()]
            raise InvalidStateError(f"Object of type {classes} received a request to register "
                                    f"a new shutdown callback but the instance was already "
                                    f"shutdown.")
        self._callbacks.add(cb)

    def join(self, nap_duration: float = 0.25) -> None:
        """
        Blocks until this Shuttable is shut down.

        :param nap_duration: how often (in seconds) we wake up and check for change in status
        """
        try:
            while not self.is_shutdown:
                time.sleep(nap_duration)
        except KeyboardInterrupt:
            print("Received a Keyboard Interrupt, exiting...")

    def mark_as_shutdown(self):
        self._is_shutdown = True

    def shutdown(self):
        was_shutdown = self.is_shutdown
        # mark as shutdown
        self.mark_as_shutdown()
        # notify callbacks
        if not was_shutdown:
            for cb in self._callbacks:
                cb()
