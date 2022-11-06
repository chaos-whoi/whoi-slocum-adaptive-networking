from adanet.engine import Engine
from adanet.solver import SimpleSolver
from adanet.types.agent import AgentRole


# load problem from disk


engine = Engine(
    role=AgentRole.SOURCE,
    solver=SimpleSolver,
    problem=problem
)
engine.start()
