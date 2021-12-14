import logging
from unittest import TestCase, mock

import pytest
from _pytest.logging import LogCaptureFixture

from constants import (BLOCK_HEADER_SIZE_BYTES, BLOCK_SIZE_BYTES, N_BLOCKS_MAX,
                       N_DESCRIPTORS)
from fs.commands.close import CloseCommand
from fs.commands.create import CreateCommand
from fs.commands.link import LinkCommand
from fs.commands.ls import LsCommand
from fs.commands.mkfs import MkfsCommand
from fs.commands.mount import MountCommand
from fs.commands.open import OpenCommand
from fs.commands.truncate import TruncateCommand
from fs.commands.umount import UmountCommand
from fs.commands.unlink import UnlinkCommand
from fs.commands.write import WriteCommand
from fs.driver.utils import form_header_from_bytes
from fs.exceptions import FSNotMounted
from fs.models.descriptor.file import FileDescriptor

lorem_ipsum = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, "
    "quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. "
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu "
    "fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa "
    "qui officia deserunt mollit anim id est laborum."
)


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

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog: LogCaptureFixture) -> None:
        self._caplog = caplog

    def test_create_file(self) -> None:
        filename = "file1"
        command = CreateCommand(name=filename)
        command.exec()

        self.assertTrue(
            filename in command._system_state.get_name_to_descriptor_mapping()
        )

        file_descriptor = command._system_state.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_state.get_descriptor_blocks(
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

            file_descriptor = command._system_state.get_descriptor_id(filename)
            file_descriptor_blocks = command._system_state.get_descriptor_blocks(
                file_descriptor
            )

            file = command._memory_proxy.get_descriptor(
                file_descriptor, file_descriptor_blocks
            )
            self.assertIsInstance(file, FileDescriptor)

    def test_ls_files(self) -> None:
        created_files = []

        for i in range(5):
            filename = f"file_{i}"

            CreateCommand(name=filename).exec()
            created_files.append(filename)

        command = LsCommand()

        with self._caplog.at_level(logging.INFO):
            command.exec()

            command_output = self._caplog.records[0].msg
            file_rows = [row for row in command_output.split("\n")[5:]]

        for i, file in enumerate(created_files):
            self.assertIn(file, file_rows[i])

    def test_link_file(self) -> None:
        filename = "file1"
        CreateCommand(name=filename).exec()

        link_filename = "file1_link"
        command = LinkCommand(name1=filename, name2=link_filename)
        command.exec()

        file_descriptor = command._system_state.get_descriptor_id(filename)
        file_link_descriptor = command._system_state.get_descriptor_id(link_filename)

        self.assertEqual(file_descriptor, file_link_descriptor)

        file_descriptor_blocks = command._system_state.get_descriptor_blocks(
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
            link_filename not in command._system_state.get_name_to_descriptor_mapping()
        )

        file_descriptor = command._system_state.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_state.get_descriptor_blocks(
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

        file_descriptor = command._system_state.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_state.get_descriptor_blocks(
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

        test_fd = 100

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            command.exec()

        self.assertTrue(str(test_fd) in command._system_state.get_fd_to_name_mapping())

        file_descriptor = command._system_state.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_state.get_descriptor_blocks(
            file_descriptor
        )

        file = command._memory_proxy.get_descriptor(
            file_descriptor, file_descriptor_blocks
        )
        self.assertIsInstance(file, FileDescriptor)
        self.assertTrue(file.opened)

    def test_close_file(self) -> None:
        filename = "file1"
        CreateCommand(name=filename).exec()

        test_fd = 100

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            OpenCommand(name=filename).exec()

        command = CloseCommand(fd=str(test_fd))
        command.exec()

        self.assertFalse(str(test_fd) in command._system_state.get_fd_to_name_mapping())

        file_descriptor = command._system_state.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_state.get_descriptor_blocks(
            file_descriptor
        )

        file = command._memory_proxy.get_descriptor(
            file_descriptor, file_descriptor_blocks
        )
        self.assertIsInstance(file, FileDescriptor)
        self.assertFalse(file.opened)

    def test_write_file(self) -> None:
        filename = "file1"
        CreateCommand(name=filename).exec()

        test_fd = 100

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            OpenCommand(name=filename).exec()

        test_content = "hello_world"

        command = WriteCommand(fd=str(test_fd), offset=0, content=test_content)
        command.exec()

        file_descriptor = command._system_state.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_state.get_descriptor_blocks(
            file_descriptor
        )

        file = command._memory_proxy.get_descriptor(
            file_descriptor, file_descriptor_blocks
        )
        self.assertIsInstance(file, FileDescriptor)
        self.assertEqual(file.size, len(test_content))

        content = file.read_content(len(test_content), offset=0)
        self.assertEqual(content, test_content)

    def test_write_large_data_to_file(self) -> None:
        filename = "file1"
        CreateCommand(name=filename).exec()

        test_fd = 100

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            OpenCommand(name=filename).exec()

        command = WriteCommand(fd=str(test_fd), offset=3, content=lorem_ipsum)
        command.exec()

        file_descriptor = command._system_state.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_state.get_descriptor_blocks(
            file_descriptor
        )

        file = command._memory_proxy.get_descriptor(
            file_descriptor, file_descriptor_blocks
        )
        self.assertEqual(file.size, len(lorem_ipsum))

        content = file.read_content(len(lorem_ipsum), offset=3)
        self.assertEqual(content, lorem_ipsum)

    def test_truncate_size_down_file(self) -> None:
        filename = "file1"
        CreateCommand(name=filename).exec()

        test_fd = 100

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            OpenCommand(name=filename).exec()

        WriteCommand(fd=str(test_fd), offset=0, content=lorem_ipsum).exec()

        test_truncate_size = len(lorem_ipsum) // 2

        command = TruncateCommand(name=filename, size=test_truncate_size)
        command.exec()

        file_descriptor = command._system_state.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_state.get_descriptor_blocks(
            file_descriptor
        )

        file = command._memory_proxy.get_descriptor(
            file_descriptor, file_descriptor_blocks
        )
        self.assertEqual(file.size, test_truncate_size)

        content = file.read_content(file.size, offset=0)
        self.assertEqual(content, lorem_ipsum[:test_truncate_size])

    def test_truncate_size_up_file(self) -> None:
        filename = "file1"
        CreateCommand(name=filename).exec()

        test_fd = 100

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            OpenCommand(name=filename).exec()

        WriteCommand(fd=str(test_fd), offset=0, content=lorem_ipsum).exec()

        test_truncate_size = len(lorem_ipsum) * 2

        command = TruncateCommand(name=filename, size=test_truncate_size)
        command.exec()

        file_descriptor = command._system_state.get_descriptor_id(filename)
        file_descriptor_blocks = command._system_state.get_descriptor_blocks(
            file_descriptor
        )

        file = command._memory_proxy.get_descriptor(
            file_descriptor, file_descriptor_blocks
        )
        self.assertEqual(file.size, len(lorem_ipsum))
