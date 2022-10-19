import socket
from ipaddress import IPv4Network, IPv4Address
from typing import Optional

from zeroconf import ServiceInfo

from ..constants import ZEROCONF_PREFIX
from ..types.agent import AgentRole


class NetworkPeerService(ServiceInfo):

    def __init__(self, role: AgentRole, key: str, iface: str, address: IPv4Address,
                 network: IPv4Network, port: int, payload: Optional[dict] = None):
        properties = {"payload": payload or {}}
        properties.update(
            key=key,
            role=role.value,
            network=str(network),
        )
        super(NetworkPeerService, self).__init__(
            ZEROCONF_PREFIX,
            f"_{iface}._{role.name.lower()}._networkpeerservice.{ZEROCONF_PREFIX}",
            addresses=[socket.inet_aton(str(address))] if address else None,
            port=port,
            properties=properties,
        )
