import time
from threading import Thread
from typing import Optional

from adanet.queue.base import IQueue, QueueType
from adanet.types.pipes import IPipe
from ..queue.lazy import Queue as LazyQueue
from ..queue.sqlite import Queue as SQLiteQueue
from ..types import Shuttable
from ..types.misc import Reminder
from ..types.problem import ChannelQoS


class ISource(IPipe):

    def __init__(self, name: str, size: int, frequency: float = 0.0, *_, **kwargs):
        super(ISource, self).__init__(name=name, size=size)
        self._frequency: float = frequency
        self._solution_frequency: float = 0.0
        self._qos: Optional[ChannelQoS] = kwargs.get("qos", None)
        self._reminder: Optional[Reminder] = Reminder(frequency=self._qos.frequency) \
            if (self._qos and self._qos.frequency is not None) else None
        queue_size: int = kwargs.get("queue_size", 1)
        self._windmill: MessageWindmill = MessageWindmill(self, QueueType.CACHE, queue_size)
        self._windmill.start()

    @property
    def frequency(self) -> float:
        return self._frequency

    @property
    def queue_length(self) -> int:
        return self._windmill.queue_length

    @property
    def solution_frequency(self) -> float:
        return self._solution_frequency

    @property
    def _is_time(self) -> bool:
        return self._reminder.is_time()

    def set_solution_frequency(self, value: float):
        self._solution_frequency = value

    def inject(self, data: bytes):
        self._on_data(data)

    def _produce(self, data: bytes):
        # TODO: maybe this is not correct, shouldn't we queue messages at max speed and only
        #  throttle the transmission? or we throttle the source so we queue at qos speed
        #  (think of an image stream, better to have a lower fps but larger temporal span
        #  than the other way around)
        if self._is_time:
            self._windmill.put(data)


class MessageWindmill(Shuttable, Thread):

    def __init__(self, source: ISource, queue_type: QueueType, queue_size: int):
        Shuttable.__init__(self)
        Thread.__init__(self, daemon=True)
        self._source: ISource = source
        self._queue: IQueue = MessageWindmill.make_queue(source.name, queue_type, queue_size)

    @property
    def is_spinning(self) -> bool:
        return self._source.solution_frequency > 0

    @property
    def queue_length(self) -> int:
        return self._queue.length

    @property
    def _sleep_period(self) -> float:
        if self._source.solution_frequency <= 0:
            # default safe frequency is 1.0Hz
            return 1.0
        return 1.0 / self._source.solution_frequency

    def put(self, data: bytes):
        self._queue.put(data)

    def run(self) -> None:
        while not self.is_shutdown:
            time.sleep(self._sleep_period)
            if not self.is_spinning:
                continue
            data: bytes = self._queue.get(block=True)
            self._source.inject(data)

    @staticmethod
    def make_queue(channel: str, type: QueueType, size: int):
        if type is QueueType.CACHE:
            if size == 1:
                return LazyQueue(type, channel)
            return SQLiteQueue(type, channel, size, multithreading=True, memory=size < 100)
        elif type is QueueType.PERSISTENT:
            return SQLiteQueue(type, channel, size, multithreading=True)
