import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from constants import PATH_DIVIDER, ROOT_DIRECTORY_PATH
from fs.driver.memory import MemoryStorageProxy
from fs.driver.state import SystemState
from fs.exceptions import DirectoryNotExists, FileNotExists
from fs.models.descriptor.base import Descriptor
from fs.models.descriptor.directory import DirectoryDescriptor
from fs.models.descriptor.file import FileDescriptor
from fs.models.path import ResolvedPath


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

    def _resolve_absolute_path(
        self, path: Optional[str] = None, to_dir: bool = False
    ) -> ResolvedPath:
        path_parts = path.rsplit(PATH_DIVIDER, maxsplit=1)

        fs_object_name = path_parts[-1]
        directory_path = path_parts[-2] if len(path_parts) > 1 and not to_dir else path

        directory = self.get_directory_descriptor_by_path(directory_path)

        return ResolvedPath(
            directory=directory,
            directory_path=directory_path,
            fs_object_name=fs_object_name,
            fs_object_path=path,
        )

    def _resolve_relative_path(
        self, path: Optional[str] = None, to_dir: bool = False
    ) -> ResolvedPath:
        cwd = self._system_state.get_cwd()
        path = cwd + PATH_DIVIDER + path

        return self._resolve_absolute_path(path, to_dir)

    def resolve_path(
        self, origin_path: Optional[str] = None, to_dir: bool = False
    ) -> ResolvedPath:
        self_point_paths = {ROOT_DIRECTORY_PATH, ".", ".."}
        cwd = self._system_state.get_cwd()

        path = origin_path or cwd
        path = cwd if path in self_point_paths else path

        if origin_path in self_point_paths:
            resolver_path = self._resolve_absolute_path(path, to_dir)
            resolver_path.fs_object_path = resolver_path.directory_path
            return resolver_path

        elif path.startswith(PATH_DIVIDER) or path in self_point_paths:
            return self._resolve_absolute_path(path, to_dir)

        return self._resolve_relative_path(path, to_dir)

    def get_directory_descriptor_by_path(self, path: str) -> DirectoryDescriptor:
        descriptor_id = self._system_state.get_descriptor_id(path)

        if descriptor_id is None:
            raise DirectoryNotExists("Can't find directory with such a path.")

        descriptor_blocks = self._system_state.get_descriptor_blocks(descriptor_id)

        return self._memory_proxy.get_directory_descriptor(
            descriptor_id, descriptor_blocks
        )

    def get_file_descriptor_by_path(self, path: str) -> FileDescriptor:
        descriptor_id = self._system_state.get_descriptor_id(path)

        if descriptor_id is None:
            raise FileNotExists("Can't find file with such a path.")

        descriptor_blocks = self._system_state.get_descriptor_blocks(descriptor_id)

        return self._memory_proxy.get_file_descriptor(descriptor_id, descriptor_blocks)
