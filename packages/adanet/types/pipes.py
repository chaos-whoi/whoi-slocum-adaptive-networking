from abc import ABC
from typing import Callable, Optional


class IPipe(ABC):

    def __init__(self, name: str, size: int, *_, **__):
        self._name: str = name
        self._size: int = size
        self._callback: Optional[Callable[[bytes], None]] = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> int:
        return self._size

    def register_callback(self, callback: Callable[[bytes], None]):
        if self._callback is not None:
            raise ValueError("Another callback is already registered")
        self._callback = callback

    def update(self, **kwargs):
        pass

    def _on_data(self, data: bytes):
        if self._callback is None:
            return
        # update size
        self._size = max(self._size, len(data))
        # ---
        self._callback(data)
