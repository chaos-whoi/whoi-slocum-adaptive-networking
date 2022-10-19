from typing import Set, Optional, Dict

from adanet.networking.manager import NetworkManager
from adanet.pipes.base import AbsDataSource
from adanet.types import Shuttable
from adanet.types.agent import AgentRole
from adanet.types.solution import Solution, SolvedChannel


class Switchboard(Shuttable):

    def __init__(self, role: AgentRole):
        super(Switchboard, self).__init__()
        self._role: AgentRole = role
        self._sources: Set[AbsDataSource] = set()
        self._network_manager: NetworkManager = NetworkManager(role)
        self._solution: Optional[Solution] = None
        self._channels: Dict[str, SolvedChannel] = {}

    def update_solution(self, solution: Solution):
        # TODO: we need to lock here
        self._solution = solution
        self._channels = {
            c.name: c for c in solution.assignments
        }

    def on_recv(self, channel: str, data: bytes):
        # find next interface for this channel according to the current solution
        channel: SolvedChannel = self._channels[channel]
        iface: Optional[str] = channel.next()
        if iface is None:
            return

