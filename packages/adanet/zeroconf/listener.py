from collections import defaultdict
from typing import Dict, Optional

from zeroconf import ServiceStateChange, ServiceBrowser, ServiceInfo, Zeroconf

from . import zc
from .services import NetworkPeerService
from ..constants import ZEROCONF_PREFIX, PROCESS_KEY, ZMQ_SERVER_PORT
from ..networking import Adapter
from ..types import Shuttable
from ..types.agent import AgentRole
from ..utils import indent_block, utf8


class ZeroconfListener(Shuttable):

    def __init__(self, role: AgentRole):
        super(ZeroconfListener, self).__init__()
        self._role: AgentRole = role
        self._services: Dict[str, Dict[str, ServiceInfo]] = defaultdict(dict)
        self._browser: Optional[ServiceBrowser] = None

    def start(self):
        # instantiate a service browser
        services = [ZEROCONF_PREFIX]
        handlers = [self._on_service_state_change]
        self._browser = ServiceBrowser(zc, services, handlers=handlers)
        # register shutdown callback
        self.register_shutdown_callback(self.stop)

    def stop(self):
        self._browser.cancel()

    @staticmethod
    def advertise(service: NetworkPeerService):
        # DEBUG:
        # print(f"ZC: Advertising service:\n\n{indent_block(str(service))}\n")
        # DEBUG:
        zc.register_service(service)

    def on_new_network_interface(self, adapter: Adapter):
        # TODO: this is not needed, the adapter class is taking care of this
        pass
        # self.advertise(NetworkPeerService(
        #     role=self._role,
        #     key=PROCESS_KEY,
        #     iface=adapter.name,
        #     address=adapter.ip_address or None,
        #     network=adapter.ip_network or None,
        #     port=ZMQ_SERVER_PORT,
        #     payload={}
        # ))

    def _on_service_state_change(self, zeroconf: Zeroconf, service_type: str, name: str,
                                 state_change: ServiceStateChange):
        # get service information
        service = ServiceInfo(service_type, name)
        # TODO: use a constant for the timeout here
        service.request(zeroconf, timeout=3000)
        # only react to changes for services that do not belong to the same process (loop events)
        if utf8(service.properties.get(b"key", b"")) == PROCESS_KEY:
            return
        # we only care about service coming from the other side
        if utf8(service.properties.get(b"role", b"")) == self._role.name:
            return
        # sanitize server field, zeroconf appends a '.' at the end
        service.server = service.server.strip(".")
        # ---

        # TODO: this should notify the switchboard of the ip address of the peer.
        #       using the IP network, services received via mDNS are mapped to local
        #       adapters, which are then instructed on where to find the server to connect to

        # DEBUG:
        print(f"Service {name} of type {service_type} changed:\n\n"
              f"    state change: {state_change}\n\n"
              f"{indent_block(NetworkPeerService.to_str(service))}\n")
        # DEBUG:
