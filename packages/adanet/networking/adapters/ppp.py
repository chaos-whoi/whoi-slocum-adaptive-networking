from ipaddress import IPv4Network
from typing import Optional

import netifaces

from .. import Adapter


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
