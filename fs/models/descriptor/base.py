from dataclasses import dataclass

from constants import BLOCK_CONTENT_SIZE_BYTES
from fs.models.block import Block


@dataclass
class Descriptor:
    n: int
    refs_count: int
    size: int
    opened: bool
    blocks: list[Block]

    def add_block(self) -> None:
        from fs.driver.memory import MemoryStorageProxy
        from fs.driver.state import SystemState

        block_n = MemoryStorageProxy().get_available_block_n()
        SystemState().add_block_to_descriptor(descriptor_id=self.n, block_n=block_n)

        self.blocks.append(Block(n=block_n))

    def truncate(self, size: int) -> list[Block]:
        size_diff = self.size - size
        blocks_to_change, block_offset = divmod(size, BLOCK_CONTENT_SIZE_BYTES)
        blocks_deleted = []

        empty_content = "\x00" * (BLOCK_CONTENT_SIZE_BYTES - block_offset)

        if size_diff < 0:
            for _ in range(-blocks_to_change):
                self.add_block()

        elif size_diff > 0:
            for _ in range(blocks_to_change + 1):
                if len(self.blocks) > 1:
                    blocks_deleted.append(self.blocks.pop(-1))
                break

            self.blocks[-1].write_content(empty_content, offset=block_offset)

        return blocks_deleted

    def update_size(self) -> None:
        self.size = 0

        for block in self.blocks:
            self.size += sum(map(bool, block.content))


@dataclass
class FSObject:
    name: str
    descriptor: Descriptor
