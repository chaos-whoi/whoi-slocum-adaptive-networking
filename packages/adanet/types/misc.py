import json
import signal
import threading
from threading import Semaphore
from time import sleep
from abc import abstractmethod
from collections import Callable, defaultdict
from typing import Set, Dict, List, Optional
from threading import Condition

import yaml
from pydantic import BaseModel

from ..constants import INFTY
from ..exceptions import InvalidStateError
from ..time import Clock


class GenericModel(BaseModel):
    class Config:
        underscore_attrs_are_private = True
        use_enum_values = True

    def as_json(self) -> str:
        return self.json(sort_keys=True, indent=4)

    def as_yaml(self) -> str:
        return yaml.safe_dump(json.loads(self.as_json()), sort_keys=True, indent=4)

    @abstractmethod
    def report(self) -> dict:
        pass


class Shuttable:
    _shuttables: Dict[int, Set['Shuttable']] = defaultdict(set)

    def __init__(self, priority: int = 0):
        self._is_shutdown: bool = False
        self._callbacks: Set[Callable] = set()
        # keep track of all shuttables
        Shuttable._shuttables[priority].add(self)

    @property
    def is_shutdown(self) -> bool:
        return self._is_shutdown

    def register_shutdown_callback(self, cb: Callable):
        if self.is_shutdown:
            classes = [cls.__name__ for cls in type(self).__class__.__subclasses__()]
            raise InvalidStateError(f"Object of type {classes} received a request to register "
                                    f"a new shutdown callback but the instance was already "
                                    f"shutdown.")
        self._callbacks.add(cb)

    def join(self, nap_duration: float = 0.25) -> None:
        """
        Blocks until this Shuttable is shut down.

        :param nap_duration: how often (in seconds) we wake up and check for change in status
        """
        # if we are joining from main thread, register signal handler
        if threading.current_thread() is threading.main_thread():

            def handler(signum, _):
                signame = signal.Signals(signum).name
                print(f"Received {signame} signal, exiting...")
                self.shutdown()

            # register as SIGINT and SIGTERM signal handler
            print("Registering for shutdown signals SIGINT...")
            signal.signal(signal.SIGINT, handler)
            print("Registering for shutdown signals SIGTERM...")
            signal.signal(signal.SIGTERM, handler)

        try:
            while not self.is_shutdown:
                sleep(nap_duration)
        except KeyboardInterrupt:
            print("Received a Keyboard Interrupt, exiting...")
        Shuttable.shutdown_all()

    def mark_as_shutdown(self):
        self._is_shutdown = True

    def shutdown(self):
        was_shutdown = self.is_shutdown
        # mark as shutdown
        self.mark_as_shutdown()
        # notify callbacks
        if not was_shutdown:
            for cb in self._callbacks:
                cb()

    @classmethod
    def shutdown_all(cls):
        for priority in sorted(cls._shuttables.keys(), reverse=True):
            for shuttable in cls._shuttables[priority]:
                shuttable.shutdown()


class Reminder:

    def __init__(self, period=None, frequency=None, right_away: bool = False):
        self._period = Reminder._get_period(period, frequency)
        self._last_execution = -INFTY if right_away else Clock.time()

    def reset(self):
        self._last_execution = Clock.time()

    def is_time(self, period=None, frequency=None, dry_run=False):
        _period = self._period
        # use provided period/frequency (if any)
        if period is not None or frequency is not None:
            _period = Reminder._get_period(period, frequency)
        # ---
        _since_last = Clock.time() - self._last_execution
        _is_time = _since_last >= _period
        if _is_time and not dry_run:
            _residual = _since_last - _period if self._last_execution >= 0 else 0
            self._last_execution = Clock.time() - _residual
        return _is_time

    @staticmethod
    def _get_period(period=None, frequency=None):
        # period or frequency has to be given
        if period is None and frequency is None:
            raise ValueError('When you construct an object of type Reminder you need '
                             'to provide either a `period` or a `frequency`.')
        # period and frequency cannot be set at the same time
        if period is not None and frequency is not None:
            raise ValueError('When you construct an object of type Reminder you need '
                             'to provide either a `period` or a `frequency`, not both.')
        # get period
        _period = 0
        if period is not None:
            if not isinstance(period, (int, float)):
                raise ValueError('Parameter `period` must be a number, got {:s} instead'.format(
                    str(type(period))
                ))
            _period = period
        if frequency is not None:
            if not isinstance(frequency, (int, float)):
                raise ValueError('Parameter `frequency` must be a number, got {:s} instead'.format(
                    str(type(frequency))
                ))
            _period = Clock.period(1.0 / frequency)
        # ---
        return _period


