from adanet.source.base import ISink


class SimulatedSink(ISink):

    def __init__(self, frequency: float, size: int):
        super(SimulatedSink, self).__init__(size=size)
        self._frequency: float = frequency
