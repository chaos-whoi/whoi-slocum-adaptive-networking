import time
from threading import Thread, Semaphore
from typing import Set, Dict, Type

import nmcli

from . import Adapter
from .adapters.ethernet import EthernetAdapter
from .adapters.ppp import PPPAdapter
from .adapters.wifi import WifiAdapter
from ..constants import ALLOW_DEVICE_TYPES
from ..types import Shuttable
from ..types.network import NetworkDevice
from ..types.agent import AgentRole


class NetworkManager(Shuttable, Thread):

    _adapter_classes = {
        "wifi": WifiAdapter,
        "ethernet": EthernetAdapter,
        "ppp": PPPAdapter,
    }

    def __init__(self, role: AgentRole):
        Thread.__init__(self, daemon=True)
        Shuttable.__init__(self)
        self._role: AgentRole = role
        self._lock: Semaphore = Semaphore()
        self._adapters: Dict[str, Adapter] = {}

    def _setup_new_adapter(self, device: NetworkDevice):
        cls: Type[Adapter] = self._adapter_classes[device.type.value]
        return cls(self._role, device)

    def run(self):
        ignored: Set[str] = set()
        while not self.is_shutdown:
            new_adapters: Set[Adapter] = set()
            for dev_nmcli in nmcli.device.status():
                dev, devt = dev_nmcli.device, dev_nmcli.device_type
                # filter devices based on their type
                if devt not in self._adapter_classes:
                    if dev not in ignored:
                        print(f"Ignoring device '{dev}' of (unsupported) type '{devt}'")
                        ignored.add(dev)
                    continue
                # filter devices based on user preferences
                if "all" not in ALLOW_DEVICE_TYPES and devt not in ALLOW_DEVICE_TYPES:
                    if dev not in ignored:
                        print(f"Ignoring device '{dev}' of (excluded) type '{devt}'")
                        ignored.add(dev)
                    continue
                # ---
                with self._lock:
                    if dev not in self._adapters:
                        print(f"Attaching to device '{dev}' of type '{devt}'")
                        device = NetworkDevice.from_nmcli_output(dev_nmcli)
                        adapter = self._setup_new_adapter(device)
                        self._adapters[dev] = adapter
                        new_adapters.add(adapter)
                    else:
                        self._adapters[dev].update(device)
            # activate new adapters
            for adapter in new_adapters:
                adapter.start()
            time.sleep(4)