class FlowWatch:

    def __init__(self, size: int = 20):
        self._size: int = size
        self._diffs: List[float] = [0] * size
        self._cursor: int = 0
        self._counter: int = 0
        self._total: int = 0
        self._last_total: float = 0
        self._last_reset: float = Clock.time()
        self._last_signal: Optional[float] = None
        self._lock: Semaphore = Semaphore()

    @property
    def counter(self) -> int:
        return self._counter

    @property
    def volume(self) -> int:
        return self._total

    @property
    def speed(self) -> float:
        elapsed: float = Clock.real_period(Clock.time() - self._last_reset)
        return (self._total - self._last_total) / elapsed

    @property
    def frequency(self) -> float:
        # DEBUG:
        # print(self._diffs,
        #       [Clock.real_period(d) for d in self._diffs if d],
        #       [1.0 / Clock.real_period(d) for d in self._diffs if d])
        # DEBUG:
        # trust the estimate at a percentage directly proportional to the amount of data we have
        smooth: float = min(self._counter / (self._size * 0.5), 1.0)
        s: float = sum(self._diffs)
        t: float = Clock.real_period(s / min(self._size, self._counter))
        f: float = (1.0 / t) * smooth if t else 0.0
        return f

    def reset(self):
        with self._lock:
            self._last_total: float = self._total
            self._last_reset: float = Clock.time()
            # self._total = 0
            # self._counter = 0
            # self._cursor = 0
            # self._diffs = [0] * self._size
            # self._last_signal = None

    def signal(self, value: int):
        with self._lock:
            now: float = Clock.time()
            if self._last_signal is None:
                self._counter += 1
                self._total += value
                self._last_signal = now
                return
            # compute diff
            self._cursor = self._cursor % self._size
            diff: float = now - self._last_signal
            self._diffs[self._cursor] = diff
            self._cursor += 1
            self._counter += 1
            self._total += value
            self._last_signal = now


class MonitoredCondition(Condition):

    def __init__(self):
        super(MonitoredCondition, self).__init__()
        self._has_changes = False

    def clear(self):
        self._has_changes = False

    def notifyAll(self) -> None:
        return self.notify_all()

    def notify_all(self) -> None:
        self._has_changes = True
        super(MonitoredCondition, self).notify_all()

    def notify(self, n: int = 1) -> None:
        self._has_changes = True
        super(MonitoredCondition, self).notify(n=n)

    def wait(self, timeout: Optional[float] = None) -> bool:
        if self._has_changes:
            self._has_changes = False
            return True
        return super(MonitoredCondition, self).wait(timeout=timeout)


class MaxWindow:

    def __init__(self, size: int = 5):
        self._size: int = size
        # noinspection PyTypeChecker
        self._data: List[Optional[float]] = [0.0] + ([None] * (size - 1))
        self._cursor: int = 0
        self._lock: Semaphore = Semaphore()

    def add(self, value: float):
        with self._lock:
            self._data[self._cursor] = value
            self._cursor = (self._cursor + 1) % self._size

    @property
    def value(self) -> float:
        with self._lock:
            return max([v for v in self._data if v is not None])

    @property
    def last(self) -> float:
        with self._lock:
            return self._data[self._cursor]
