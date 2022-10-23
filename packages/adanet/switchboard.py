from functools import partial
from threading import Semaphore
from typing import Set, Optional, Dict

from adanet.networking.manager import NetworkManager
from adanet.pipes.base import AbsDataSource
from adanet.types import Shuttable
from adanet.types.agent import AgentRole
from adanet.types.problem import Problem
from adanet.types.solution import Solution, SolvedChannel


class Switchboard(Shuttable):

    def __init__(self, role: AgentRole, problem: Problem, simulation: bool = False):
        super(Switchboard, self).__init__()
        self._problem: Problem = problem
        self._sources: Set[AbsDataSource] = set()
        self._network_manager: NetworkManager = NetworkManager(role)
        self._solution: Optional[Solution] = None
        self._channels: Dict[str, SolvedChannel] = {}
        self._lock: Semaphore = Semaphore()
        # start network manager
        self._network_manager.start()
        # choose between simulated and real data sources
        if simulation:
            from adanet.pipes.simulated import SimulatedDataSource as DataSource
        else:
            from adanet.pipes.ros import ROSDataSource as DataSource
        # instantiate data sources
        for channel in problem.channels:
            source: AbsDataSource = DataSource(channel.size,
                                               channel=channel.name, frequency=channel.frequency)
            source.register_callback(partial(self._on_recv, channel.name))
            self._sources.add(source)

    def update_solution(self, solution: Solution):
        with self._lock:
            self._solution = solution
            self._channels = {
                c.name: c for c in solution.assignments
            }

    def _on_recv(self, channel: str, data: bytes):
        with self._lock:
            # make sure we have a solution for this channel
            if channel not in self._channels:
                return
            # get channel solution
            solved_channel: SolvedChannel = self._channels[channel]
        # find next interface for this channel according to the current solution
        interface: Optional[str] = solved_channel.next()
        if interface is None:
            return
        # send data through interface
        self._network_manager.send(interface, channel, data)
