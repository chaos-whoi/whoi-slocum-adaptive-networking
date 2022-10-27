import os
from typing import Any, Dict

import wandb

from adanet.constants import WANDB_API_KEY, WANDB_PROJECT, WANDB_OFFLINE
from adanet.logger.base import Logger


class WandBLogger(Logger):

    def __init__(self):
        if WANDB_OFFLINE:
            os.environ["WANDB_MODE"] = "offline"
        wandb.login(key=WANDB_API_KEY)
        self._run = wandb.init(project=WANDB_PROJECT)

    def log(self, t: float, data: Dict[str, Any]):
        if not self.is_active():
            return
        # log to W&B
        step: int = int(t * 1000)
        self._run.log(data=data, step=step, commit=False)

    def commit(self, t: float):
        step: int = int(t * 1000)
        self._run.log(data={}, step=step, commit=True)
