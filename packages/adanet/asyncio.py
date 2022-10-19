import asyncio
from threading import Thread
from typing import Callable

from adanet.types import Shuttable


class EventLoop(Shuttable, Thread):

    _loop = asyncio.get_event_loop()
    _loop.run_forever()

    @staticmethod
    async def _every(seconds: float, func, *args, **kwargs):
        while True:
            func(*args, **kwargs)
            await asyncio.sleep(seconds)

    @staticmethod
    async def _await(func, *args, **kwargs):
        return func(*args, **kwargs)

    @staticmethod
    def create_task(func: Callable, every_sec: float, *args, **kwargs):
        EventLoop._loop.create_task(EventLoop._every(every_sec, func, *args, **kwargs))

    @staticmethod
    def create_oneshot_task(func: Callable, *args, **kwargs):
        EventLoop._loop.create_task(EventLoop._await(func, *args, **kwargs))
