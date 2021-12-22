import contextlib
import json
import random
from collections.abc import Generator
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

from constants import CONFIG_PATH, FD_GENERATION_RANGE
from fs.driver.utils import DescriptorState, State
from fs.exceptions import OutOfDescriptors
from fs.models.descriptor.base import Descriptor


class SystemState:
    def __init__(self) -> None:
        self._config_path = Path(CONFIG_PATH)
        self._state: Optional[State] = None

    @property
    @contextlib.contextmanager
    def state(self) -> Generator[State, Any, Any]:
        if not self._state:
            self._state = self._read_state()

        try:
            yield self._state
        finally:
            self._write_state()

    def _read_state(self) -> State:
        if self._config_path.exists():
            with open(self._config_path) as f:
                raw_data = json.load(f)
                raw_data["descriptors"] = [
                    DescriptorState(**data) for data in raw_data["descriptors"]
                ]

                return State(**raw_data)

        return State()

    def _write_state(self) -> None:
        with open(self._config_path, "w") as f:
            json.dump(asdict(self._state), f, indent=2)

    def init_descriptors(self, n: int) -> None:
        with self.state as s:
            s.descriptors = [DescriptorState(i) for i in range(n)]

    def clear_config_file(self) -> None:
        with self.state:
            self._state = State()

    def set_mounted(self, mounted: bool) -> None:
        with self.state as s:
            s.mounted = mounted

    def check_mounted(self) -> bool:
        with self.state as s:
            return s.mounted

    def check_path_exists(self, path: str) -> bool:
        with self.state as s:
            return path in s.path_to_descriptor

    def get_path_to_descriptor_mapping(self) -> dict[str, int]:
        with self.state as s:
            return s.path_to_descriptor

    def get_fd_to_path_mapping(self) -> dict[str, str]:
        with self.state as s:
            return s.fd_to_path

    def add_block_to_descriptor(self, descriptor_id: int, block_n: int) -> None:
        with self.state as s:
            s.descriptors[descriptor_id].blocks.append(block_n)

    def remove(self, descriptor: Descriptor, path: str) -> None:
        self.unmap_path_from_descriptor(path)
        self.unmap_descriptor_from_blocks(descriptor.n)
        self.set_descriptor_unused(descriptor.n)

    def write(self, descriptor: Descriptor, path: str) -> None:
        self.map_path_to_descriptor(path, descriptor.n)
        self.map_descriptor_to_blocks(
            descriptor.n, [block.n for block in descriptor.blocks]
        )
        self.set_descriptor_used(descriptor.n)

    def map_descriptor_to_blocks(self, descriptor_id: int, blocks: list[int]) -> None:
        with self.state as s:
            s.descriptors[descriptor_id].blocks = blocks

    def map_path_to_descriptor(self, path: str, descriptor_id: int) -> None:
        with self.state as s:
            s.path_to_descriptor[path] = descriptor_id

    def unmap_descriptor_from_blocks(self, descriptor_id: int) -> None:
        with self.state as s:
            s.descriptors[descriptor_id].blocks = []
            s.descriptors[descriptor_id].used = False

    def unmap_path_from_descriptor(self, path: str) -> None:
        with self.state as s:
            s.path_to_descriptor.pop(path)

    def _set_descriptor_use(self, n: int, used: bool) -> None:
        with self.state as s:
            s.descriptors[n].used = used

    def set_descriptor_used(self, n: int) -> None:
        self._set_descriptor_use(n, used=True)

    def set_descriptor_unused(self, n: int) -> None:
        self._set_descriptor_use(n, used=False)

    def check_for_descriptor(self, descriptor_id: int) -> bool:
        with self.state as s:
            return s.descriptors[descriptor_id].used

    def get_new_descriptor_id(self) -> int:
        with self.state as s:
            available_descriptors = [
                descriptor for descriptor in s.descriptors if not descriptor.used
            ]

        try:
            descriptor = available_descriptors[0]
        except IndexError:
            raise OutOfDescriptors("System run out of available descriptors")
        else:
            return descriptor.n

    def get_descriptor_blocks(self, descriptor_id: int) -> list[int]:
        with self.state as s:
            return s.descriptors[descriptor_id].blocks

    def get_descriptor_id(self, path: str) -> Optional[int]:
        with self.state as s:
            return s.path_to_descriptor.get(path)

    def get_descriptor_path(self, fd: str) -> Optional[str]:
        with self.state as s:
            return s.fd_to_path.get(fd)

    def map_filepath_to_fd(self, filepath: str) -> str:
        fd = str(random.randint(*FD_GENERATION_RANGE))

        with self.state as s:
            s.fd_to_path[fd] = filepath

        return fd

    def unmap_fd_from_path(self, fd: str) -> None:
        with self.state as s:
            s.fd_to_path.pop(fd)

    def check_system_formatted(self) -> bool:
        with self.state as s:
            return bool(s.descriptors)

    def get_cwd_name(self) -> str:
        with self.state as s:
            return s.cwd
