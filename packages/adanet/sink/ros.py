from .base import ISink


class ROSSink(ISink):

    def __init__(self, name: str, size: int, *_, **__):
        super(ROSSink, self).__init__(name=name, size=size)

    @property
    def topic(self) -> str:
        return self.name

    def recv(self, data: bytes):
        # TODO: publish to ROS topic here
        print(f"RECEIVED DATA: {len(data)} bytes")
        pass
