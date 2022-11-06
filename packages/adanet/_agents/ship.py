from adanet.networking.manager import NetworkManager
from adanet.types.agent import AgentRole


nm = NetworkManager(AgentRole.SINK)
nm.start()

nm.join()

