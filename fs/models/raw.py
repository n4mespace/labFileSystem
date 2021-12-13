from dataclasses import dataclass

from constants import BLOCK_CONTENT_SIZE_BYTES


@dataclass
class BlockHeader:
    used: bool = False
    directory: bool = False
    ref_count: int = 0
    size: int = 0
    opened: bool = False


@dataclass
class BlockContent:
    header: BlockHeader
    content: bytearray = bytearray(BLOCK_CONTENT_SIZE_BYTES)
