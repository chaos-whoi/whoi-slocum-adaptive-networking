from abc import abstractmethod, ABC

from ..types.pipes import IPipe


class ISink(IPipe):

    def __init__(self, name: str, size: int, *_, **__):
        super(ISink, self).__init__(name=name, size=size)

    @abstractmethod
    def recv(self, data: bytes):
        pass
