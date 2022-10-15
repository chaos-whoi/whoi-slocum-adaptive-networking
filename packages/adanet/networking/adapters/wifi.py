from .. import Adapter
from ...types import NetworkDevice


class WifiAdapter(Adapter):

    def _is_active(self) -> bool:
        # TODO: fix this
        return True

    def _has_link(self) -> bool:
        # TODO: fix this
        return True

    def _is_connected(self) -> bool:
        # TODO: fix this
        return True

    def _update(self, device: NetworkDevice) -> None:
        pass

    def _setup(self) -> None:
        pass
