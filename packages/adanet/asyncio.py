import asyncio
import functools
from asyncio import AbstractEventLoop
from concurrent.futures import Future
from threading import Thread, current_thread, Event
from typing import Optional, Set

from adanet.time import Clock
from adanet.types import Shuttable


class EventLoop(Shuttable, Thread):

    def __init__(self, start_event):
        Shuttable.__init__(self, priority=-999)
        Thread.__init__(self)
        self.loop: Optional[AbstractEventLoop] = None
        self.tid: Optional[Thread] = None
        self.event = start_event
        self._futures: Set[Future] = set()
        self._tasks: Set[Future] = set()

    @asyncio.coroutine
    def _every(self, period: float, func, *args, **kwargs):
        task_switch: Shuttable = Shuttable()
        future = Future()
        self._futures.add(future)
        # execute until shutdown
        while not task_switch.is_shutdown:
            func(*args, **kwargs)
            yield from asyncio.sleep(Clock.period(period))
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

    def add_task(self, func, every, *args, **kwargs):
        """this method should return a task object, that I
          can cancel, not a handle"""

        def _async_add(_func, _future):
            try:
                ret = _func()
                _future.set_result(ret)
            except Exception as e:
                _future.set_exception(e)

        coro = self._every(every, func, *args, **kwargs)
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
            res = fut.result()
            self._tasks.add(res)
            return res

    def cancel_task(self, task):
        self.loop.call_soon_threadsafe(task.cancel)


event = Event()
loop: EventLoop = EventLoop(event)
loop.start()

# wait for the event loop to be ready before returning
event.wait()
