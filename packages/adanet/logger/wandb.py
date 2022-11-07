import os
from threading import Semaphore
from typing import Any, Dict

import wandb

from adanet.constants import WANDB_API_KEY, WANDB_PROJECT, WANDB_OFFLINE
from adanet.logger.base import Logger


class WandBLogger(Logger):

    def __init__(self):
        if WANDB_OFFLINE:
            os.environ["WANDB_MODE"] = "offline"
        wandb.login(key=WANDB_API_KEY)
        self._lock: Semaphore = Semaphore()
        self._run = wandb.init(project=WANDB_PROJECT)
        self._buffer: dict = {}
        self._step: int = -1

    def log(self, t: float, data: Dict[str, Any]):
        if not self.is_active():
            return
        # log to W&B
        step: int = int(t * 1000)
        # ignore old data
        if step >= self._step:
            with self._lock:
                self._buffer.update(data)

        # TODO: do not use wandb.log every time, it is very inefficient, accumulate and then .log on commit
        # self._run.log(data=data, step=step, commit=False)

    def commit(self, t: float):
        with self._lock:
            self._step: int = int(t * 1000)
            self._run.log(data=self._buffer, step=self._step, commit=True)
            self._buffer.clear()
