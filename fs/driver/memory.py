import logging
from pathlib import Path
from typing import Any, BinaryIO, Optional

from constants import (BLOCK_CONTENT_SIZE_BYTES, BLOCK_HEADER_SIZE_BYTES,
                       BLOCK_SIZE_BYTES, MEMORY_PATH, N_BLOCKS_MAX)
from fs.exceptions import FSAlreadyMounted, FSNotMounted, OutOfBlocks
from fs.types import (Block, BlockContent, BlockHeader, BlockHeaderBytes,
                      Descriptor, Directory, DirectoryDescriptor, File,
                      FileDescriptor)


class MemoryStorageProxy:
    def __init__(self) -> None:
        self._memory_path = Path(MEMORY_PATH)
        self._memory: Optional[BinaryIO] = None

        self._logger = logging.getLogger(__name__)

    def __enter__(self) -> 'MemoryStorageProxy':
        self._memory = open(self._memory_path, "r+b")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._memory.close()

    @property
    def memory(self) -> BinaryIO:
        if not self._memory:
            raise AttributeError("Can't access memory resource. Use Proxy class as context manager.")

        return self._memory

    def clear(self) -> None:
        self.memory.truncate(0)

    def create_memory_file(self) -> None:
        if self._memory_path.exists():
            raise FSAlreadyMounted("Can't mount new FS till current is unmounted.")

        with open(self._memory_path, "wb"):
            self._logger.info(f"FS successfully mounted at `{MEMORY_PATH}`.")

    def delete_memory_file(self) -> None:
        if not self._memory_path.exists():
            raise FSNotMounted("Can't unmount new FS till one is not mounted.")

        self._memory_path.unlink()
        self._logger.info(f"FS successfully unmounted.")

    def write(self, descriptor: Descriptor) -> None:
        directory = isinstance(descriptor, DirectoryDescriptor)

        for block in descriptor.blocks:
            self.memory.seek(block.n * BLOCK_SIZE_BYTES)

            self.write_block(
                BlockContent(
                    header=BlockHeader(
                        used=True,
                        directory=directory,
                        ref_count=1,
                        size=sum(map(bool, block.content)),
                        opened=descriptor.opened,
                    ),
                    content=block.content,
                )
            )

    def write_empty_blocks(self, n: int) -> None:
        for _ in range(n):
            self.write_block(
                BlockContent(
                    header=BlockHeader(
                        used=False,
                        directory=False,
                        ref_count=0,
                        size=0,
                        opened=False,
                    ),
                )
            )

    def write_block(self, block: BlockContent) -> None:
        header_bytes = self._form_header_bytes(block.header)
        self.memory.write(header_bytes + block.content)

    @staticmethod
    def _form_header_bytes(header: BlockHeader) -> bytearray:
        header_bytes: bytearray = bytearray(BLOCK_HEADER_SIZE_BYTES)

        header_bytes[BlockHeaderBytes.DIRECTORY] = header.directory
        header_bytes[BlockHeaderBytes.USED] = header.used
        header_bytes[BlockHeaderBytes.REF_COUNT] = header.ref_count
        header_bytes[BlockHeaderBytes.SIZE] = header.size
        header_bytes[BlockHeaderBytes.OPENED] = header.opened

        return header_bytes

    @staticmethod
    def _form_header_from_bytes(header_bytes: bytes) -> BlockHeader:
        header = BlockHeader()

        header.directory = header_bytes[BlockHeaderBytes.DIRECTORY]
        header.used = header_bytes[BlockHeaderBytes.USED]
        header.ref_count = header_bytes[BlockHeaderBytes.REF_COUNT]
        header.size = header_bytes[BlockHeaderBytes.SIZE]
        header.opened = header_bytes[BlockHeaderBytes.OPENED]

        return header

    @staticmethod
    def get_available_block(used_blocks: list[int]) -> int:
        available_blocks = [n for n in range(N_BLOCKS_MAX) if n not in used_blocks]

        try:
            return available_blocks[0]
        except IndexError:
            raise OutOfBlocks("System run out of available blocks")

    def add_ref_count(self, descriptor: Descriptor, c: int) -> int:
        total_ref_count = 0

        for block in descriptor.blocks:
            self.memory.seek(block.n * BLOCK_SIZE_BYTES)

            header_bytes = self.memory.read(BLOCK_HEADER_SIZE_BYTES)
            header = self._form_header_from_bytes(header_bytes)
            header.ref_count += c

            total_ref_count += header.ref_count

            if not header.ref_count:
                # Then deleting a block.
                header.used = False

            self.memory.seek(block.n * BLOCK_SIZE_BYTES)
            self.memory.write(self._form_header_bytes(header))

        return total_ref_count

    def read_block(self, block_n: int) -> tuple[BlockHeader, Block]:
        self.memory.seek(block_n * BLOCK_SIZE_BYTES)

        header_bytes = self.memory.read(BLOCK_HEADER_SIZE_BYTES)
        content_bytes = self.memory.read(BLOCK_CONTENT_SIZE_BYTES)

        header = self._form_header_from_bytes(header_bytes)

        return header, Block(n=block_n, content=bytearray(content_bytes))

    def get_descriptor(self, n: int, blocks: list[int]) -> Descriptor:
        descriptor_blocks = [self.read_block(block_n) for block_n in blocks]

        blocks_headers = [block[0] for block in descriptor_blocks]
        blocks_data = [block[1] for block in descriptor_blocks]

        descriptor_size = sum(block_header.size for block_header in blocks_headers)
        descriptor_header = blocks_headers[0]

        descriptor_params = dict(
            n=n,
            size=descriptor_size,
            opened=False,
            refs_count=descriptor_header.ref_count,
            blocks=blocks_data,
        )

        if descriptor_header.directory:
            return DirectoryDescriptor(**descriptor_params)

        return FileDescriptor(**descriptor_params)

    def create_directory(self, n: int, block_n: int, name: str, parent: DirectoryDescriptor,
                         opened: bool = False, root: bool = False) -> Directory:
        descriptor = DirectoryDescriptor(
            n=n,
            size=0,
            refs_count=1,
            opened=opened,
            blocks=[Block(n=block_n)],
        )
        descriptor.write_link(name=".", descriptor_id=n)
        descriptor.write_link(name="..", descriptor_id=n if root else parent.n)

        descriptor.size += 3

        self._logger.info(f"Created directory descriptor [{n}].")

        return Directory(name, descriptor, parent)

    def create_file(self, n: int, block_n: int, name: str, directory_descriptor: DirectoryDescriptor) -> File:
        descriptor = FileDescriptor(
            n=n,
            size=0,
            refs_count=1,
            opened=False,
            blocks=[Block(n=block_n)],
        )
        directory_descriptor.write_link(name, n)

        self._logger.info(f"Created file descriptor [{n}].")

        return File(descriptor=descriptor, name=name, directory=directory_descriptor)
