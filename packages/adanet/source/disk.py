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
        # period = -1 means paused, the function set_solution_frequency below will resume if solution allows
        self._queue_task: Task = Task(Clock.period(1.0), self._queue_get)
        loop.add_task(self._queue_task)
        # wait for at least one message to be available so that we can compute the message size
        self._read_message_size_task: Task = Task(Clock.period(1.0), self._read_message_size)
        loop.add_task(self._read_message_size_task)

    @property
    def frequency(self) -> float:
        return self._db.size / FORMULATE_PROBLEM_EVERY_SEC

    @property
    def queue_length(self) -> int:
        return self._db.length

    @property
    def _is_time(self) -> bool:
        return True

    def set_solution_frequency(self, value: float):
        super(DiskSource, self).set_solution_frequency(value)
        if value <= 0:
            # pause task
            self._queue_task.period = -1
        else:
            self._queue_task.period = Clock.period(1.0 / value)

    def _queue_get(self):
        data: Optional[bytes] = self._db.get(block=False)
        if data is not None:
            self._produce(data)

    def _read_message_size(self):
        # if we know the message size already, we are done
        if self._size is not None:
            self._read_message_size_task.shutdown()
        # try to get something off the queue
        data: Optional[bytes] = self._db.get(block=False)
        if data is None:
            return
        # compute message size then shutdown
        self._size = len(data)
        self._read_message_size_task.shutdown()
