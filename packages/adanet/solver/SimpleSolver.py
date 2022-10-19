from collections import defaultdict
from typing import List, Tuple, Dict

from adanet.constants import FORMULATE_PROBLEM_EVERY_SEC
from adanet.solver.base import AbsSolver
from adanet.types.problem import Problem, Channel, Link
from adanet.types.solution import Solution, SolvedChannel

Priority = int
Latency = int
Interface = str
BandwidthRemaining = float


class SimpleSolver(AbsSolver):

    def solve(self, problem: Problem) -> Solution:
        solution: Solution = Solution(problem=problem)
        # return an empty solution if we don't have information about the links
        if problem.links is None:
            return solution
        # - group channels by priority
        groups: Dict[Priority, List[Channel]] = defaultdict(list)
        for c in problem.channels:
            groups[c.priority].append(c)
        # - sort channels according to priority
        channel_groups: List[List[Channel]] = [
            groups[p] for p in sorted(groups.keys(), reverse=True)
        ]
        # - sort links by latency
        links: List[Link] = []
        for link in problem.links:
            links.append(link.copy(deep=True))
            # - convert bandwidth into capacity
            link.capacity = link.bandwidth * FORMULATE_PROBLEM_EVERY_SEC
        links.sort(key=lambda l: l.latency)
        # - allocate bandwidth to channels according to priority and bandwidth left
        for channels in channel_groups:
            for channel in channels:
                solved_channel: SolvedChannel = SolvedChannel(
                    name=channel.name,
                    # this is updated below
                    frequency=0,
                    # NOTE: we are populating this list without taking into account the bandwidth
                    #       just the capacity, this is not correct, we should compute the link
                    #       usage over time and avoid spikes in the usage that overshoot the
                    #       bandwidth
                    interfaces=[],
                    problem=channel,
                )
                num_packets: int = int(channel.qos.frequency * FORMULATE_PROBLEM_EVERY_SEC)
                sent_packet: int = 0
                for _ in range(num_packets):
                    for link in links:
                        compatible: bool = channel.qos is None or channel.qos.latency is None or \
                                           channel.qos.latency <= link.latency
                        if not compatible:
                            continue
                        enough_bw: bool = link.capacity >= channel.size
                        if enough_bw:
                            # update link's capacity
                            link.capacity -= channel.size
                            # assign 1 packet from `channel` to `link`
                            solved_channel.interfaces.append(link.interface)
                            sent_packet += 1
                # update channel effective frequency
                solved_channel.frequency = sent_packet / FORMULATE_PROBLEM_EVERY_SEC
                # add solved channel to the solution
                solution.assignments.append(solved_channel)
        # ---
        return solution

