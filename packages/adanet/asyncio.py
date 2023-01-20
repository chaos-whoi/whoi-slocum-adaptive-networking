import asyncio
import functools
from asyncio import AbstractEventLoop
from concurrent.futures import Future
from threading import Thread, current_thread, Event
from typing import Optional, Set, Callable

from adanet.exceptions import StopTaskException
from adanet.types import Shuttable


class Task(Shuttable):

    def __init__(self, period: float, target: Optional[Callable] = None):
        super(Task, self).__init__()
        self._period: float = period
        self._paused: bool = period < 0
        self._target: Optional[Callable] = target

    @property
    def period(self) -> float:
        return self._period

    @property
    def paused(self) -> bool:
        return self._paused

    @period.setter
    def period(self, value: float):
        self._period = value
        if value < 0:
            self.pause()
        else:
            self.resume()

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def step(self, *args, **kwargs):
        if self._target is None:
            raise ValueError("If you do not subclass 'Task', the field 'target' becomes mandatory")
        self._target(*args, **kwargs)


class EventLoop(Shuttable, Thread):

    def __init__(self, start_event):
        Shuttable.__init__(self, priority=-999)
        Thread.__init__(self)
        self.loop: Optional[AbstractEventLoop] = None
        self.tid: Optional[Thread] = None
        self.event = start_event
        self._futures: Set[Future] = set()

    @asyncio.coroutine
    def _every(self, task: Task, *args, **kwargs):
        future = Future()
        self._futures.add(future)
        # execute until shutdown
        while not task.is_shutdown:
            if not task.paused:
                try:
                    task.step(*args, **kwargs)
                except StopTaskException:
                    return
            yield from asyncio.sleep(task.period)
        # mark task as finished
        future.set_result(None)

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.tid = current_thread()
        # make sure we can shutdown the event loop
        self.register_shutdown_callback(self.stop)
        # mark the event loop as initialized
        self.loop.call_soon(self.event.set)
        self.loop.run_forever()

    def stop(self):
        # wait for all tasks to complete
        for fut in self._futures:
            fut.result()
        # ---
        self.loop.call_soon_threadsafe(self.loop.stop)

    def add_task(self, task: Task, *args, **kwargs):
        """this method should return a task object, that I
          can cancel, not a handle"""

        def _async_add(_func, _future):
            try:
                ret = _func()
                _future.set_result(ret)
            except Exception as e:
                _future.set_exception(e)

        coro = self._every(task, *args, **kwargs)
        f = functools.partial(asyncio.ensure_future, coro, loop=self.loop)
        if current_thread() == self.tid:
            # We can call directly if we're not going between threads.
            return f()

        else:
            # We're in a non-event loop thread so we use a Future
            # to get the task from the event loop thread once
            # it's ready.
            fut = Future()
            self.loop.call_soon_threadsafe(_async_add, f, fut)
            return fut.result()

    def cancel_task(self, task):
        self.loop.call_soon_threadsafe(task.cancel)


event = Event()
loop: EventLoop = EventLoop(event)
loop.start()

# wait for the event loop to be ready before returning
event.wait()
