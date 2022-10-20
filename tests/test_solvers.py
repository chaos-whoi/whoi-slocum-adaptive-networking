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


def test_simplesolver_wifi_acoustic_1():
    problem: Problem = _load_problem("wifi-acoustic-1.yaml")
    solution: Solution = simple_solver.solve(problem)
    # make sure solution is feasible and respects the problem's constraints
    _ensure_feasibility(problem, solution)
    # known solution
