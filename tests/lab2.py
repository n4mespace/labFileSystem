import logging
from unittest import mock

from constants import BLOCK_HEADER_SIZE_BYTES, BLOCK_SIZE_BYTES
from fs.commands.close import CloseCommand
from fs.commands.create import CreateCommand
from fs.commands.link import LinkCommand
from fs.commands.ls import LsCommand
from fs.commands.open import OpenCommand
from fs.commands.truncate import TruncateCommand
from fs.commands.unlink import UnlinkCommand
from fs.commands.write import WriteCommand
from fs.driver.utils import form_header_from_bytes
from tests.base import LOREM_IPSUM, FSBaseMountAndMkfsTestCase


class FSWorkLab2Tests(FSBaseMountAndMkfsTestCase):
    def test_create_file(self) -> None:
        filename = "file1"
        command = CreateCommand(path=filename)
        command.exec()

        self.assertTrue(
            filename in command._system_state.get_path_to_descriptor_mapping()
        )
        self.get_file_descriptor(command, filename)

    def test_create_n_files(self) -> None:
        for i in range(5):
            filename = f"file_{i}"
            command = CreateCommand(path=filename)
            command.exec()

            self.get_file_descriptor(command, filename)

    def test_ls_files(self) -> None:
        created_files = []

        for i in range(5):
            filename = f"file_{i}"

            CreateCommand(path=filename).exec()
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
        CreateCommand(path=filename).exec()

        link_filename = "file1_link"
        command = LinkCommand(path1=filename, path2=link_filename)
        command.exec()

        file = self.get_file_descriptor(command, filename)
        file_link = self.get_file_descriptor(command, filename)

        self.assertEqual(file.n, file_link.n)
        self.assertEqual(file.refs_count, 2)

    def test_unlink_file(self) -> None:
        filename = "file1"
        CreateCommand(path=filename).exec()

        link_filename = "file1_link"
        LinkCommand(path1=filename, path2=link_filename).exec()

        command = UnlinkCommand(path=link_filename)
        command.exec()

        self.assertTrue(
            link_filename not in command._system_state.get_path_to_descriptor_mapping()
        )

        file = self.get_file_descriptor(command, filename)
        self.assertEqual(file.refs_count, 1)

    def test_delete_file(self) -> None:
        filename = "file1"
        CreateCommand(path=filename).exec()

        command = UnlinkCommand(path=filename)

        file_descriptor = command._system_state.get_descriptor_id(filename)
        self.assertIsNotNone(file_descriptor)

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
        CreateCommand(path=filename).exec()

        command = OpenCommand(path=filename)

        test_fd = 100

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            command.exec()

        self.assertTrue(str(test_fd) in command._system_state.get_fd_to_path_mapping())

        file = self.get_file_descriptor(command, filename)
        self.assertTrue(file.opened)

    def test_close_file(self) -> None:
        filename = "file1"
        CreateCommand(path=filename).exec()

        test_fd = 100

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            OpenCommand(path=filename).exec()

        command = CloseCommand(fd=str(test_fd))
        command.exec()

        file = self.get_file_descriptor(command, filename)
        self.assertFalse(file.opened)

    def test_write_file(self) -> None:
        filename = "file1"
        CreateCommand(path=filename).exec()

        test_fd = 100

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            OpenCommand(path=filename).exec()

        test_content = "hello_world"

        command = WriteCommand(fd=str(test_fd), offset=0, content=test_content)
        command.exec()

        file = self.get_file_descriptor(command, filename)
        self.assertEqual(file.size, len(test_content))

        content = file.read_content(len(test_content), offset=0)
        self.assertEqual(content, test_content)

    def test_write_large_data_to_file(self) -> None:
        filename = "file1"
        CreateCommand(path=filename).exec()

        test_fd = 100

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            OpenCommand(path=filename).exec()

        command = WriteCommand(fd=str(test_fd), offset=3, content=LOREM_IPSUM)
        command.exec()

        file = self.get_file_descriptor(command, filename)

        self.assertEqual(file.size, len(LOREM_IPSUM))

        content = file.read_content(len(LOREM_IPSUM), offset=3)
        self.assertEqual(content, LOREM_IPSUM)

    def test_truncate_size_down_file(self) -> None:
        filename = "file1"
        CreateCommand(path=filename).exec()

        test_fd = 100

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            OpenCommand(path=filename).exec()

        WriteCommand(fd=str(test_fd), offset=0, content=LOREM_IPSUM).exec()

        test_truncate_size = len(LOREM_IPSUM) // 2

        command = TruncateCommand(path=filename, size=test_truncate_size)
        command.exec()

        file = self.get_file_descriptor(command, filename)

        content = file.read_content(file.size, offset=0)
        self.assertEqual(content, LOREM_IPSUM[:test_truncate_size])

    def test_truncate_size_up_file(self) -> None:
        filename = "file1"
        CreateCommand(path=filename).exec()

        test_fd = 100

        # For getting predictable `fd` we should mock `random.randint` result.
        with mock.patch("random.randint", lambda _x, _y: test_fd):
            OpenCommand(path=filename).exec()

        WriteCommand(fd=str(test_fd), offset=0, content=LOREM_IPSUM).exec()

        test_truncate_size = len(LOREM_IPSUM) * 2

        command = TruncateCommand(path=filename, size=test_truncate_size)
        command.exec()

        file = self.get_file_descriptor(command, filename)

        self.assertEqual(file.size, len(LOREM_IPSUM))
