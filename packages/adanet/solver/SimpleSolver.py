from collections import defaultdict
from math import ceil
from typing import List, Dict, Iterator

from adanet.constants import FORMULATE_PROBLEM_EVERY_SEC
from adanet.solver.base import AbsSolver
from adanet.types.problem import Problem, Channel, Link, LatencyPolicy
from adanet.types.solution import Solution, SolvedChannel
from adanet.utils import infinite_iterator

Priority = int
Latency = int
Interface = str
BandwidthRemaining = float


class SimpleSolver(AbsSolver):

    def solve(self, problem: Problem) -> Solution:
        solution: Solution = Solution(problem=problem, assignments=[])
        # return an empty solution if we don't have information about the links
        if problem.links is None:
            return solution
        # - group channels by priority
        groups: Dict[Priority, List[Channel]] = defaultdict(list)
        for c in problem.channels:
            groups[c.priority].append(c)
        # - sort channels by priority
        channel_groups: List[List[Channel]] = [
            groups[p] for p in sorted(groups.keys(), reverse=True)
        ]
        # - find biggest currently streaming channel
        biggest_packet_size: int = 0
        for c in problem.channels:
            if c.frequency and c.size:
                biggest_packet_size = max(biggest_packet_size, c.size)
        # - sort links by latency
        links: List[Link] = []
        for link1 in problem.links:
            link = link1.copy(deep=True)
            # to avoid getting stuck in a bandwidth=0 situation, assume bandwidth is always good
            # enough to transfer a single packet of the biggest channel in the current deltaT
            bandwidth: float = max(biggest_packet_size, link.bandwidth if link.bandwidth else 0)

            # TODO: test PR 2023
            bandwidth = max(2048.0, bandwidth)

            # - convert bandwidth into capacity
            # TODO: there is a bug here
            link.capacity = bandwidth * FORMULATE_PROBLEM_EVERY_SEC


            # print(link1.name, biggest_packet_size, bandwidth, FORMULATE_PROBLEM_EVERY_SEC, link.capacity)

            links.append(link)
        links.sort(key=lambda l: l.latency)
        # - allocate bandwidth to channels according to priority and bandwidth left
        for channels in channel_groups:
            for channel in channels:
                interfaces: List[str] = []
                # frequency is either the QoS frequency (if given) or the original frequency
                frequency: float = channel.qos.frequency \
                    if (channel.qos and channel.qos.frequency) else channel.frequency
                packets_total: int = channel.queue_length + \
                                     int(frequency * FORMULATE_PROBLEM_EVERY_SEC)
                packets_sent: int = 0
                # find good/slow links
                good_links: List[Link] = []
                slow_links: List[Link] = []
                num_links: int = len(links)
                for link in links:
                    compatible: bool = channel.qos is None or channel.qos.latency is None or \
                                       channel.qos.latency >= link.latency
                    if compatible:
                        good_links.append(link)
                    else:
                        slow_links.append(link)
                # open an iterator over the list of compatible links
                links_iter: Iterator[Link] = infinite_iterator(good_links)
                num_assignments: int = int(num_links * ceil(packets_total / (num_links or 1)))
                assert (num_links == 0) or (num_assignments >= packets_total)

                # assign packets to links
                for _ in range(num_assignments):
                    i: int = 0
                    for link in links_iter:
                        if i >= len(good_links):
                            # we iterate over the entire list of compatible links and could not
                            # squeeze the packet anywhere, check if we can use incompatible links
                            if channel.qos is not None and \
                                    channel.qos.latency_policy == LatencyPolicy.BEST_EFFORT:
                                links_iter: Iterator[Link] = infinite_iterator(slow_links)
                            break

                        enough_budget: bool = link.budget is None or ((link.budget is not None) and (link.budget >= channel.size))
                        enough_bw: bool = link.capacity is None or ((link.capacity is not None) and (link.capacity >= channel.size))

                        # DEBUG:
                        # print(packets_sent, packets_total,
                        #       link.budget, link.capacity,
                        #       enough_budget, enough_bw)
                        # DEBUG:

                        if enough_budget and enough_bw:
                            # update link's budget
                            if link.budget:
                                link.budget -= channel.size
                            # update link's capacity
                            if link.capacity:
                                link.capacity -= channel.size
                            # assign 1 packet from `channel` to `link`
                            interfaces.append(link.interface)
                            packets_sent += 1
                            break

                        i += 1
                # create solved channel object
                solved_channel: SolvedChannel = SolvedChannel(
                    name=channel.name,
                    frequency=packets_sent / FORMULATE_PROBLEM_EVERY_SEC,
                    # NOTE: we are populating this list without taking into account the bandwidth
                    #       just the capacity, this is not correct, we should compute the link
                    #       usage over time and avoid spikes in the usage that overshoot the
                    #       bandwidth
                    interfaces=self._compact_sequence(interfaces),
                    problem=channel,
                )
                # add solved channel to the solution
                solution.assignments.append(solved_channel)
        # ---
        return solution
