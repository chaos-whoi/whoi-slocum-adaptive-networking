from abc import abstractmethod, ABC
from enum import IntEnum, Enum

import dataclasses

from adanet.types.message import Message


class NetworkDeviceType(Enum):
    ETHERNET = "veth"
    WIFI = "wifi"
    PPP = "ppp"


@dataclasses.dataclass
class NetworkDevice:
    interface: str
    type: NetworkDeviceType


class INetworkManager(ABC):

    @abstractmethod
    def send(self, interface: str, message: Message):
        pass

    @abstractmethod
    def recv(self, interface: str, message: Message):
        pass


class ISwitchboard(ABC):

    @abstractmethod
    def send(self, message: Message):
        pass

    @abstractmethod
    def recv(self, message: Message):
        pass


class IAdapter(ABC):

    @abstractmethod
    def send(self, message: Message):
        pass
