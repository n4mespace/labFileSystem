import contextlib
import json
import random
from dataclasses import asdict
from pathlib import Path
from typing import Optional, Any

from constants import CONFIG_PATH, FD_GENERATION_RANGE
from fs.exceptions import OutOfDescriptors
from fs.types import Config, DescriptorConfig, Descriptor


class SystemConfig:
    def __init__(self) -> None:
        self._config_path = Path(CONFIG_PATH)

        if self._config_path.exists():
            self._config = self._read_config()
        else:
            self._config = self._init_config()

    @contextlib.contextmanager
    @property
    def config(self) -> Config:
        resource = self._read_config()
        try:
            yield resource
        finally:
            self._write_config()

    def _read_config(self) -> Config:
        with open(self._config_path) as f:
            raw_data = json.load(f)
            raw_data["descriptors"] = [DescriptorConfig(**data) for data in raw_data["descriptors"]]

            return Config(**raw_data)

    @staticmethod
    def _init_config() -> Config:
        return Config()

    def _write_config(self) -> None:
        with open(self._config_path, "w") as f:
            json.dump(asdict(self._config), f, indent=2)

    def init_descriptors(self, n: int) -> None:
        self.config.descriptors = [DescriptorConfig(i) for i in range(n)]
        self._write_config()

    def set_mounted(self, mounted: bool) -> None:
        with self.config as c:
            c.mounted = True
        if not mounted:
            self.config = self._init_config()
        else:
            self.config.mounted = True

        self._write_config()

    def check_name_exists(self, name: str) -> bool:
        return name in self.config.name_to_descriptor

    def get_used_blocks(self) -> list[int]:
        return [
            block for descriptor
            in self.config.descriptors
            for block in descriptor.blocks
        ]

    def remove_descriptor_from_config(self, descriptor: Descriptor, name: str) -> None:
        self.unmap_name_from_descriptor(name)
        self.unmap_descriptor_from_blocks(descriptor.n)
        self.set_descriptor_unused(descriptor.n)

    def write_descriptor_to_config(self, descriptor: Descriptor, name: str) -> None:
        self.map_name_to_descriptor(name, descriptor.n)
        self.map_descriptor_to_blocks(descriptor.n, [block.n for block in descriptor.blocks])
        self.set_descriptor_used(descriptor.n)

    def map_descriptor_to_blocks(self, descriptor_id: int, blocks: list[int]) -> None:
        self.config.descriptors[descriptor_id].blocks = blocks
        self._write_config()

    def map_name_to_descriptor(self, name: str, descriptor_id: int) -> None:
        self.config.name_to_descriptor[name] = descriptor_id
        self._write_config()

    def unmap_descriptor_from_blocks(self, descriptor_id: int) -> None:
        self.config.descriptors[descriptor_id].blocks = []
        self.config.descriptors[descriptor_id].used = False
        self._write_config()

    def unmap_name_from_descriptor(self, name: str) -> None:
        self.config.name_to_descriptor.pop(name)
        self._write_config()

    def _set_descriptor_use(self, n: int, used: bool) -> None:
        self.config.descriptors[n].used = used
        self._write_config()

    def set_descriptor_used(self, n: int) -> None:
        self._set_descriptor_use(n, used=True)

    def set_descriptor_unused(self, n: int) -> None:
        self._set_descriptor_use(n, used=False)

    def check_for_descriptor(self, descriptor_id: int) -> bool:
        return self.config.descriptors[descriptor_id].used

    def get_new_descriptor_id(self) -> int:
        available_descriptors = [descriptor for descriptor in self.config.descriptors if not descriptor.used]

        try:
            descriptor = available_descriptors[0]
        except IndexError:
            raise OutOfDescriptors("System run out of available descriptors")
        else:
            return descriptor.n

    def get_descriptor_id(self, name: str) -> Optional[int]:
        return self.config.name_to_descriptor.get(name)

    def get_descriptor_name(self, fd: str) -> Optional[str]:
        return self.config.fd_to_name.get(fd)

    def map_file_to_fd(self, name: str) -> str:
        fd = str(random.randint(*FD_GENERATION_RANGE))
        self.config.fd_to_name[fd] = name

        self._write_config()
        return fd

    def unmap_fd_from_name(self, fd: str) -> None:
        self.config.fd_to_name.pop(fd)
        self._write_config()
