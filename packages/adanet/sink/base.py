from ..types.pipes import IPipe


class ISink(IPipe):

    # TODO: not sure we need this
    def send(self, data: bytes):
        self._on_data(data)
