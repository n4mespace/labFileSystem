from constants import BLOCK_HEADER_SIZE_BYTES, BLOCK_SIZE_BYTES
from fs.commands.mkdir import MkdirCommand
from fs.commands.rmdir import RmdirCommand
from fs.driver.utils import form_header_from_bytes
from tests.conftest import FSBaseMountAndMkfsTestCase


class TestFSLab3(FSBaseMountAndMkfsTestCase):
    def test_mkdir(self) -> None:
        dirname = "dir1"
        command = MkdirCommand(path=dirname)
        command.exec()

        dirpath = command.resolve_path(path=dirname)

        self.assertTrue(
            dirpath.fs_object_path
            in command._system_state.get_path_to_descriptor_mapping()
        )

        self.get_directory_descriptor(command, dirpath.fs_object_path)

    def test_rmdir(self) -> None:
        dirname = "dir1"

        MkdirCommand(path=dirname).exec()

        command = RmdirCommand(path=dirname)

        dirpath = command.resolve_path(path=dirname)

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