import time
from threading import Thread
from typing import Type, Optional

from adanet.constants import FORMULATE_PROBLEM_EVERY_SEC
from adanet.solver.base import AbsSolver
from adanet.switchboard import Switchboard
from adanet.time import Clock
from adanet.types import Shuttable
from adanet.types.agent import AgentRole
from adanet.types.problem import Problem
from adanet.types.solution import Solution


class Engine(Shuttable, Thread):

    def __init__(self, role: AgentRole, solver: Type[AbsSolver], problem: Problem):
        Shuttable.__init__(self)
        Thread.__init__(self, daemon=True)
        self._solver: AbsSolver = solver()
        self._problem: Problem = problem
        self._switchboard: Switchboard = Switchboard(role=role)

    def _formulate_new_problem(self) -> Problem:
        # TODO: for now returns same problem again and again
        return self._problem

    def _solve_problem(self) -> Solution:
        stime = time.time()
        solution = self._solver.solve(self._problem)
        ftime = time.time()
        print(f" solved in {ftime - stime:.2f} secs")
        return solution

    def run(self):
        stime: float = time.time()
        solution: Optional[Solution] = None
        # ---
        while not self.is_shutdown:
            # is it time for a new problem?
            if time.time() - stime >= FORMULATE_PROBLEM_EVERY_SEC:
                print("Formulating new problem...")
                solution = None
                stime = time.time()
            # solve problem (if needed)
            if solution is None:
                self._problem = self._formulate_new_problem()
                print(f"Problem definition:\n{self._problem.as_yaml()}")
                print("Solving new problem...", end='')
                solution = self._solve_problem()
                print(f"Solution found:\n{solution.as_yaml()}")
                # inform the switchboard of a new solution
                self._switchboard.update_solution(solution)
            # let the switchbox do its job
            time.sleep(Clock.period(0.1))
