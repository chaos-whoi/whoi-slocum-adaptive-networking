import os
from typing import Optional, Any

from persistqueue import SQLiteQueue, Empty

from adanet.constants import QUEUE_PATH
from adanet.queue.base import IQueue, QueueType


class Queue(IQueue, SQLiteQueue):

    def __init__(self, type: QueueType, channel: str, multithreading: bool = False,
                 memory: bool = False):
        IQueue.__init__(self, type, channel)
        if memory:
            queue_location: str = ":memory:"
        else:
            queue_location: str = os.path.join(QUEUE_PATH, type.value, self._channel.strip("/"))
            os.makedirs(queue_location, exist_ok=True)
        # make queue
        SQLiteQueue.__init__(self, queue_location, auto_commit=True, multithreading=multithreading)

    def put(self, data: bytes, block: bool = True):
        SQLiteQueue.put(self, data, block=block)

    def get(self, block: bool = True, timeout: Optional[float] = None, default: Any = None) -> \
            Optional[bytes]:
        try:
            return SQLiteQueue.get(self, block=block, timeout=timeout)
        except Empty:
            return default
