from .base import ISink
from ..queue.base import QueueType
from ..queue.sqlite import Queue


class DiskSink(ISink):

    def __init__(self, name: str, size: int, *_, **__):
        super(DiskSink, self).__init__(name=name, size=size)
        self._db: Queue = Queue(QueueType.PERSISTENT, self.name, multithreading=True)

    def recv(self, data: bytes):
        self._db.put(data)
