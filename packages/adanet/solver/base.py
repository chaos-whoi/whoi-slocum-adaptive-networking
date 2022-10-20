import os
from abc import abstractmethod, ABC
from typing import List

from adanet.types import Shuttable
from adanet.types.problem import Problem
from adanet.types.solution import Solution
from adanet.utils import find_shortest_whole_repetitive_pattern


class AbsSolver(ABC, Shuttable):

    def __init__(self):
        super(AbsSolver, self).__init__()

    @abstractmethod
    def solve(self, problem: Problem) -> Solution:
        raise NotImplementedError("Subclasses of AbsSolver need to implement their own 'solve()'")

    @staticmethod
    def _compact_sequence(sequence: List[str]) -> List[str]:
        if os.environ.get("COMPACT_SOLUTION", "1") == "1":
            return find_shortest_whole_repetitive_pattern(sequence)
        else:
            return sequence
