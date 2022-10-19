from typing import Set, Callable


class AbsDataSource:

    def __init__(self, size: int):
        self._size: int = size
        self._callbacks: Set[Callable[[bytes], None]] = set()

    def register_callback(self, callback: Callable[[bytes], None]):
        self._callbacks.add(callback)

    def _on_data(self, data: bytes):
        for callback in self._callbacks:
            callback(data)


class AbsDataSink:

    def __init__(self, size: int):
        self._size: int = size
        self._callbacks: Set[Callable[[bytes], None]] = set()

    def register_callback(self, callback: Callable[[bytes], None]):
        self._callbacks.add(callback)

    def send(self, data: bytes):
        for callback in self._callbacks:
            callback(data)
