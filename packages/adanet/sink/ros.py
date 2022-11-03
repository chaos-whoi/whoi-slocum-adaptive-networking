from adanet.source.base import ISink


class ROSSink(ISink):

    def __init__(self, size: int, channel: str, *_, **__):
        super(ROSSink, self).__init__(size=size)
        self._topic: str = channel
        # TODO: publish to ROS topic here
