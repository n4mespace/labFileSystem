from enum import IntEnum


class BlockHeaderBytes(IntEnum):
    DIRECTORY: int = 0
    USED: int = 1
    REF_COUNT: int = 2
    SIZE: int = 3
    OPENED: int = 4
