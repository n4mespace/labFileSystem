from dataclasses import dataclass

from fs.models.block import Block


@dataclass
class Descriptor:
    n: int
    refs_count: int
    size: int
    opened: bool
    blocks: list[Block]

    def add_block(self) -> None:
        from fs.driver.config import SystemConfig
        from fs.driver.memory import MemoryStorageProxy

        block_n = MemoryStorageProxy().get_available_block_n()
        SystemConfig().add_block_to_descriptor(descriptor_id=self.n, block_n=block_n)

        self.blocks.append(Block(n=block_n))


@dataclass
class FSObject:
    name: str
    descriptor: Descriptor
