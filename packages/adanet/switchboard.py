from functools import partial
from threading import Semaphore
from typing import Optional, Dict

from adanet.asyncio import loop, Task
from adanet.networking.manager import NetworkManager
from adanet.pipes.base import AbsDataSource
from adanet.time import Clock
from adanet.types import Shuttable
from adanet.types.agent import AgentRole
from adanet.types.problem import Problem
from adanet.types.report import Report
from adanet.types.solution import Solution, SolvedChannel


class NetworkMonitorTask(Task):

    def step(self, nm: NetworkManager):
        for interface, stats in nm.link_statistics.items():
            Report.log({
                f"link/{interface}": stats
            })
        for channel, stats in nm.channel_statistics.items():
            Report.log({
                f"channel/{channel.strip('/')}": stats
            })


class Switchboard(Shuttable):

    def __init__(self, role: AgentRole, problem: Problem, simulation: bool = False):
        super(Switchboard, self).__init__()
        self._problem: Problem = problem
        self._simulation: bool = simulation
        self._network_manager: NetworkManager = NetworkManager(role)
        self._solution: Optional[Solution] = None
        self._channels: Dict[str, SolvedChannel] = {}
        self._sources: Dict[str, AbsDataSource] = {}
        self._lock: Semaphore = Semaphore()
        # start network manager
        self._network_manager.start()
        # choose between simulated and real data sources
        if self._simulation:
            from adanet.pipes.simulated import SimulatedDataSource as DataSource
        else:
            from adanet.pipes.ros import ROSDataSource as DataSource
        # instantiate data sources
        for channel in problem.channels:
            source: AbsDataSource = DataSource(channel.size,
                                               channel=channel.name, frequency=channel.frequency)
            source.register_callback(partial(self._on_recv, channel.name))
            self._sources[channel.name] = source
        # activate network monitor
        task: Task = NetworkMonitorTask(period=Clock.period(2.0))
        loop.add_task(task, self._network_manager)

    def update_solution(self, solution: Solution):
        with self._lock:
            self._solution = solution
            self._channels = {
                c.name: c for c in solution.assignments
            }
            # if we are simulating the problem, update the sources' frequency
            if self._simulation:
                # TODO: the idea here is that simulated sources can be throttled to the actual
                #       solution frequency given that the data is fake. Also, this would reduce
                #       the pressure on asyncio eventloop sleep
                # for c in solution.assignments:
                #     self._sources[c.name].update(frequency=c.frequency)
                # TODO:
                pass

    def _on_recv(self, channel: str, data: bytes):
        with self._lock:
            # get channel solution
            solved_channel: Optional[SolvedChannel] = self._channels.get(channel, None)
            # make sure we have a solution for this channel
            if solved_channel is None:
                return
        # find next interface for this channel according to the current solution
        interface: Optional[str] = solved_channel.next()
        if interface is None:
            return
        # send data through interface
        self._network_manager.send(interface, channel, data)
