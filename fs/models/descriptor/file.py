from dataclasses import dataclass

from fs.models.descriptor.base import Descriptor, FSObject
from fs.models.descriptor.directory import DirectoryDescriptor


@dataclass
class FileDescriptor(Descriptor):
    ...


@dataclass
class File(FSObject):
    descriptor: FileDescriptor
    directory: DirectoryDescriptor
