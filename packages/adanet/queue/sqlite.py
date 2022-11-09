import os
from typing import Optional, Any

from persistqueue import SQLiteQueue, Empty

from adanet.constants import QUEUE_PATH
from adanet.queue.base import IQueue, QueueType


class Queue(IQueue, SQLiteQueue):

    def __init__(self, type: QueueType, channel: str, max_size: int, multithreading: bool = False,
                 memory: bool = False):
        IQueue.__init__(self, type, channel)
        self._max_size: int = max_size
        # in memory database
        if memory:
            queue_location: str = ":memory:"
        else:
            queue_location: str = os.path.join(QUEUE_PATH, type.value, self._channel.strip("/"))
            os.makedirs(queue_location, exist_ok=True)
        # make queue
        SQLiteQueue.__init__(self, queue_location, auto_commit=True, multithreading=multithreading)

    @property
    def length(self) -> int:
        return self.size

    def put(self, data: bytes, block: bool = True):
        if self.length >= self._max_size:
            # remove oldest
            _ = SQLiteQueue.get(self, block=False, timeout=0)
        # add new
        SQLiteQueue.put(self, data, block=block)

    def get(self, block: bool = True, timeout: Optional[float] = None, default: Any = None) -> \
            Optional[bytes]:
        try:
            return SQLiteQueue.get(self, block=block, timeout=timeout)
        except Empty:
            return default
