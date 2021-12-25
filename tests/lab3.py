import logging

from constants import (BLOCK_HEADER_SIZE_BYTES, BLOCK_SIZE_BYTES, PATH_DIVIDER,
                       ROOT_DIRECTORY_PATH)
from fs.commands.cd import CdCommand
from fs.commands.cwd import CwdCommand
from fs.commands.link import LinkCommand
from fs.commands.mkdir import MkdirCommand
from fs.commands.rmdir import RmdirCommand
from fs.commands.symlink import SymlinkCommand
from fs.commands.unlink import UnlinkCommand
from fs.driver.utils import form_header_from_bytes
from fs.exceptions import MaxSymlinkHopsExceeded
from tests.conftest import FSBaseMountAndMkfsTestCase


class TestFSLab3(FSBaseMountAndMkfsTestCase):
    def test_mkdir(self) -> None:
        dirname = "dir1"
        command = MkdirCommand(path=dirname)
        command.exec()

        dirpath = command.resolve_path(dirname)

        self.assertTrue(
            dirpath.fs_object_path
            in command._system_state.get_path_to_descriptor_mapping()
        )

        self.get_directory_descriptor(command, dirpath.fs_object_path)

    def test_rmdir(self) -> None:
        dirname = "dir1"

        MkdirCommand(path=dirname).exec()

        command = RmdirCommand(path=dirname)
        dirpath = command.resolve_path(dirname)

        directory_descriptor = command._system_state.get_descriptor_id(
            dirpath.fs_object_path
        )
        self.assertIsNotNone(directory_descriptor)

        directory_descriptor_blocks = command._system_state.get_descriptor_blocks(
            directory_descriptor
        )

        command.exec()

        self.assertTrue(
            dirpath.fs_object_path
            not in command._system_state.get_path_to_descriptor_mapping()
        )

        directory = command._memory_proxy.get_descriptor(
            directory_descriptor, directory_descriptor_blocks
        )

        self.assertEqual(directory.refs_count, 0)

        with command._memory_proxy.memory as m:
            for block in directory.blocks:
                m.seek(block.n * BLOCK_SIZE_BYTES)
                header_bytes = m.read(BLOCK_HEADER_SIZE_BYTES)

                header = form_header_from_bytes(header_bytes)

                self.assertFalse(header.used)
                self.assertEqual(header.ref_count, 0)

    def _test_cwd(self, right_cwd: str) -> None:
        with self._caplog.at_level(logging.INFO):
            CwdCommand().exec()
            command_output = self._caplog.records[-1].msg

        cwd_template = "Current working directory: "
        cwd = command_output.strip(cwd_template)

        self.assertEqual(cwd, right_cwd)

    def test_cd(self) -> None:
        command = CdCommand(path=ROOT_DIRECTORY_PATH)
        command.exec()
        self._test_cwd(right_cwd="/")

        command = CdCommand(path=".")
        command.exec()
        self._test_cwd(right_cwd="/")

        command = CdCommand(path="..")
        command.exec()
        self._test_cwd(right_cwd="/")

        # create some dir for test.
        dirname = "dir1"
        MkdirCommand(path=dirname).exec()

        command = CwdCommand()
        dirpath = command.resolve_path(dirname)

        command = CdCommand(path=dirpath.fs_object_path)
        command.exec()

        self._test_cwd(right_cwd=dirpath.fs_object_path)

    def test_create_symlink(self) -> None:
        symlink_name = "s1"
        test_content = "/dir1/dir2"

        command = SymlinkCommand(path=symlink_name, content=test_content)
        command.exec()

        symlink = self.get_symlink_descriptor(command, PATH_DIVIDER + symlink_name)
        self.assertEqual(symlink.size, len(test_content))

        content = symlink.read_content(len(test_content), offset=0)
        self.assertEqual(content, test_content)

    def test_link_symlink(self) -> None:
        symlink_name = "s1"
        test_content = "/dir1/dir2"

        SymlinkCommand(path=symlink_name, content=test_content).exec()

        link_filename = "s1_link"
        command = LinkCommand(path1=symlink_name, path2=link_filename)
        command.exec()

        symlink = self.get_symlink_descriptor(command, PATH_DIVIDER + symlink_name)

        symlink_link = self.get_symlink_descriptor(
            command, PATH_DIVIDER + link_filename
        )

        self.assertEqual(symlink.n, symlink_link.n)
        self.assertEqual(symlink.refs_count, 2)

    def test_unlink_symlink(self) -> None:
        symlink_name = "s1"
        test_content = "/dir1/dir2"

        SymlinkCommand(path=symlink_name, content=test_content).exec()

        link_filename = "s1_link"
        LinkCommand(path1=symlink_name, path2=link_filename).exec()

        command = UnlinkCommand(path=link_filename)
        command.exec()

        self.assertTrue(
            PATH_DIVIDER + link_filename
            not in command._system_state.get_path_to_descriptor_mapping()
        )

        symlink = self.get_symlink_descriptor(command, PATH_DIVIDER + symlink_name)
        self.assertEqual(symlink.refs_count, 1)

    def test_cd_symlink(self) -> None:
        symlink_name = "s1"
        test_content = "/dir1"

        SymlinkCommand(path=symlink_name, content=test_content).exec()

        dirname1 = "dir1"
        MkdirCommand(path=dirname1).exec()
        self._test_cwd(right_cwd="/")

        CdCommand(path=symlink_name).exec()
        self._test_cwd(right_cwd=test_content)

    def test_cd_symlink_within_other_dir(self) -> None:
        symlink_name = "s1"
        test_content = "/dir2"

        dirname1 = "dir1"
        MkdirCommand(path=dirname1).exec()

        dirname2 = "dir2"
        MkdirCommand(path=dirname2).exec()

        CdCommand(path=dirname1).exec()
        SymlinkCommand(path=symlink_name, content=test_content).exec()

        CdCommand(path=symlink_name).exec()
        self._test_cwd(right_cwd=test_content)

    def test_cd_symlink_max_hops(self) -> None:
        symlink_name = "s1"
        test_content = "/s1"

        SymlinkCommand(path=symlink_name, content=test_content).exec()
        self.assertRaises(MaxSymlinkHopsExceeded, CdCommand(path=symlink_name).exec)
