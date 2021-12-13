from dataclasses import dataclass

from constants import DIRECTORY_MAPPING_BYTES
from fs.models.descriptor.base import Descriptor, FSObject


@dataclass
class DirectoryDescriptor(Descriptor):
    def write_link(self, name: str, descriptor_id: int) -> None:
        for block in self.blocks:
            if not any(block.content[-DIRECTORY_MAPPING_BYTES:]):
                block.write_link(name, descriptor_id)
                break
        else:
            self.add_block()
            self.blocks[-1].write_link(name, descriptor_id)

    def get_directory_links(self) -> dict:
        links = {}

        for block in self.blocks:
            links.update(block.get_links())

        return links

    def remove_directory_link(self, name: str) -> None:
        for block in self.blocks:
            block.remove_link(name)


@dataclass
class Directory(FSObject):
    descriptor: DirectoryDescriptor
    parent: DirectoryDescriptor
