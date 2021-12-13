from dataclasses import dataclass

from constants import BLOCK_CONTENT_SIZE_BYTES
from fs.models.descriptor.base import Descriptor, FSObject
from fs.models.descriptor.directory import DirectoryDescriptor


@dataclass
class FileDescriptor(Descriptor):
    def write_content(self, content: str, offset: int = 0) -> None:
        from_block, offset = divmod(offset, BLOCK_CONTENT_SIZE_BYTES)

        for block in self.blocks[from_block:]:
            can_write = BLOCK_CONTENT_SIZE_BYTES - offset

            content_chunk, content = content[:can_write], content[can_write:]
            block.write_content(content_chunk, offset)

            # If all the data was written
            if not content:
                break
        else:
            self.add_block()
            self.blocks[-1].write_content(content)

    def read_content(self, size: int, offset: int = 0) -> str:
        from_block, offset = divmod(offset, BLOCK_CONTENT_SIZE_BYTES)

        content = []

        for block in self.blocks[from_block:]:
            from_b, size = divmod(size, BLOCK_CONTENT_SIZE_BYTES - offset)

            content_chunk = block.content[from_b:size]
            content.extend(chr(int(str(ch))) if ch else " " for ch in content_chunk)

            size -= len(content_chunk)

            # If we read all we need.
            if not size:
                break

            offset = 0

        return "".join(content)


@dataclass
class File(FSObject):
    descriptor: FileDescriptor
    directory: DirectoryDescriptor
