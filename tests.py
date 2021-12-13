from unittest import TestCase

from constants import (
    BLOCK_SIZE_BYTES,
    N_BLOCKS_MAX,
    N_DESCRIPTORS,
    BLOCK_HEADER_SIZE_BYTES,
)
from fs.exceptions import FSNotMounted
from fs.service import FsCommandHandlerService
from fs.types import FileDescriptor


class FSTests(TestCase):
    def setUp(self) -> None:
        self.fs_handler = FsCommandHandlerService()

        try:
            self.fs_handler.umount()
        except FSNotMounted:
            # For test cases correct work.
            pass

    def test_mount(self) -> None:
        self.fs_handler.mount()
        self.assertTrue(self.fs_handler._memory_proxy._memory_path.exists())

    def test_umount(self) -> None:
        self.fs_handler.mount()
        self.fs_handler.umount()
        self.assertFalse(self.fs_handler._memory_proxy._memory_path.exists())

    def test_mkfs_n_descriptors(self) -> None:
        n_descriptors = 10

        self.fs_handler.mount()
        self.fs_handler.mkfs(n_descriptors)

        with self.fs_handler._memory_proxy as fs:
            self.assertEqual(len(fs.memory.read()), BLOCK_SIZE_BYTES * N_BLOCKS_MAX)

    def test_create_file(self) -> None:
        self.fs_handler.mount()
        self.fs_handler.mkfs(N_DESCRIPTORS)

        self.fs_handler.create("file1")

        self.assertTrue(
            "file1" in self.fs_handler._system_data.config.name_to_descriptor
        )

        file_descriptor = self.fs_handler._system_data.config.name_to_descriptor[
            "file1"
        ]
        file_descriptor_blocks = self.fs_handler._system_data.config.descriptors[file_descriptor].blocks

        with self.fs_handler._memory_proxy as fs:
            file = fs.get_descriptor(file_descriptor, file_descriptor_blocks)
            self.assertIsInstance(file, FileDescriptor)

    def test_link_file(self) -> None:
        self.fs_handler.mount()
        self.fs_handler.mkfs(N_DESCRIPTORS)

        self.fs_handler.create("file1")
        self.fs_handler.link("file1", "file1_link")

        file_descriptor = self.fs_handler._system_data.config.name_to_descriptor[
            "file1"
        ]
        file_link_descriptor = self.fs_handler._system_data.config.name_to_descriptor[
            "file1_link"
        ]

        self.assertEqual(file_descriptor, file_link_descriptor)

        file_descriptor_blocks = self.fs_handler._system_data.config.descriptors[file_descriptor].blocks

        with self.fs_handler._memory_proxy as fs:
            file = fs.get_descriptor(file_descriptor, file_descriptor_blocks)
            self.assertEqual(file.refs_count, 2)

    def test_unlink_file(self) -> None:
        self.fs_handler.mount()
        self.fs_handler.mkfs(N_DESCRIPTORS)

        self.fs_handler.create("file1")
        self.fs_handler.link("file1", "file1_link")

        self.fs_handler.unlink("file1_link")
        self.assertTrue(
            "file1_link" not in self.fs_handler._system_data.config.name_to_descriptor
        )

        file_descriptor = self.fs_handler._system_data.config.name_to_descriptor[
            "file1"
        ]
        file_descriptor_blocks = self.fs_handler._system_data.config.descriptors[file_descriptor].blocks

        with self.fs_handler._memory_proxy as fs:
            file = fs.get_descriptor(file_descriptor, file_descriptor_blocks)
            self.assertEqual(file.refs_count, 1)

    def test_delete_file(self) -> None:
        self.fs_handler.mount()
        self.fs_handler.mkfs(N_DESCRIPTORS)

        self.fs_handler.create("file1")

        file_descriptor = self.fs_handler._system_data.config.name_to_descriptor[
            "file1"
        ]

        self.fs_handler.unlink("file1")

        file_descriptor_blocks = self.fs_handler._system_data.config.descriptors[file_descriptor].blocks

        with self.fs_handler._memory_proxy as fs:
            file = fs.get_descriptor(file_descriptor, file_descriptor_blocks)
            self.assertEqual(file.refs_count, 0)

            for block in file.blocks:
                fs.memory.seek(block.n * BLOCK_SIZE_BYTES)
                header_bytes = fs.memory.read(BLOCK_HEADER_SIZE_BYTES)
                header = fs._form_header_from_bytes(header_bytes)

                self.assertFalse(header.used)
                self.assertEqual(header.ref_count, 0)
