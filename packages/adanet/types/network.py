from enum import IntEnum, Enum

import dataclasses


class NetworkDeviceType(Enum):
    ETHERNET = "veth"
    WIFI = "wifi"
    PPP = "ppp"


class NetworkDeviceState(IntEnum):
    UNKNOWN = 0
    NOLINK = 10
    DISCONNECTED = 20
    CONNECTED = 30

    # @staticmethod
    # def from_nmcli_output(state: str):
    #     if state == "connected":
    #         return NetworkDeviceState.CONNECTED
    #     if state == "unavailable":
    #         return NetworkDeviceState.NOLINK
    #     if state == "unmanaged":
    #         return NetworkDeviceState.DISCONNECTED
    #     if state == "disconnected":
    #         return NetworkDeviceState.DISCONNECTED
    #     raise ValueError(f"Unknown network state '{state}'")


@dataclasses.dataclass
class NetworkDevice:
    interface: str
    type: NetworkDeviceType
    state: NetworkDeviceState
    connection: str

    # @staticmethod
    # def from_nmcli_output(info) -> 'NetworkDevice':
    #     return NetworkDevice(
    #         interface=info.device,
    #         type=NetworkDeviceType(info.device_type),
    #         state=NetworkDeviceState.from_nmcli_output(info.state),
    #         connection=info.connection,
    #     )
