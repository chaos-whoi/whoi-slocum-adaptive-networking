from typing import List

import nmcli


class Machine:

    @staticmethod
    def network_interfaces() -> List[str]:
        nmcli.device.status()
