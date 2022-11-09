from threading import Thread
from time import sleep
from typing import Type, Optional, List

from adanet.constants import FORMULATE_PROBLEM_EVERY_SEC
from adanet.networking import Adapter
from adanet.networking.manager import NetworkManager
from adanet.simulation import Simulator
from adanet.solver.base import AbsSolver
from adanet.source.base import ISource
from adanet.switchboard import Switchboard
from adanet.time import Clock
from adanet.types import Shuttable
from adanet.types.agent import AgentRole
from adanet.types.problem import Problem, Link, Channel
from adanet.types.report import Report
from adanet.types.solution import Solution
from adanet.utils import indent_block
from adanet.zeroconf.listener import ZeroconfListener


class Engine(Shuttable, Thread):

    def __init__(self, role: AgentRole, problem: Problem,
                 solver: Optional[Type[AbsSolver]] = None,
                 simulator: Optional[Simulator] = None):
        Shuttable.__init__(self)
        Thread.__init__(self, daemon=True)
        self._role: AgentRole = role
        self._solver: Optional[AbsSolver] = None
        # - ROBOT mode
        if role is AgentRole.SOURCE:
            # make sure a solver is given when running in ROBOT mode
            if solver is None:
                raise ValueError("A 'solver' is required when 'role=ROBOT'")
            # instantiate solver
            self._solver: AbsSolver = solver()
        # ---
        simulation: bool = simulator is not None
        self._problem: Problem = problem
        self._simulator: Optional[Simulator] = simulator
        self._network_manager: NetworkManager = NetworkManager(role=role, problem=problem)
        self._switchboard: Switchboard = Switchboard(role=role, problem=problem,
                                                     simulation=simulation)
        self._zeroconf: ZeroconfListener = ZeroconfListener(role)
        # link network manager and switchboard
        self._network_manager.switchboard = self._switchboard
        self._switchboard.network_manager = self._network_manager
        # tell the network manager to notify zeroconf of any new network interface
        self._network_manager.on_new_interface(self._zeroconf.on_new_network_interface)

    def start(self):
        # reset clock
        Clock.reset()
        # start network manager
        self._network_manager.start()
        # start switchboard
        self._switchboard.start()
        # start simulator
        if self._simulator:
            self._simulator.start()
        # start zeroconf listener
        self._zeroconf.start()
        # start engine
        super(Engine, self).start()

    def _formulate_new_problem(self) -> Problem:
        if self._simulator:
            # simulated problem
            problem = self._simulator.step()
        else:
            # start from an empty problem
            links: List[Link] = []
            channels: List[Channel] = []
            # add channels to the problem
            for channel in self._problem.channels:
                new_channel: Channel = channel.copy(deep=True)
                # update frequency based on the source's readings
                source: ISource = self._switchboard.source(channel.name)
                new_channel.frequency = source.frequency
            # add links to the problem
            for adapter in self._network_manager.adapters:
                # use the statistics collector to formulate a new problem
                links.append(Link(
                    interface=adapter.device.interface,
                    # TODO: perhaps we should use a combination of IN and OUT bandwidth
                    bandwidth=adapter.bandwidth_out,
                    latency=adapter.latency,
                    # TODO: this is not used
                    reliability=1.0,
                ))
            # compile the problem
            problem: Problem = Problem(links=links, channels=channels)
        # remove adapters that have no signal
        for link in list(problem.links):
            adapter: Optional[Adapter] = self._network_manager.adapter(link.interface)
            if adapter is None or not adapter.is_connected:
                problem.links.remove(link)
        # ---
        return problem

    def _solve_problem(self) -> Solution:
        stime = Clock.true_time()
        solution = self._solver.solve(self._problem)
        ftime = Clock.true_time()
        print(f" solved in {ftime - stime:.2f} secs")
        return solution

    def run(self):
        stime: float = Clock.time()
        solution: Optional[Solution] = None
        # ---
        while not self.is_shutdown:
            # - ROBOT mode
            if self._role is AgentRole.SOURCE:
                # is it time for a new problem?
                if Clock.time() - stime >= FORMULATE_PROBLEM_EVERY_SEC:
                    print("Formulating new problem...")
                    solution = None
                    stime = Clock.time()
                # solve problem (if needed)
                if solution is None:
                    self._problem = self._formulate_new_problem()
                    print(f"Problem definition:\n{indent_block(self._problem.as_yaml())}\n")
                    # log new problem
                    Report.log(self._problem)
                    print("Solving new problem...", end='')
                    solution = self._solve_problem()
                    print(f"Solution found:\n{indent_block(solution.as_yaml())}\n")
                    # log new solution
                    Report.log(solution)
                    # inform the switchboard of a new solution
                    self._switchboard.update_solution(solution)
            # let the switchbox do its job
            sleep(Clock.period(0.1))
        # stop simulator (if any)
        if self._simulator:
            self._simulator.shutdown()
