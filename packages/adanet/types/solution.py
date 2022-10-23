from collections import defaultdict
from typing import List, Any, Dict, Optional, Iterator

from ..types.misc import Reminder, GenericModel
from ..types.problem import Problem, Channel


class SolvedChannel(GenericModel):
    name: str
    frequency: float
    interfaces: List[str]
    problem: Channel

    # internal use only
    _iterator: Iterator[str]
    _reminder: Reminder

    class Config:
        underscore_attrs_are_private = True

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._reminder: Optional[Reminder] = None
        self._iterator = self._iface_iterator()
        if self.frequency > 0:
            self._reminder = Reminder(frequency=self.frequency)

    def _iface_iterator(self) -> Iterator[str]:
        cursor: int = 0
        if len(self.interfaces) > 0:
            while True:
                if cursor >= len(self.interfaces):
                    cursor = 0
                if not self._is_time():
                    yield None
                    continue
                yield self.interfaces[cursor]
                cursor += 1

    def _is_time(self):
        return self._reminder is not None and self._reminder.is_time()

    def next(self):
        try:
            return next(self._iterator)
        except StopIteration:
            return None

    def dict(self, *_, **__) -> Dict:
        d = super(SolvedChannel, self).dict(*_, **__)
        del d["problem"]
        return d

    def report(self) -> dict:
        histogram: Dict[str, int] = defaultdict(lambda: 0)
        for iface in self.interfaces:
            histogram[iface] += 1
        usage = {k: v / len(self.interfaces) for k, v in histogram.items()}
        return {
            "frequency": self.frequency,
            "usage": usage
        }


class Solution(GenericModel):
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
        return self.json(sort_keys=True, indent=4, exclude={"problem"})

    def report(self) -> dict:
        return {
            ch.name.strip("/"): ch.report() for ch in self.assignments
        }
