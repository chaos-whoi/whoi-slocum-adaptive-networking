from abc import abstractmethod, ABC

from ..types.pipes import IPipe


class ISink(IPipe):

    @abstractmethod
    def recv(self, data: bytes):
        pass
