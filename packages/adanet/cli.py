import argparse
import os

import yaml

from adanet.engine import Engine
from adanet.solver import solvers
from adanet.types.agent import AgentRole
from adanet.types.problem import Problem


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("role", type=str, choices=["robot", "ship"],
                        help="Role of this instance, either 'robot' or 'ship'")
    parser.add_argument("-s", "--solver", required=True, type=str, choices=solvers.keys(),
                        help="Name of the class to instantiate the solver from")
    parser.add_argument("-p", "--problem", required=True, type=str,
                        help="Path to a problem definition file")
    parsed, remaining = parser.parse_known_args()

    # instantiate agent
    role: AgentRole = AgentRole(parsed.role)

    # make sure problem file exists
    problem_fpath: str = os.path.abspath(parsed.problem)
    if problem_fpath is None:
        raise ValueError("Environment variable 'PROBLEM_FPATH' is not set")
    if not os.path.isfile(problem_fpath):
        raise FileNotFoundError(f"Problem file '{problem_fpath}' not found")

    # load problem file from disk
    with open(problem_fpath, "rt") as fin:
        problem = Problem.parse_obj(yaml.safe_load(fin))
    print("Problem loaded:\n\t" + "\n\t".join(problem.as_yaml().splitlines()) + "\n")

    # spin up engine
    solver = solvers[parsed.solver]
    print("Instantiating engine with:\n"
          f"\trole: {role.name}\n"
          f"\tsolver: {parsed.solver}\n"
          f"\tproblem: {problem_fpath}\n")
    engine = Engine(role=role, solver=solver, problem=problem)

    # wait for the engine to finish
    engine.join()


if __name__ == '__main__':
    main()
