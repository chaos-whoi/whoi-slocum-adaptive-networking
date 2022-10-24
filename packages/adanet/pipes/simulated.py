from typing import Optional

from adanet.asyncio import loop, Task
from adanet.pipes.base import AbsDataSource, AbsDataSink
from adanet.time import Clock


class SimulatedDataSource(AbsDataSource):

    def __init__(self, size: int, frequency: float, *_, **__):
        super(SimulatedDataSource, self).__init__(size=size)
        self._frequency: float = frequency
        self._buffer = b"x" * size
        # simulate a publisher at the given frequency
        period: float = Clock.period(1.0 / frequency)
        self._task: Task = Task(period, self._on_data)
        loop.add_task(self._task, self._buffer)

    def update(self, frequency: Optional[float] = None, **kwargs):
        if frequency is not None and frequency > 0:
            self._task.period = Clock.period(1.0 / frequency)

    def _on_data(self, data: bytes):
        super(SimulatedDataSource, self)._on_data(data)


class SimulatedDataSink(AbsDataSink):

    def __init__(self, frequency: float, size: int):
        super(SimulatedDataSink, self).__init__(size=size)
        self._frequency: float = frequency
