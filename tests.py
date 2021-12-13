import unittest.mock as mock
from unittest import TestCase

from constants import (
    BLOCK_HEADER_SIZE_BYTES,
    BLOCK_SIZE_BYTES,
    N_BLOCKS_MAX,
    N_DESCRIPTORS,
)
from fs.commands.create import CreateCommand
from fs.commands.link import LinkCommand
from fs.commands.mkfs import MkfsCommand
from fs.commands.mount import MountCommand
from fs.commands.open import OpenCommand
from fs.commands.umount import UmountCommand
from fs.commands.unlink import UnlinkCommand
from fs.driver.utils import form_header_from_bytes
from fs.exceptions import FSNotMounted
from fs.models.descriptor.file import FileDescriptor


class FSInitializationTests(TestCase):
    def setUp(self) -> None:
        try:
            UmountCommand().exec()
        except FSNotMounted:
            # For test cases correct work.
            pass

    def test_mount(self) -> None:
        command = MountCommand()
        command.exec()
        self.assertTrue(command._memory_proxy._memory_path.exists())

    def test_umount(self) -> None:
        MountCommand().exec()

        command = UmountCommand()
        command.exec()

        self.assertFalse(command._memory_proxy._memory_path.exists())

    def test_mkfs_n_descriptors(self) -> None:
        MountCommand().exec()

        command = MkfsCommand(n=N_DESCRIPTORS)
        command.exec()

        with command._memory_proxy.memory as m:
            self.assertEqual(len(m.read()), BLOCK_SIZE_BYTES * N_BLOCKS_MAX)


class FSWorkTests(TestCase):
    def setUp(self) -> None:
        try:
            UmountCommand().exec()
        except FSNotMounted:
            # For test cases correct work.
            pass

        MountCommand().exec()
        MkfsCommand(n=N_DESCRIPTORS).exec()

    def test_create_file(self) -> None:
        filename = "file1"
        command = CreateCommand(name=filename)
        command.exec()

        self.assertTrue(
            filename in command._system_data.get_name_to_descriptor_mapping()
        )

        file_descriptor = command._system_data.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_data.get_descriptor_blocks(
            file_descriptor
        )

        file = command._memory_proxy.get_descriptor(
            file_descriptor, file_descriptor_blocks
        )
        self.assertIsInstance(file, FileDescriptor)

    def test_create_n_files(self) -> None:
        for i in range(5):
            filename = f"file_{i}"
            command = CreateCommand(name=filename)
            command.exec()

            file_descriptor = command._system_data.get_descriptor_id(filename)
            file_descriptor_blocks = command._system_data.get_descriptor_blocks(
                file_descriptor
            )

            file = command._memory_proxy.get_descriptor(
                file_descriptor, file_descriptor_blocks
            )
            self.assertIsInstance(file, FileDescriptor)

    def test_link_file(self) -> None:
        filename = "file1"
        CreateCommand(name=filename).exec()

        link_filename = "file1_link"
        command = LinkCommand(name1=filename, name2=link_filename)
        command.exec()

        file_descriptor = command._system_data.get_descriptor_id(filename)
        file_link_descriptor = command._system_data.get_descriptor_id(link_filename)

        self.assertEqual(file_descriptor, file_link_descriptor)

        file_descriptor_blocks = command._system_data.get_descriptor_blocks(
            file_descriptor
        )

        file = command._memory_proxy.get_descriptor(
            file_descriptor, file_descriptor_blocks
        )
        self.assertEqual(file.refs_count, 2)

    def test_unlink_file(self) -> None:
        filename = "file1"
        CreateCommand(name=filename).exec()

        link_filename = "file1_link"
        LinkCommand(name1=filename, name2=link_filename).exec()

        command = UnlinkCommand(name=link_filename)
        command.exec()

        self.assertTrue(
            link_filename not in command._system_data.get_name_to_descriptor_mapping()
        )

        file_descriptor = command._system_data.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_data.get_descriptor_blocks(
            file_descriptor
        )

        file = command._memory_proxy.get_descriptor(
            file_descriptor, file_descriptor_blocks
        )
        self.assertEqual(file.refs_count, 1)

    def test_delete_file(self) -> None:
        filename = "file1"
        CreateCommand(name=filename).exec()

        command = UnlinkCommand(name=filename)

        file_descriptor = command._system_data.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_data.get_descriptor_blocks(
            file_descriptor
        )

        command.exec()

        file = command._memory_proxy.get_descriptor(
            file_descriptor, file_descriptor_blocks
        )

        self.assertEqual(file.refs_count, 0)

        with command._memory_proxy.memory as m:
            for block in file.blocks:
                m.seek(block.n * BLOCK_SIZE_BYTES)
                header_bytes = m.read(BLOCK_HEADER_SIZE_BYTES)

                header = form_header_from_bytes(header_bytes)

                self.assertFalse(header.used)
                self.assertEqual(header.ref_count, 0)

    def test_open_file(self) -> None:
        filename = "file1"
        CreateCommand(name=filename).exec()

        command = OpenCommand(name=filename)

        test_fd = 1000

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            command.exec()

        self.assertTrue(str(test_fd) in command._system_data.get_fd_to_name_mapping())

        file_descriptor = command._system_data.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_data.get_descriptor_blocks(
            file_descriptor
        )

        file = command._memory_proxy.get_descriptor(
            file_descriptor, file_descriptor_blocks
        )
        self.assertIsInstance(file, FileDescriptor)
        self.assertTrue(file.opened)
