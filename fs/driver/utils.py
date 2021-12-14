from dataclasses import dataclass, field

from constants import BLOCK_HEADER_SIZE_BYTES, ROOT_DIRECTORY_NAME
from fs.models.raw import BlockHeader
from fs.models.utils import BlockHeaderBytes


@dataclass
class DescriptorState:
    n: int
    used: bool = False
    blocks: list[int] = field(default_factory=list)


@dataclass
class State:
    descriptors: list[DescriptorState] = field(default_factory=list)
    name_to_descriptor: dict[str, int] = field(default_factory=dict)
    fd_to_name: dict[str, str] = field(default_factory=dict)
    cwd: str = ROOT_DIRECTORY_NAME
    mounted: bool = False


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

    header.directory = bool(header_bytes[BlockHeaderBytes.DIRECTORY])
    header.used = bool(header_bytes[BlockHeaderBytes.USED])
    header.ref_count = header_bytes[BlockHeaderBytes.REF_COUNT]
    header.size = header_bytes[BlockHeaderBytes.SIZE]
    header.opened = bool(header_bytes[BlockHeaderBytes.OPENED])

    return header
