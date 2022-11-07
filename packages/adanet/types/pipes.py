from abc import ABC
from typing import Callable, Optional


class IPipe(ABC):

    def __init__(self, size: int, *_, **__):
        self._size: int = size
        self._callback: Optional[Callable[[bytes], None]] = None

    def register_callback(self, callback: Callable[[bytes], None]):
        if self._callback is not None:
            raise ValueError("Another callback is already registered")
        self._callback = callback

    def update(self, **kwargs):
        pass

    def _on_data(self, data: bytes):
        if self._callback is None:
            return
        self._callback(data)
