from dataclasses import dataclass

from fs.models.descriptor.file import File, FileDescriptor


@dataclass
class SymlinkDescriptor(FileDescriptor):
    ...


@dataclass
class Symlink(File):
    descriptor: SymlinkDescriptor
