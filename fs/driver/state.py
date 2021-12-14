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
        self._config: Optional[State] = None

    @property
    @contextlib.contextmanager
    def config(self) -> Generator[State, Any, Any]:
        if not self._config:
            self._config = self._read_config()

        try:
            yield self._config
        finally:
            self._write_config()

    def _read_config(self) -> State:
        if self._config_path.exists():
            with open(self._config_path) as f:
                raw_data = json.load(f)
                raw_data["descriptors"] = [
                    DescriptorState(**data) for data in raw_data["descriptors"]
                ]

                return State(**raw_data)

        return State()

    def _write_config(self) -> None:
        with open(self._config_path, "w") as f:
            json.dump(asdict(self._config), f, indent=2)

    def init_descriptors(self, n: int) -> None:
        with self.config as c:
            c.descriptors = [DescriptorState(i) for i in range(n)]

    def clear_config_file(self) -> None:
        with self.config:
            self._config = State()

    def set_mounted(self, mounted: bool) -> None:
        with self.config as c:
            c.mounted = mounted

    def check_mounted(self) -> bool:
        with self.config as c:
            return c.mounted

    def check_name_exists(self, name: str) -> bool:
        with self.config as c:
            return name in c.name_to_descriptor

    def get_name_to_descriptor_mapping(self) -> dict[str, int]:
        with self.config as c:
            return c.name_to_descriptor

    def get_fd_to_name_mapping(self) -> dict[str, str]:
        with self.config as c:
            return c.fd_to_name

    def get_used_blocks(self) -> list[int]:
        with self.config as c:
            return [
                block for descriptor in c.descriptors for block in descriptor.blocks
            ]

    def add_block_to_descriptor(self, descriptor_id: int, block_n: int) -> None:
        with self.config as c:
            c.descriptors[descriptor_id].blocks.append(block_n)

    def remove(self, descriptor: Descriptor, name: str) -> None:
        self.unmap_name_from_descriptor(name)
        self.unmap_descriptor_from_blocks(descriptor.n)
        self.set_descriptor_unused(descriptor.n)

    def write(self, descriptor: Descriptor, name: str) -> None:
        self.map_name_to_descriptor(name, descriptor.n)
        self.map_descriptor_to_blocks(
            descriptor.n, [block.n for block in descriptor.blocks]
        )
        self.set_descriptor_used(descriptor.n)

    def map_descriptor_to_blocks(self, descriptor_id: int, blocks: list[int]) -> None:
        with self.config as c:
            c.descriptors[descriptor_id].blocks = blocks

    def map_name_to_descriptor(self, name: str, descriptor_id: int) -> None:
        with self.config as c:
            c.name_to_descriptor[name] = descriptor_id

    def unmap_descriptor_from_blocks(self, descriptor_id: int) -> None:
        with self.config as c:
            c.descriptors[descriptor_id].blocks = []
            c.descriptors[descriptor_id].used = False

    def unmap_name_from_descriptor(self, name: str) -> None:
        with self.config as c:
            c.name_to_descriptor.pop(name)

    def _set_descriptor_use(self, n: int, used: bool) -> None:
        with self.config as c:
            c.descriptors[n].used = used

    def set_descriptor_used(self, n: int) -> None:
        self._set_descriptor_use(n, used=True)

    def set_descriptor_unused(self, n: int) -> None:
        self._set_descriptor_use(n, used=False)

    def check_for_descriptor(self, descriptor_id: int) -> bool:
        with self.config as c:
            return c.descriptors[descriptor_id].used

    def get_new_descriptor_id(self) -> int:
        with self.config as c:
            available_descriptors = [
                descriptor for descriptor in c.descriptors if not descriptor.used
            ]

        try:
            descriptor = available_descriptors[0]
        except IndexError:
            raise OutOfDescriptors("System run out of available descriptors")
        else:
            return descriptor.n

    def get_descriptor_blocks(self, descriptor_id: int) -> list[int]:
        with self.config as c:
            return c.descriptors[descriptor_id].blocks

    def get_descriptor_id(self, name: str) -> Optional[int]:
        with self.config as c:
            return c.name_to_descriptor.get(name)

    def get_descriptor_name(self, fd: str) -> Optional[str]:
        with self.config as c:
            return c.fd_to_name.get(fd)

    def map_file_to_fd(self, name: str) -> str:
        fd = str(random.randint(*FD_GENERATION_RANGE))

        with self.config as c:
            c.fd_to_name[fd] = name

        return fd

    def unmap_fd_from_name(self, fd: str) -> None:
        with self.config as c:
            c.fd_to_name.pop(fd)

    def check_system_formatted(self) -> bool:
        with self.config as c:
            return bool(c.descriptors)
