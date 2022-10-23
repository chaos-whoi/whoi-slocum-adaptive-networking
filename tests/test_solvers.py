import os
from typing import Dict, Iterator

import yaml

from adanet.constants import FORMULATE_PROBLEM_EVERY_SEC
from adanet.solver import AbsSolver, SimpleSolver
from adanet.types.problem import Problem, Link, LatencyPolicy
from adanet.types.solution import Solution
from adanet.utils import infinite_iterator

problems_fpath = "/data/tests/"


simple_solver: AbsSolver = SimpleSolver()


def _load_problem(name: str) -> Problem:
    problem_fpath: str = os.path.join(problems_fpath, name)
    with open(problem_fpath, "rt") as fin:
        return Problem.parse_obj(yaml.safe_load(fin))


def _ensure_feasibility(problem: Problem, solution: Solution):
    # compute link's capacity
    for link in problem.links:
        link.capacity = link.bandwidth * FORMULATE_PROBLEM_EVERY_SEC
    # consume link capacity according to assignments
    links: Dict[str, Link] = {link.interface: link for link in problem.links}
    for c in solution.assignments:
        packets_sent: int = int(c.frequency * FORMULATE_PROBLEM_EVERY_SEC)
        interfaces: Iterator[str] = infinite_iterator(c.interfaces)
        i: int = 0
        for interface in interfaces:
            if i > packets_sent:
                break
            i += 1
            # ---
            links[interface].capacity -= c.problem.size
    # make sure no links are over-used
    for link in problem.links:
        assert link.capacity >= 0
    # make sure channels that have a strict latency policy do not use slow links
    for c in solution.assignments:
        if c.problem.qos is None:
            continue
        if c.problem.qos.latency is None:
            continue
        if c.problem.qos.latency_policy is LatencyPolicy.BEST_EFFORT:
            continue
        # this channel has a strict latency policy
        for iface in set(c.interfaces):
            assert c.problem.qos.latency >= links[iface].latency


def test_simplesolver_no_links():
    problem: Problem = _load_problem("no-links.yaml")
    solution: Solution = simple_solver.solve(problem)
    # make sure solution is feasible and respects the problem's constraints
    _ensure_feasibility(problem, solution)
    # known solution
    for c in solution.assignments:
        assert c.interfaces == []


def test_simplesolver_no_channels():
    problem: Problem = _load_problem("no-channels.yaml")
    solution: Solution = simple_solver.solve(problem)
    # make sure solution is feasible and respects the problem's constraints
    _ensure_feasibility(problem, solution)
    # known solution
    assert solution.assignments == []


def test_simplesolver_one_wifi_two_channels():
    problem: Problem = _load_problem("one-wifi-two-channels.yaml")
    solution: Solution = simple_solver.solve(problem)
    # make sure solution is feasible and respects the problem's constraints
    _ensure_feasibility(problem, solution)
    # known solution, channels split the wifi link
    for c in solution.assignments:
        assert c.interfaces == ["wlan0"]
        assert c.frequency == c.problem.frequency


def test_simplesolver_two_wifis_two_channels():
    problem: Problem = _load_problem("two-wifis-two-channels.yaml")
    solution: Solution = simple_solver.solve(problem)
    # make sure solution is feasible and respects the problem's constraints
    _ensure_feasibility(problem, solution)
    # known solution, channels split the wifi links and alternate between the two
    for c in solution.assignments:
        assert c.interfaces == ["wlan0", "wlan1"]
        assert c.frequency == c.problem.frequency


def test_simplesolver_two_wifis_one_metered():
    problem: Problem = _load_problem("two-wifis-one-metered.yaml")
    solution: Solution = simple_solver.solve(problem)
    # make sure solution is feasible and respects the problem's constraints
    _ensure_feasibility(problem, solution)
    # known solution:
    assert solution.assignments[0].name == "/channel_1"
    assert solution.assignments[1].name == "/channel_2"
    # - channel 1 is going to consume the whole budget on wlan0 with the first 20
    #   messages (10 on wlan0 and 10 on wlan1)
    assert solution.assignments[0].interfaces[0:20] == ["wlan0", "wlan1"] * 10
    # - channel 1 is going to use wlan1 for the remainder of the messages
    assert set(solution.assignments[0].interfaces[20:]) == {"wlan1"}
    # - channel 2 can only be served by wlan1 as wlan0 was depleted by channel 1
    assert solution.assignments[1].interfaces == ["wlan1"]
    # - frequencies are satisfied on both channels
    assert solution.assignments[0].frequency == problem.channels[0].frequency
    assert solution.assignments[1].frequency == problem.channels[1].frequency


def test_simplesolver_two_wifis_one_metered_priority():
    problem: Problem = _load_problem("two-wifis-one-metered-priority.yaml")
    solution: Solution = simple_solver.solve(problem)
    # make sure solution is feasible and respects the problem's constraints
    _ensure_feasibility(problem, solution)
    # known solution:
    assert solution.assignments[0].name == "/channel_2"
    assert solution.assignments[1].name == "/channel_1"
    # - channel 2 (highest priority) is going to consume the whole budget on wlan0 with the
    #   first 20 messages (10 on wlan0 and 10 on wlan1)
    assert solution.assignments[0].interfaces[0:20] == ["wlan0", "wlan1"] * 10
    # - channel 2 is going to use wlan1 for the remainder of the messages
    assert set(solution.assignments[0].interfaces[20:]) == {"wlan1"}
    # - channel 1 (lowest priority) can only be served by wlan1 as wlan0 was depleted by channel 2
    assert solution.assignments[1].interfaces == ["wlan1"]
    # - frequencies are satisfied on both channels
    assert solution.assignments[0].frequency == problem.channels[1].frequency
    assert solution.assignments[1].frequency == problem.channels[0].frequency


def test_simplesolver_wifi_acoustic_1():
    problem: Problem = _load_problem("wifi-acoustic-1.yaml")
    solution: Solution = simple_solver.solve(problem)
    # make sure solution is feasible and respects the problem's constraints
    _ensure_feasibility(problem, solution)
    # known solution
    # TODO: update this unit problem
