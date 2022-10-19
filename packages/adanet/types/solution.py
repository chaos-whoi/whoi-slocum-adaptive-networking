from typing import List, Any, Dict, Optional

from pydantic import BaseModel

from ..types.misc import Reminder
from ..types.problem import Problem, Channel


class SolvedChannel(BaseModel):
    name: str
    frequency: float
    interfaces: List[str]
    problem: Channel

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._reminder: Reminder = Reminder(frequency=self.frequency)

    def _iface_iterator(self) -> Optional[str]:
        cursor: int = 0
        while True:
            if cursor >= len(self.interfaces):
                cursor = 0
            if not self._is_time():
                yield None
            yield self.interfaces[cursor]

    def _is_time(self):
        return self._reminder.is_time()

    def next(self):
        return self._iface_iterator()


class Solution(BaseModel):
    problem: Problem
    assignments: List[SolvedChannel]

    @property
    def span_over_packets(self) -> float:
        """
        Returns the span of the solution over the problem as the number of packets sent.
        The returned value is between 0 and 1, where 0 means that the solution solves 0%
        of the problem and 1 means that the solution solves 100% of the problem.

        :return: the span over number of packets sent.
        """
        # TODO: test this
        total: int = 0
        sent: int = 0
        frequencies: Dict[str, float] = {}
        for c1 in self.problem.channels:
            if c1.frequency:
                frequencies[c1.name] = c1.frequency
        for c2 in self.assignments:
            if c2.name not in frequencies:
                print("WARNING: You are computing the span of a solution over a problem with "
                      f"the channel '{c2.name}' that have an unknown frequency. "
                      f"The result will be partial and ignore the contribution of this channel.")
                continue
            total += frequencies[c2.name]
            sent += c2.frequency
        # compute solution ratio
        return sent / total if total > 0 else 0

    @property
    def span_over_bytes(self) -> float:
        """
        Returns the span of the solution over the problem as the number of bytes sent.
        The returned value is between 0 and 1, where 0 means that the solution solves 0%
        of the problem and 1 means that the solution solves 100% of the problem.

        :return: the span over number of bytes sent.
        """
        # TODO: test this
        total: int = 0
        sent: int = 0
        frequencies: Dict[str, float] = {}
        for c1 in self.problem.channels:
            if c1.frequency:
                frequencies[c1.name] = c1.frequency
        for c2 in self.assignments:
            if c2.name not in frequencies:
                print("WARNING: You are computing the span of a solution over a problem with "
                      f"the channel '{c2.name}' that have an unknown frequency. "
                      f"The result will be partial and ignore the contribution of this channel.")
                continue
            total += frequencies[c2.name] * c2.problem.size
            sent += c2.frequency * c2.problem.size
        # compute solution ratio
        return sent / total if total > 0 else 0

    def as_json(self) -> str:
        return self.json(sort_keys=True, indent=4)
