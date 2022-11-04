from .base import ISource


class ROSSource(ISource):

    def __init__(self, size: int, channel: str, *_, **__):
        super(ROSSource, self).__init__(size=size)
        self._topic: str = channel
        # TODO: subscribe to ROS topic here
