from abc import ABC, abstractmethod
from typing import Optional


class IQueue(ABC):

    def __init__(self, channel: str):
        self._channel: str = channel

    @abstractmethod
    def put(self, data: bytes):
        pass

    @abstractmethod
    def get(self, block: bool = True) -> Optional[bytes]:
        pass
