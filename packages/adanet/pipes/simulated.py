from adanet.asyncio import loop
from adanet.pipes.base import AbsDataSource, AbsDataSink


class SimulatedDataSource(AbsDataSource):

    def __init__(self, size: int, frequency: float, *_, **__):
        super(SimulatedDataSource, self).__init__(size=size)
        self._frequency: float = frequency
        self._buffer = b"x" * size
        # simulate a publisher at the given frequency
        loop.add_task(self._on_data, 1.0 / frequency, self._buffer)

    def _on_data(self, data: bytes):
        super(SimulatedDataSource, self)._on_data(data)


class SimulatedDataSink(AbsDataSink):

    def __init__(self, frequency: float, size: int):
        super(SimulatedDataSink, self).__init__(size=size)
        self._frequency: float = frequency
