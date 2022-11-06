from .base import ISource


class DiskSource(ISource):

    def __init__(self, size: int, channel: str, *_, **__):
        super(DiskSource, self).__init__(size=size)
        self._topic: str = channel
        # TODO: create a queue here
