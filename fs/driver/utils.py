from constants import (BLOCK_HEADER_SIZE_BYTES,
                       N_BLOCKS_MAX)
from fs.exceptions import OutOfBlocks
from fs.types import (BlockHeader)
from fs.types import (BlockHeaderBytes)


def form_header_bytes(header: BlockHeader) -> bytearray:
    header_bytes: bytearray = bytearray(BLOCK_HEADER_SIZE_BYTES)

    header_bytes[BlockHeaderBytes.DIRECTORY] = header.directory
    header_bytes[BlockHeaderBytes.USED] = header.used
    header_bytes[BlockHeaderBytes.REF_COUNT] = header.ref_count
    header_bytes[BlockHeaderBytes.SIZE] = header.size
    header_bytes[BlockHeaderBytes.OPENED] = header.opened

    return header_bytes


def form_header_from_bytes(header_bytes: bytes) -> BlockHeader:
    header = BlockHeader()

    header.directory = header_bytes[BlockHeaderBytes.DIRECTORY]
    header.used = header_bytes[BlockHeaderBytes.USED]
    header.ref_count = header_bytes[BlockHeaderBytes.REF_COUNT]
    header.size = header_bytes[BlockHeaderBytes.SIZE]
    header.opened = header_bytes[BlockHeaderBytes.OPENED]

    return header


def get_available_block(used_blocks: list[int]) -> int:
    available_blocks = set(range(N_BLOCKS_MAX)) - set(used_blocks)

    try:
        return list(available_blocks)[0]
    except IndexError:
        raise OutOfBlocks("System run out of available blocks")
