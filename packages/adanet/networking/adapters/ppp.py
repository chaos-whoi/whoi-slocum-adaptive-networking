from ipaddress import IPv4Network
from typing import Optional

import netifaces

from .. import Adapter
from ...types.network import NetworkDevice


class PPPAdapter(Adapter):

    @property
    def ip_network(self) -> Optional[IPv4Network]:
        """
        The IP network of the interface.

        :return: the IP network of the interface
        """
        addresses = netifaces.ifaddresses(self.name).get(netifaces.AF_INET, {})
        if addresses:
            address = addresses[0]
            ip = address.get("addr", None)
            if ip is None:
                return None
            # we have a valid IP, `ppp` links have only two IPs, so we use a mask of 31 bits
            netmask = 31
            return IPv4Network(f"{ip}/{netmask}", strict=False)
        return None

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
