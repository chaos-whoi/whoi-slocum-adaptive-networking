import json
import socket
from ipaddress import IPv4Network, IPv4Address
from typing import Optional

import yaml
from zeroconf import ServiceInfo

from ..constants import ZEROCONF_PREFIX
from ..types.agent import AgentRole
from ..utils import utf8


class NetworkPeerService(ServiceInfo):

    def __init__(self, role: AgentRole, key: str, iface: str, address: IPv4Address,
                 network: IPv4Network, port: int, payload: Optional[dict] = None):
        properties = {"payload": payload or {}}
        properties.update(
            key=key,
            role=role.value,
            network=str(network),
            interface=iface,
        )
        super(NetworkPeerService, self).__init__(
            ZEROCONF_PREFIX,
            f"_{iface}._{role.name.lower()}._networkpeerservice.{ZEROCONF_PREFIX}",
            addresses=[socket.inet_aton(str(address))] if address else None,
            port=port,
            server=str(address),
            properties=properties,
        )

    @staticmethod
    def to_str(srv: ServiceInfo) -> str:
        data = {
            "addresses": [f"{addr}:{srv.port}" for addr in srv.parsed_scoped_addresses()],
            "name": srv.name,
            "weight": srv.weight,
            "priority": srv.priority,
            "server": srv.server,
            "properties": {utf8(k): utf8(v) for k, v in srv.properties.items()},
        }
        return yaml.safe_dump(data, indent=4, sort_keys=True)

    def __str__(self) -> str:
        return NetworkPeerService.to_str(self)
