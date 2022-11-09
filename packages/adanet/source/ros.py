from .base import ISource


class ROSSource(ISource):

    def __init__(self, name: str, size: int, *args, **kwargs):
        super(ROSSource, self).__init__(name=name, size=size, *args, **kwargs)
        # TODO: subscribe to ROS topic here
        # TODO: we should monitor the frequency here and update self._frequency
        #       use a flowwatch object here to estimate the frequency

    @property
    def topic(self) -> str:
        return self.name
