from time import sleep
from threading import Thread
from typing import Type, Optional

from adanet.constants import FORMULATE_PROBLEM_EVERY_SEC
from adanet.simulation import Simulator
from adanet.solver.base import AbsSolver
from adanet.switchboard import Switchboard
from adanet.time import Clock
from adanet.types import Shuttable
from adanet.types.agent import AgentRole
from adanet.types.problem import Problem
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
        if role is AgentRole.ROBOT:
            # make sure a solver is given when running in ROBOT mode
            if solver is None:
                raise ValueError("A 'solver' is required when 'role=ROBOT'")
            # instantiate solver
            self._solver: AbsSolver = solver()
        # ---
        self._problem: Problem = problem
        self._simulator: Optional[Simulator] = simulator
        self._switchboard: Switchboard = Switchboard(role=role, problem=problem,
                                                     simulation=simulator is not None)
        self._zeroconf: ZeroconfListener = ZeroconfListener(role)
        # tell the network manager to notify zeroconf of any new network interface
        self._switchboard.network_manager.on_new_interface(self._zeroconf.on_new_network_interface)

    def start(self):
        # reset clock
        Clock.reset()
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
            return self._simulator.step()
        else:
            # TODO: use the statistics collector to formulate a new problem
            pass
        # TODO: for now returns same problem again and again
        return self._problem

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
            if self._role is AgentRole.ROBOT:
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
