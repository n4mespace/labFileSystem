import contextlib
import logging
from pathlib import Path
from typing import Any, BinaryIO, Generator, Optional

from constants import (BLOCK_CONTENT_SIZE_BYTES, BLOCK_HEADER_SIZE_BYTES,
                       BLOCK_SIZE_BYTES, MEMORY_PATH, N_BLOCKS_MAX,
                       ROOT_BLOCK_N)
from fs.driver.utils import form_header_bytes, form_header_from_bytes
from fs.exceptions import (BlockWriteDenied, FSAlreadyMounted, FSNotMounted,
                           OutOfBlocks, WrongDescriptorClass)
from fs.models.block import Block
from fs.models.descriptor.base import Descriptor
from fs.models.descriptor.directory import Directory, DirectoryDescriptor
from fs.models.descriptor.file import File, FileDescriptor
from fs.models.descriptor.symlink import Symlink, SymlinkDescriptor
from fs.models.raw import BlockContent, BlockHeader


class MemoryStorageProxy:
    def __init__(self) -> None:
        self._memory_path = Path(MEMORY_PATH)
        self._memory: Optional[BinaryIO] = None

        self._logger = logging.getLogger(__name__)

    @property
    @contextlib.contextmanager
    def memory(self) -> Generator[BinaryIO, Any, Any]:
        self._memory = open(self._memory_path, "r+b")

        try:
            yield self._memory
        finally:
            self._memory.close()

    def clear(self) -> None:
        with self.memory as m:
            m.truncate(0)

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
        symlink = isinstance(descriptor, SymlinkDescriptor)

        with self.memory as m:
            for block in descriptor.blocks:
                m.seek(block.n * BLOCK_SIZE_BYTES)

                self.write_block(
                    BlockContent(
                        header=BlockHeader(
                            used=True,
                            directory=directory,
                            symlink=symlink,
                            ref_count=1,
                            size=sum(map(bool, block.content)),
                            opened=descriptor.opened,
                        ),
                        content=block.content,
                    )
                )

    def write_empty_blocks(self, n: int, start_from: int = 0) -> None:
        with self.memory as m:
            for i in range(start_from, n):
                m.seek(i * BLOCK_SIZE_BYTES)

                self.write_block(
                    BlockContent(
                        header=BlockHeader(
                            used=False,
                            directory=False,
                            ref_count=0,
                            size=0,
                            opened=False,
                            symlink=False,
                        ),
                    )
                )

    def write_block(self, block: BlockContent) -> None:
        header_bytes = form_header_bytes(block.header)

        if not self._memory:
            raise BlockWriteDenied("Something went wrong writing a block to memory.")

        self._memory.write(header_bytes + block.content)

    def add_ref_count(self, descriptor: Descriptor, c: int) -> int:
        total_ref_count = 0

        with self.memory as m:
            for block in descriptor.blocks:
                m.seek(block.n * BLOCK_SIZE_BYTES)

                header_bytes = m.read(BLOCK_HEADER_SIZE_BYTES)
                header = form_header_from_bytes(header_bytes)
                header.ref_count += c

                total_ref_count += header.ref_count

                if not header.ref_count:
                    # Then deleting a block.
                    header.used = False

                m.seek(block.n * BLOCK_SIZE_BYTES)
                m.write(form_header_bytes(header))

        return total_ref_count

    def get_available_block_n(self) -> int:
        for block_n in range(N_BLOCKS_MAX):
            block_header, _ = self.read_block(block_n)

            if not block_header.used:
                block_header.used = True

                with self.memory as m:
                    # Prevent collision when demand multiple new blocks.
                    m.seek(block_n * BLOCK_SIZE_BYTES)
                    m.write(form_header_bytes(block_header))

                return block_n

        raise OutOfBlocks("System run out of available blocks")

    def read_block(self, block_n: int) -> tuple[BlockHeader, Block]:
        with self.memory as m:
            m.seek(block_n * BLOCK_SIZE_BYTES)

            header_bytes = m.read(BLOCK_HEADER_SIZE_BYTES)
            content_bytes = m.read(BLOCK_CONTENT_SIZE_BYTES)

        header = form_header_from_bytes(header_bytes)

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
            opened=descriptor_header.opened,
            refs_count=descriptor_header.ref_count,
            blocks=blocks_data,
        )

        if descriptor_header.directory:
            return DirectoryDescriptor(**descriptor_params)

        elif descriptor_header.symlink:
            return SymlinkDescriptor(**descriptor_params)

        return FileDescriptor(**descriptor_params)

    def get_directory_descriptor(self, n: int, blocks: list[int]) -> DirectoryDescriptor:
        descriptor = self.get_descriptor(n, blocks)

        if not isinstance(descriptor, DirectoryDescriptor):
            raise WrongDescriptorClass("Get wrong descriptor class.")

        return descriptor

    def get_file_descriptor(self, n: int, blocks: list[int]) -> FileDescriptor:
        descriptor = self.get_descriptor(n, blocks)

        if not isinstance(descriptor, FileDescriptor):
            raise WrongDescriptorClass("Get wrong descriptor class.")

        return descriptor

    def create_directory(self, n: int, name: str, parent: DirectoryDescriptor,
                         opened: bool = False, root: bool = False) -> Directory:

        block_n = ROOT_BLOCK_N if root else self.get_available_block_n()

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

        if not root:
            parent.write_link(name, n)
            parent.size += len(name)

        self._logger.info(f"Created directory descriptor [{n}].")

        return Directory(name, descriptor, parent)

    def create_file(self, n: int, name: str, directory_descriptor: DirectoryDescriptor) -> File:
        block_n = self.get_available_block_n()

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

    def create_symlink(self, n: int, name: str, directory_descriptor: DirectoryDescriptor, content: str) -> Symlink:
        block_n = self.get_available_block_n()

        descriptor = SymlinkDescriptor(
            n=n,
            size=0,
            refs_count=1,
            opened=False,
            blocks=[Block(n=block_n)],
        )

        descriptor.write_content(content)
        directory_descriptor.write_link(name, n)

        self._logger.info(f"Created symlink descriptor [{n}].")

        return Symlink(descriptor=descriptor, name=name, directory=directory_descriptor)
