from abc import abstractmethod, ABC
from typing import Optional, Tuple, Any, Dict


class Logger(ABC):

    @staticmethod
    def is_active() -> bool:
        return True

    @abstractmethod
    def log(self, t: float, data: Dict[str, Any]):
        raise NotImplementedError()

    @abstractmethod
    def commit(self, t: float):
        raise NotImplementedError()
