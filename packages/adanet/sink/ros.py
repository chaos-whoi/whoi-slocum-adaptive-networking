from .base import ISink


class ROSSink(ISink):

    def __init__(self, size: int, channel: str, *_, **__):
        super(ROSSink, self).__init__(size=size)
        self._topic: str = channel

    def recv(self, data: bytes):
        # TODO: publish to ROS topic here
        pass
