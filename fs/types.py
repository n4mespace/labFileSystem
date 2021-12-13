from dataclasses import dataclass, field, asdict
from enum import IntEnum

from constants import BLOCK_CONTENT_SIZE_BYTES, DIRECTORY_MAPPING_BYTES


@dataclass
class Block:
    n: int
    content: bytearray = field(
        default_factory=lambda: bytearray(BLOCK_CONTENT_SIZE_BYTES)
    )

    def write_link(self, name: str, descriptor_id: int) -> None:
        offset = 0

        for link_mapping_step in range(0, BLOCK_CONTENT_SIZE_BYTES - DIRECTORY_MAPPING_BYTES,
                                       DIRECTORY_MAPPING_BYTES):
            mapping_bytes = self.content[link_mapping_step: link_mapping_step + DIRECTORY_MAPPING_BYTES]

            if not any(mapping_bytes):
                offset = link_mapping_step
                break
        # TODO: What if not find offset?

        for i, ch in enumerate(name):
            self.content[offset + i] = ord(ch)

        self.content[offset + DIRECTORY_MAPPING_BYTES - 1] = descriptor_id

    def get_links(self) -> dict:
        links = {}

        for link_mapping_step in range(0, BLOCK_CONTENT_SIZE_BYTES - DIRECTORY_MAPPING_BYTES,
                                       DIRECTORY_MAPPING_BYTES):
            mapping_bytes = self.content[link_mapping_step: link_mapping_step + DIRECTORY_MAPPING_BYTES]

            # Run out of links.
            if not any(mapping_bytes):
                break

            descriptor_id = mapping_bytes[-1]
            name_bytes = mapping_bytes[:-1]
            name = "".join(chr(b) for b in name_bytes if b)

            links[name] = descriptor_id

        return links

    def remove_link(self, name: str) -> None:
        for link_mapping_step in range(0, BLOCK_CONTENT_SIZE_BYTES - DIRECTORY_MAPPING_BYTES,
                                       DIRECTORY_MAPPING_BYTES):
            mapping_bytes = self.content[link_mapping_step: link_mapping_step + DIRECTORY_MAPPING_BYTES]

            # Run out of links.
            if not any(mapping_bytes):
                break

            name_bytes = mapping_bytes[:-1]
            link_name = "".join(chr(b) for b in name_bytes if b)

            if name == link_name:
                for i in range(link_mapping_step, link_mapping_step + DIRECTORY_MAPPING_BYTES):
                    self.content[i] = 0

                break

    def __repr__(self):
        attrs_str = []

        for k, v in asdict(self).items():
            if k == "content":
                v = list(map(ord, self.content.decode("utf-8")))

            attrs_str.append(f"{k}={v}")

        return f"{type(self).__name__}({', '.join(attrs_str)})"


@dataclass
class Descriptor:
    n: int
    refs_count: int
    size: int
    opened: bool
    blocks: list[Block]


@dataclass
class FileDescriptor(Descriptor):
    ...


@dataclass
class DirectoryDescriptor(Descriptor):
    def write_link(self, name: str, descriptor_id: int) -> None:
        for block in self.blocks:
            if not any(block.content[-DIRECTORY_MAPPING_BYTES:]):
                block.write_link(name, descriptor_id)
                return

        # Add new block.

    def get_directory_links(self) -> dict:
        links = {}

        for block in self.blocks:
            links.update(block.get_links())

        return links

    def remove_directory_link(self, name: str) -> None:
        for block in self.blocks:
            block.remove_link(name)


@dataclass
class FSObject:
    name: str
    descriptor: Descriptor


@dataclass
class Directory(FSObject):
    descriptor: DirectoryDescriptor
    parent: DirectoryDescriptor


@dataclass
class File(FSObject):
    descriptor: FileDescriptor
    directory: DirectoryDescriptor


@dataclass
class DescriptorConfig:
    n: int
    used: bool = False
    blocks: list[int] = field(default_factory=list)


@dataclass
class Config:
    descriptors: list[DescriptorConfig] = field(default_factory=list)
    name_to_descriptor: dict[str, int] = field(default_factory=dict)
    fd_to_name: dict[str, str] = field(default_factory=dict)
    mounted: bool = False


@dataclass
class BlockHeader:
    used: bool = False
    directory: bool = False
    ref_count: int = 0
    size: int = 0
    opened: bool = False


class BlockHeaderBytes(IntEnum):
    DIRECTORY: int = 0
    USED: int = 1
    REF_COUNT: int = 2
    SIZE: int = 3
    OPENED: int = 4


@dataclass
class BlockContent:
    header: BlockHeader
    content: bytearray = bytearray(BLOCK_CONTENT_SIZE_BYTES)
