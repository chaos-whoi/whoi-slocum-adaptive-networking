import os
from typing import Optional, Any

from persistqueue import SQLiteQueue, Empty

from adanet.constants import QUEUE_PATH
from adanet.queue.base import IQueue


class Queue(IQueue, SQLiteQueue):

    def __init__(self, channel: str):
        IQueue.__init__(self, channel)
        queue_dir: str = os.path.join(QUEUE_PATH, self._channel)
        SQLiteQueue.__init__(self, queue_dir, auto_commit=True)

    def put(self, data: bytes, block: bool = True):
        SQLiteQueue.put(self, data, block=block)

    def get(self, block: bool = True, timeout: Optional[float] = None, default: Any = None) -> \
            Optional[bytes]:
        try:
            return SQLiteQueue.get(self, block=block, timeout=timeout)
        except Empty:
            return default
