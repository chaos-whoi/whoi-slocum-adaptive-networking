from adanet.types import Shuttable
from adanet.types.problem import Problem
from adanet.types.solution import Solution


class AbsSolver(Shuttable):

    def __init__(self):
        super(AbsSolver, self).__init__()

    def solve(self, problem: Problem) -> Solution:
        raise NotImplementedError("Subclasses of AbsSolver need to implement their own 'solve()'")
