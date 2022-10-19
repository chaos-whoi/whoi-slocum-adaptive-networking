from adanet.asyncio import EventLoop
from adanet.pipes.base import AbsDataSource, AbsDataSink


class SimulatedDataSource(AbsDataSource):

    def __init__(self, frequency: float, size: int):
        super(SimulatedDataSource, self).__init__(size=size)
        self._frequency: float = frequency
        self._buffer = b"x" * size
        # simulate a publisher at the given frequency
        EventLoop.create_task(self._on_data, 1.0 / frequency, self._buffer)


class SimulatedDataSink(AbsDataSink):

    def __init__(self, frequency: float, size: int):
        super(SimulatedDataSink, self).__init__(size=size)
        self._frequency: float = frequency
