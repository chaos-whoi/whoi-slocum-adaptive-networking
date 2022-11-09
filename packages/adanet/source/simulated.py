from .base import ISource
from ..asyncio import loop, Task
from ..time import Clock


class SimulatedSource(ISource):

    def __init__(self, name: str, size: int, frequency: float, *args, **kwargs):
        super(SimulatedSource, self).__init__(name=name, size=size, frequency=frequency,
                                              *args, **kwargs)
        self._buffer = b"x" * size
        # simulate a publisher at the given frequency
        period: float = Clock.period(1.0 / self.frequency)
        # DEBUG:
        # print(f"FREQUENCY[real]: {frequency}, FREQUENCY[sim]: {1.0 / period}, "
        #       f"PERIOD[real]: {1.0 / frequency}, PERIOD[sim]: {period}")
        # self._stime = Clock.time()
        # DEBUG:
        self._task: Task = Task(period, self._generate_data)
        loop.add_task(self._task)

    # TODO: not used
    # def update(self, frequency: Optional[float] = None, **kwargs):
    #     if frequency is not None and frequency > 0:
    #         self._task.period = Clock.period(1.0 / frequency)

    def _generate_data(self):
        # DEBUG:
        # print(f"PUBLISH AT {1.0 / Clock.real_period(Clock.time() - self._stime)}")
        # self._stime = Clock.time()
        # DEBUG:
        self._produce(self._buffer)
