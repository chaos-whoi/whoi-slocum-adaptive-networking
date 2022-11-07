from .base import ISink


class DiskSink(ISink):

    def __init__(self, size: int, channel: str, *_, **__):
        super(DiskSink, self).__init__(size=size)
        self._channel: str = channel

    def recv(self, data: bytes):
        # TODO: put data in a disk queue
        print("INCOMING DATA:", str(data))
        pass
