from typing import Optional

from .base import ISource
from ..asyncio import Task, loop
from ..constants import FORMULATE_PROBLEM_EVERY_SEC
from ..queue.base import QueueType
from ..queue.sqlite import Queue
from ..time import Clock


class DiskSource(ISource):

    def __init__(self, name: str, size: int, *args, **kwargs):
        super(DiskSource, self).__init__(name=name, size=size, *args, **kwargs)
        self._db: Queue = Queue(QueueType.PERSISTENT, self.name, max_size=-1, multithreading=True)
        self._task: Task = Task(Clock.period(1.0), self._queue_get)
        loop.add_task(self._task)

    @property
    def frequency(self) -> float:
        return self._db.size / FORMULATE_PROBLEM_EVERY_SEC

    @property
    def _is_time(self) -> bool:
        return True

    def set_solution_frequency(self, value: float):
        super(DiskSource, self).set_solution_frequency(value)
        if value <= 0:
            # pause task
            self._task.period = -1
        else:
            self._task.period = Clock.period(1.0 / value)

    def _queue_get(self):
        data: Optional[bytes] = self._db.get(block=False)
        if data is not None:
            self._produce(data)
