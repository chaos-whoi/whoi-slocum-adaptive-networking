from collections import defaultdict
from typing import Dict, Optional

from zeroconf import ServiceStateChange, ServiceBrowser, IPVersion, ServiceInfo, Zeroconf

from .services import NetworkPeerService
from ..constants import ZEROCONF_PREFIX, SERVER_PORT, PROCESS_KEY
from ..networking import Adapter
from ..types import Shuttable
from ..types.agent import AgentRole
from ..utils import indent_block, utf8


class ZeroconfListener(Shuttable):

    def __init__(self, role: AgentRole):
        super(ZeroconfListener, self).__init__()
        self._role: AgentRole = role
        self._services: Dict[str, Dict[str, ServiceInfo]] = defaultdict(dict)
        self._zc: Zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self._browser: Optional[ServiceBrowser] = None

    def start(self):
        # instantiate a service browser
        services = [ZEROCONF_PREFIX]
        handlers = [self._on_service_state_change]
        self._browser = ServiceBrowser(self._zc, services, handlers=handlers)
        # register shutdown callback
        self.register_shutdown_callback(self.stop)

    def stop(self):
        self._browser.cancel()

    def advertise(self, service: NetworkPeerService):
        # DEBUG:
        # print(f"ZC: Advertising service:\n\n{indent_block(str(service))}\n")
        # DEBUG:
        self._zc.register_service(service)

    def on_new_network_interface(self, adapter: Adapter):
        self.advertise(NetworkPeerService(
            role=self._role,
            key=PROCESS_KEY,
            iface=adapter.name,
            address=adapter.ip_address or None,
            network=adapter.ip_network or None,
            port=SERVER_PORT,
            payload={}
        ))

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
        # DEBUG:
        print(f"Service {name} of type {service_type} changed:\n\n"
              f"    state change: {state_change}\n\n"
              f"{indent_block(NetworkPeerService.to_str(service))}\n")
        # DEBUG:
