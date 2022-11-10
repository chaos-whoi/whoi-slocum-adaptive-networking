import os
from typing import Optional, Any

from persistqueue import SQLiteQueue, Empty

from adanet.asyncio import loop, Task
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
        # internal state
        # - length is taken from the database at the beginning
        self._length: int = self._count()
        # update queue size every once in a while
        task: Task = Task(1.0, self._update_length)
        loop.add_task(task)

    @property
    def size(self) -> int:
        return self._length

    @property
    def length(self) -> int:
        return self._length

    def put(self, data: bytes, block: bool = True):
        if self._max_size >= 0 and self.length >= self._max_size:
            # remove oldest
            _ = SQLiteQueue.get(self, block=False, timeout=0)
            self._length -= 1
        # add new
        SQLiteQueue.put(self, data, block=block)
        self._length += 1

    def get(self, block: bool = True, timeout: Optional[float] = None, default: Any = None) -> \
            Optional[bytes]:
        try:
            self._length -= 1
            return SQLiteQueue.get(self, block=block, timeout=timeout)
        except Empty:
            return default

    def _update_length(self):
        self._length = self._count()
