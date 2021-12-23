from dataclasses import dataclass

from fs.models.descriptor.directory import DirectoryDescriptor


@dataclass
class ResolvedPath:
    directory: DirectoryDescriptor
    directory_path: str
    fs_object_name: str
    fs_object_path: str
