import logging
from abc import abstractmethod, ABC
from typing import Any

from fs.config import SystemConfig
from fs.driver.memory import MemoryStorageProxy


class BaseFSCommand(ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

        self._memory_proxy = MemoryStorageProxy()
        self._system_data = SystemConfig()

        self._logger = logging.getLogger(__name__)

    @abstractmethod
    def exec(self) -> None:
        raise NotImplementedError("Command must implement its exec method.")
