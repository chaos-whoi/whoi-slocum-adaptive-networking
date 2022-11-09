from typing import Optional

from adanet.queue.base import IQueue, QueueType
from adanet.types.misc import MonitoredCondition


class Queue(IQueue):

    def __init__(self, type: QueueType, channel: str):
        super(Queue, self).__init__(type, channel)
        assert type == QueueType.CACHE
        self._content: Optional[bytes] = None
        self._event: MonitoredCondition = MonitoredCondition()

    @property
    def length(self) -> int:
        return 0 if self._content is None else 1

    def put(self, data: bytes):
        self._content = data
        with self._event:
            self._event.notify()

    def get(self, block: bool = True) -> Optional[bytes]:
        if self._content is None and not block:
            return None
        with self._event:
            self._event.wait()
        return self._content
