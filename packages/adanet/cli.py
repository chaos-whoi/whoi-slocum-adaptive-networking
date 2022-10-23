import argparse
import os
from pathlib import Path
from typing import Optional

import yaml

from adanet.engine import Engine
from adanet.logger.wandb import WandBLogger
from adanet.simulation import Simulator
from adanet.solver import solvers
from adanet.types.agent import AgentRole
from adanet.types.problem import Problem
from adanet.types.report import Report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("role", type=str, choices=["robot", "ship"],
                        help="Role of this instance, either 'robot' or 'ship'")
    parser.add_argument("-s", "--solver", required=True, type=str, choices=solvers.keys(),
                        help="Name of the class to instantiate the solver from")
    parser.add_argument("-p", "--problem", required=True, type=str,
                        help="Path to a problem definition file")
    parser.add_argument("-S", "--simulation", default=False, action="store_true",
                        help="Simulate problem")
    parser.add_argument("-l", "--logger", required=False, type=str, default=None,
                        choices=["wb"],
                        help="Logger to attach to the engine")
    parsed = parser.parse_args()

    # instantiate agent
    role: AgentRole = AgentRole(parsed.role)

    # make sure problem file exists
    problem_fpath: str = os.path.abspath(parsed.problem)
    if problem_fpath is None:
        raise ValueError("Environment variable 'PROBLEM_FPATH' is not set")
    if not os.path.isfile(problem_fpath):
        raise FileNotFoundError(f"Problem file '{problem_fpath}' not found")
    problem_fpath: Path = Path(problem_fpath)

    # load problem file from disk
    with open(problem_fpath, "rt") as fin:
        problem_name: str = problem_fpath.stem
        problem = Problem.parse_obj({"name": problem_name, **yaml.safe_load(fin)})
    print("Problem loaded:\n\t" + "\n\t".join(problem.as_yaml().splitlines()) + "\n")

    # activate logger (if needed)
    if parsed.logger == "wb":
        logger = WandBLogger()
        Report.attach_logger(logger)

    # - robot agent
    if role is AgentRole.ROBOT:
        # create problem simulator (if needed)
        simulator: Optional[Simulator] = None
        if parsed.simulation:
            simulator: Simulator = Simulator(problem)

        # pick the right solver
        solver = solvers[parsed.solver]

        # spin up engine
        print("Instantiating engine with:\n"
              f"\trole: {role.name}\n"
              f"\tsolver: {parsed.solver}\n"
              f"\tproblem: {problem_fpath}\n")
        engine = Engine(role=role, solver=solver, problem=problem, simulator=simulator)
        engine.start()

        # wait for the engine to finish
        engine.join()


if __name__ == '__main__':
    main()
