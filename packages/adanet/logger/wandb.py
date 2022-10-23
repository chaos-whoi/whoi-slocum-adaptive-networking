import json
from typing import Any, Dict

import wandb

from adanet.constants import WANDB_API_KEY, WANDB_PROJECT
from adanet.logger.base import Logger


class WandBLogger(Logger):

    def __init__(self):
        wandb.login(key=WANDB_API_KEY)
        self._run = wandb.init(project=WANDB_PROJECT)

    def log(self, t: float, data: Dict[str, Any]):
        if not self.is_active():
            return
        # log to W&B
        step: int = int(t * 1000)

        # DEBUG: remove this
        # print(json.dumps(data, indent=4, sort_keys=True))
        # DEBUG: remove this

        self._run.log(data=data, step=step, commit=False)

    def commit(self, t: float):
        step: int = int(t * 1000)
        self._run.log(data={}, step=step, commit=True)
