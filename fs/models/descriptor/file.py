from dataclasses import dataclass

from constants import BLOCK_CONTENT_SIZE_BYTES
from fs.models.descriptor.base import Descriptor, FSObject
from fs.models.descriptor.directory import DirectoryDescriptor


@dataclass
class FileDescriptor(Descriptor):
    def write_content(
        self, content: str, offset: int = 0, skip_blocks: int = 0
    ) -> None:
        from_block, offset = divmod(offset, BLOCK_CONTENT_SIZE_BYTES)

        for block in self.blocks[from_block + skip_blocks :]:
            can_write = BLOCK_CONTENT_SIZE_BYTES - offset

            content_chunk, content = content[:can_write], content[can_write:]
            block.write_content(content_chunk, offset)

            # If all the data was written
            if not content:
                break

            offset = 0

        else:
            self.add_block()
            self.write_content(
                content, offset, skip_blocks=skip_blocks + from_block + 1
            )

    def read_content(self, size: int, offset: int = 0) -> str:
        from_block = offset // BLOCK_CONTENT_SIZE_BYTES
        blocks_to_read = (offset + size) // BLOCK_CONTENT_SIZE_BYTES

        content = [
            b
            for block in self.blocks[from_block : blocks_to_read + 1]
            for b in block.content
        ]
        content = content[offset : offset + size]
        content = [chr(int(str(ch))) if ch else " " for ch in content]

        return "".join(content)


@dataclass
class File(FSObject):
    descriptor: FileDescriptor
    directory: DirectoryDescriptor
