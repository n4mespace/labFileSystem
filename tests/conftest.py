from unittest import TestCase

import pytest
from _pytest.logging import LogCaptureFixture

from constants import N_DESCRIPTORS
from fs.commands.base import BaseFSCommand
from fs.commands.mkfs import MkfsCommand
from fs.commands.mount import MountCommand
from fs.commands.umount import UmountCommand
from fs.exceptions import FSNotMounted
from fs.models.descriptor.base import Descriptor
from fs.models.descriptor.directory import DirectoryDescriptor
from fs.models.descriptor.file import FileDescriptor
from fs.models.descriptor.symlink import SymlinkDescriptor

LOREM_IPSUM: str = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, "
    "quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. "
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu "
    "fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa "
    "qui officia deserunt mollit anim id est laborum."
)


class FSBaseTestCase(TestCase):
    def setUp(self) -> None:
        try:
            UmountCommand().exec()
        except FSNotMounted:
            # For test cases correct work.
            pass


class FSBaseMountAndMkfsTestCase(FSBaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        MountCommand().exec()
        MkfsCommand(n=N_DESCRIPTORS).exec()

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog: LogCaptureFixture) -> None:
        self._caplog = caplog

    def _get_descriptor(
        self,
        command: BaseFSCommand,
        path: str,
        descriptor_type: type[Descriptor],
    ) -> Descriptor:
        descriptor_id = command._system_state.get_descriptor_id(path)
        self.assertIsNotNone(descriptor_id)

        descriptor_blocks = command._system_state.get_descriptor_blocks(descriptor_id)

        descriptor = command._memory_proxy.get_descriptor(
            descriptor_id, descriptor_blocks
        )
        self.assertIsInstance(descriptor, descriptor_type)

        return descriptor

    def get_file_descriptor(
        self, command: BaseFSCommand, filepath: str
    ) -> FileDescriptor:
        return self._get_descriptor(command, filepath, FileDescriptor)  # type: ignore

    def get_directory_descriptor(
        self, command: BaseFSCommand, dirpath: str
    ) -> DirectoryDescriptor:
        return self._get_descriptor(command, dirpath, DirectoryDescriptor)  # type: ignore

    def get_symlink_descriptor(
        self, command: BaseFSCommand, symlink_path: str
    ) -> SymlinkDescriptor:
        return self._get_descriptor(command, symlink_path, SymlinkDescriptor)  # type: ignore
