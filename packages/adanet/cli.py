import argparse
import os
from pathlib import Path
from typing import Optional

import yaml

from adanet.asyncio import loop, Task
from adanet.constants import DEFAULT_SOLVER
from adanet.engine import Engine
from adanet.exceptions import StopTaskException
from adanet.logger.wandb import WandBLogger
from adanet.simulation import Simulator
from adanet.solver import solvers
from adanet.time import Clock
from adanet.types.agent import AgentRole
from adanet.types.problem import Problem
from adanet.types.report import Report


def duration_monitor(engine: Engine, duration: float, stime: float):
    if (Clock.relative_time() - stime) >= Clock.period(duration):
        print(f"Reached limit duration of {duration} secs, shutting down...")
        engine.shutdown()
        raise StopTaskException()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("role", type=str, choices=["source", "sink"],
                        help="Role of this instance")
    parser.add_argument("-a", "--agent", required=True, type=str,
                        help="Agent name")
    parser.add_argument("-s", "--solver", required=False, type=str, choices=solvers.keys(),
                        default=DEFAULT_SOLVER,
                        help="Name of the class to instantiate the solver from")
    parser.add_argument("-p", "--problem", required=True, type=str,
                        help="Path to a problem definition file")
    parser.add_argument("-d", "--duration", type=float, default=None,
                        help="Duration of the run, program will end once the duration is reached")
    parser.add_argument("-S", "--simulation", default=False, action="store_true",
                        help="Simulate problem")
    parser.add_argument("-l", "--logger", required=False, type=str, default=None, choices=["wb"],
                        help="Logger to attach to the engine")
    parsed = parser.parse_args()

    # check duration value
    if parsed.duration is not None and parsed.duration <= 2:
        print("FATAL: duration cannot be less than 2 seconds")

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

    # extend channels to be of two types 'live/...' and 'cached/...'
    if False:
        # TODO: temporarily disabled
        problem.categorize_channels(categories=["live", "cached"])

    # activate logger (if needed)
    if parsed.logger == "wb":
        logger = WandBLogger(parsed.agent, role)
        Report.attach_logger(logger)

    # pointers
    engine: Optional[Engine] = None

    # - 'source' agent
    if role is AgentRole.SOURCE:
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

        # create duration monitor (if needed)
        if parsed.duration is not None:
            monitor: Task = Task(0.1, target=duration_monitor)
            loop.add_task(monitor, engine, parsed.duration, Clock.relative_time())

    # - 'sink' agent
    elif role is AgentRole.SINK:
        # spin up engine
        print("Instantiating engine with:\n"
              f"\trole: {role.name}\n"
              f"\tproblem: {problem_fpath}\n")
        engine = Engine(role=role, problem=problem)
        engine.start()

        # create duration monitor (if needed)
        if parsed.duration is not None:
            monitor: Task = Task(0.1, target=duration_monitor)
            loop.add_task(monitor, engine, parsed.duration, Clock.relative_time())

    # wait for the engine to finish
    engine.join()


if __name__ == '__main__':
    main()
