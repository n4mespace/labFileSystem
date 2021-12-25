import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from constants import MAX_SYMLINK_HOPS, PATH_DIVIDER, ROOT_DIRECTORY_PATH
from fs.driver.memory import MemoryStorageProxy
from fs.driver.state import SystemState
from fs.exceptions import (DirectoryNotExists, FileNotExists,
                           MaxSymlinkHopsExceeded)
from fs.models.descriptor.base import Descriptor
from fs.models.descriptor.directory import DirectoryDescriptor
from fs.models.descriptor.file import FileDescriptor
from fs.models.descriptor.symlink import SymlinkDescriptor
from fs.models.path import ResolvedPath


class BaseFSCommand(ABC):
    symlink_hop_cnt = 0

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

    def _check_path_parts(
        self,
        path: str,
        prev_path: Optional[list[str]] = None,
        resolve_symlink: bool = True,
    ) -> list[str]:
        self.symlink_hop_cnt += 1

        if self.symlink_hop_cnt > MAX_SYMLINK_HOPS:
            raise MaxSymlinkHopsExceeded("Maximum recursion for symlinks exceeded.")

        prev_path = prev_path or []
        path_parts = path.split(PATH_DIVIDER, maxsplit=1)

        if len(path_parts) == 1:
            path_part = path_parts[0]
            path_rest = ""

        else:
            path_part, path_rest = path_parts

        full_path = (
            f"{PATH_DIVIDER}".join(prev_path + [path_part]) if path_part else path_part
        )
        path_descriptor_id = self._system_state.get_descriptor_id(full_path)

        if path_descriptor_id is not None:
            path_descriptor_blocks = self._system_state.get_descriptor_blocks(
                path_descriptor_id
            )
            path_descriptor = self._memory_proxy.get_descriptor(
                path_descriptor_id, path_descriptor_blocks
            )

            if isinstance(path_descriptor, SymlinkDescriptor) and resolve_symlink:
                symlink_content = path_descriptor.read_content(path_descriptor.size)
                symlink_path = self.resolve_path(symlink_content).fs_object_path.split(
                    PATH_DIVIDER
                )

                if path_rest:
                    return self._check_path_parts(
                        path_rest, symlink_path, resolve_symlink
                    )

                return symlink_path

            if path_rest:
                return (
                    self._check_path_parts(
                        path_rest, prev_path + [path_part], resolve_symlink
                    )
                    # + prev_path
                )

        return prev_path + [path_part]

    def _resolve_absolute_path(
        self,
        path: Optional[str] = None,
        to_dir: bool = False,
        resolve_symlink: bool = True,
    ) -> ResolvedPath:
        path_parts = self._check_path_parts(path, resolve_symlink=resolve_symlink)

        fs_object_name = path_parts[-1]
        directory_path = (
            f"{PATH_DIVIDER}".join(path_parts[:-1])
            if len(path_parts) > 1 and not to_dir
            else path
        )

        directory = self.get_directory_descriptor_by_path(directory_path)
        fs_object_path = f"{PATH_DIVIDER}".join(path_parts)

        return ResolvedPath(
            directory=directory,
            directory_path=directory_path,
            fs_object_name=fs_object_name,
            fs_object_path=fs_object_path,
        )

    def _resolve_relative_path(
        self,
        path: Optional[str] = None,
        to_dir: bool = False,
        resolve_symlink: bool = True,
    ) -> ResolvedPath:
        cwd = self._system_state.get_cwd()
        path = cwd + PATH_DIVIDER + path

        return self._resolve_absolute_path(path, to_dir, resolve_symlink)

    def resolve_path(
        self,
        origin_path: Optional[str] = None,
        to_dir: bool = False,
        resolve_symlink: bool = True,
    ) -> ResolvedPath:
        self_point_paths = {ROOT_DIRECTORY_PATH, ".", ".."}
        cwd = self._system_state.get_cwd()

        path = origin_path or cwd
        path = cwd if path in self_point_paths else path

        if origin_path in self_point_paths:
            resolver_path = self._resolve_absolute_path(path, to_dir, resolve_symlink)
            resolver_path.fs_object_path = resolver_path.directory_path
            return resolver_path

        elif path.startswith(PATH_DIVIDER) or path in self_point_paths:
            return self._resolve_absolute_path(path, to_dir, resolve_symlink)

        return self._resolve_relative_path(path, to_dir, resolve_symlink)

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
