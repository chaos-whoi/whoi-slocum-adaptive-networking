from typing import Set, Any, ClassVar, Dict, Union, Type, Optional

from flatdict import FlatDict

from adanet.constants import REPORT_PRECISION_SEC
from adanet.logger.base import Logger
from adanet.time import Clock
from adanet.types.problem import Problem
from adanet.types.solution import Solution


class Report:
    _problem_counter: ClassVar[int] = 0
    _solution_counter: ClassVar[int] = 0
    _loggers: Set[Logger] = set()
    _last_committed: float = -1.0

    @classmethod
    def attach_logger(cls, logger: Logger):
        cls._loggers.add(logger)

    @classmethod
    def log(cls, data: Union[Problem, Solution, dict]):
        t_precision_ms = REPORT_PRECISION_SEC * 1000
        t: float = (((Clock.relative_time() * 1000) // t_precision_ms) * t_precision_ms) / 1000
        d_type: Type = type(data)
        # increase and log counters
        if d_type is Problem:
            d: Dict[str, Any] = {
                "t": t,
                "problem/counter": Report._problem_counter,
                **Report._dictify("problem", data)
            }
            Report._problem_counter += 1
        elif d_type is Solution:
            # create full dict container
            d: Dict[str, Any] = {
                "t": t,
                "solution/counter": Report._solution_counter,
                **Report._dictify("solution", data)
            }
            Report._solution_counter += 1
        else:
            # create full dict container
            d: Dict[str, Any] = {"t": t, **data}

        # commit
        to_commit: Optional[float] = None
        if t > cls._last_committed:
            to_commit = cls._last_committed
            cls._last_committed = t

        # send data to loggers
        for logger in cls._loggers:
            logger.log(t, d)
            if to_commit:
                logger.commit(to_commit)

    @staticmethod
    def _dictify(prefix: str, v: Union[Problem, Solution]) -> dict:
        d: dict = {prefix: v.report()}
        return {k: (v if not isinstance(v, FlatDict) else v.as_dict()) for k, v in
                FlatDict(d, delimiter="/").items()}

        # return d
        # return flat_dict.encode(d, "/")
