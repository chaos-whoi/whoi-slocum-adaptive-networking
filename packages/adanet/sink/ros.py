from .base import ISink
import time

class ROSSink(ISink):

    def __init__(self, name: str, size: int, *_, **__):
        super(ROSSink, self).__init__(name=name, size=size)

    @property
    def topic(self) -> str:
        return self.name

    def recv(self, data: bytes):
        # TODO: publish to ROS topic here
        print(f"[{time.time()}] RECEIVED DATA: {len(data)} bytes")
        pass
