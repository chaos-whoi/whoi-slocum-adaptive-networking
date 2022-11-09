from .base import ISink


class SimulatedSink(ISink):

    def __init__(self, name: str, size: int, *_, **__):
        super(SimulatedSink, self).__init__(name=name, size=size)

    def recv(self, _: bytes):
        # do nothing
        pass
