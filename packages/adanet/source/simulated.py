from typing import Optional

from adanet.asyncio import loop, Task
from adanet.source.base import ISource
from adanet.time import Clock


class SimulatedSource(ISource):

    def __init__(self, size: int, frequency: float, *_, **__):
        super(SimulatedSource, self).__init__(size=size)
        self._frequency: float = frequency
        self._buffer = b"x" * size
        # simulate a publisher at the given frequency
        period: float = Clock.period(1.0 / frequency)
        # DEBUG:
        # print(f"FREQUENCY[real]: {frequency}, FREQUENCY[sim]: {1.0 / period}, "
        #       f"PERIOD[real]: {1.0 / frequency}, PERIOD[sim]: {period}")
        # self._stime = Clock.time()
        # DEBUG:
        self._task: Task = Task(period, self._on_data)
        loop.add_task(self._task, self._buffer)

    def update(self, frequency: Optional[float] = None, **kwargs):
        if frequency is not None and frequency > 0:
            self._task.period = Clock.period(1.0 / frequency)

    def _on_data(self, data: bytes):
        # DEBUG:
        # print(f"PUBLISH AT {1.0 / Clock.real_period(Clock.time() - self._stime)}")
        # self._stime = Clock.time()
        # DEBUG:
        super(SimulatedSource, self)._on_data(data)
