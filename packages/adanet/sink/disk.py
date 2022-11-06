from .base import ISink


class DiskSink(ISink):

    def __init__(self, size: int, channel: str, *_, **__):
        super(DiskSink, self).__init__(size=size)
        self._topic: str = channel
        # TODO: listen from a queue here
