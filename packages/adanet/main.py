from adanet.networking.manager import NetworkManager
from adanet.types import NetworkRole

nm = NetworkManager(NetworkRole.SERVER)
nm.start()

nm.join()

