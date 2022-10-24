import os
import time


class Clock:
    _stime: float = time.time()
    _correction: float = float(os.environ.get("TIME_SPEED", 1.0))

    @staticmethod
    def reset():
        Clock._stime = time.time()

    @staticmethod
    def _correct_time(t: float) -> float:
        return Clock._stime + (t - Clock._stime) * Clock._correction

    @staticmethod
    def period(t: float) -> float:
        return t / Clock._correction

    @staticmethod
    def time() -> float:
        return Clock._correct_time(time.time())

    @staticmethod
    def relative_time() -> float:
        return Clock.time() - Clock._stime

    @staticmethod
    def true_time() -> float:
        return time.time()
