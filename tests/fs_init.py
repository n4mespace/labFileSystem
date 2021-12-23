from constants import BLOCK_SIZE_BYTES, N_BLOCKS_MAX, N_DESCRIPTORS
from fs.commands.mkfs import MkfsCommand
from fs.commands.mount import MountCommand
from fs.commands.umount import UmountCommand
from tests.conftest import FSBaseTestCase


class TestFSInitialization(FSBaseTestCase):
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
