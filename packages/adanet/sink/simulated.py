from .base import ISink


class SimulatedSink(ISink):

    def __init__(self, frequency: float, size: int, *_, **__):
        super(SimulatedSink, self).__init__(size=size)
        self._frequency: float = frequency

    def recv(self, _: bytes):
        # do nothing
        pass
