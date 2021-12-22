import logging
from abc import ABC, abstractmethod
from typing import Any

from fs.driver.memory import MemoryStorageProxy
from fs.driver.state import SystemState
from fs.models.descriptor.base import Descriptor


class BaseFSCommand(ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

        self._memory_proxy = MemoryStorageProxy()
        self._system_state = SystemState()

        self._logger = logging.getLogger(__name__)

    @abstractmethod
    def exec(self) -> None:
        raise NotImplementedError("Command must implement its exec method.")

    def save(self, descriptor: Descriptor, path: str) -> None:
        self._memory_proxy.write(descriptor)
        self._system_state.write(descriptor, path)
