import os

import yaml

from adanet.engine import Engine
from adanet.solver import SimpleSolver
from adanet.types.problem import Problem

# get problem file path from environment variable
problem_fpath = os.environ.get("PROBLEM_FPATH", None)
if problem_fpath is None:
    raise ValueError("Environment variable 'PROBLEM_FPATH' is not set")
if not os.path.isfile(problem_fpath):
    raise FileNotFoundError(f"Problem file '{problem_fpath}' not found")

# load problem file from disk
with open(problem_fpath, "rt") as fin:
    problem = Problem.parse_obj(**yaml.safe_load(fin))

# spin up engine
engine = Engine(solver=SimpleSolver, problem=problem)

# wait for the engine to finish
engine.join()
