import datetime
import os
from threading import Semaphore
from typing import Any, Dict, Optional

import wandb

from adanet.constants import WANDB_API_KEY, WANDB_PROJECT, WANDB_OFFLINE, WANDB_NAME
from adanet.logger.base import Logger
from adanet.types.agent import AgentRole


class WandBLogger(Logger):

    def __init__(self, agent: str, role: AgentRole):
        if WANDB_OFFLINE:
            os.environ["WANDB_MODE"] = "offline"
        else:
            wandb.login(key=WANDB_API_KEY)
        self._lock: Semaphore = Semaphore()
        # pick a name for the run
        name: Optional[str] = WANDB_NAME
        if name is None:
            date = datetime.datetime.now().strftime("%b%d%y_%H:%M:%S")
            name = f"{agent}_{role.value}_{date}"
        self._run = wandb.init(project=WANDB_PROJECT, name=name)
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
