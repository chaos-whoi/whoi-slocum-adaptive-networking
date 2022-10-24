import os
import time


_stime: float = time.time()
_correction: float = float(os.environ.get("TIME_SPEED", 1.0))


class Clock:

    @staticmethod
    def _correct_time(t: float) -> float:
        return _stime + (t - _stime) * _correction

    @staticmethod
    def period(t: float) -> float:
        return t / _correction

    @staticmethod
    def time() -> float:
        return Clock._correct_time(time.time())

    @staticmethod
    def relative_time() -> float:
        return Clock.time() - _stime

    @staticmethod
    def true_time() -> float:
        return time.time()
