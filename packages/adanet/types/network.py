from enum import IntEnum, Enum

import dataclasses


class NetworkDeviceType(Enum):
    ETHERNET = "veth"
    WIFI = "wifi"
    PPP = "ppp"


@dataclasses.dataclass
class NetworkDevice:
    interface: str
    type: NetworkDeviceType
