from adanet.asyncio import EventLoop
from adanet.pipes.base import AbsDataSource, AbsDataSink


class ROSDataSource(AbsDataSource):

    def __init__(self, size: int, channel: str, *_, **__):
        super(ROSDataSource, self).__init__(size=size)
        self._topic: str = channel
        # TODO: subscribe to ROS topic here


class ROSDataSink(AbsDataSink):

    def __init__(self, size: int, channel: str, *_, **__):
        super(ROSDataSink, self).__init__(size=size)
        self._topic: str = channel
        # TODO: publish to ROS topic here
