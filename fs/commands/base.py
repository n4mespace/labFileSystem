import logging
from abc import abstractmethod, ABC

from fs.config import SystemConfig
from fs.driver.memory import MemoryStorageProxy


class BaseFSCommand(ABC):
    _memory_proxy = MemoryStorageProxy()
    _system_data = SystemConfig()

    _logger = logging.getLogger(__name__)

    @abstractmethod
    def exec(self) -> None:
        raise NotImplementedError

    @property
    def config(self) -> SystemConfig:
        with self._system_data.config as system_config:
            return system_config
