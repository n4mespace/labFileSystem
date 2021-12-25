from tabulate import tabulate

from fs.commands.base import BaseFSCommand
from fs.exceptions import FSNotFormatted
from fs.models.descriptor.base import Descriptor
from fs.models.descriptor.directory import DirectoryDescriptor
from fs.models.descriptor.file import FileDescriptor
from fs.models.descriptor.symlink import SymlinkDescriptor


class LsCommand(BaseFSCommand):
    output_headers: list[str] = [
        "name",
        "descriptor",
        "type",
        "refs_count",
        "size",
    ]
    descriptor_types: dict[Descriptor, str] = {
        DirectoryDescriptor: "directory",
        FileDescriptor: "file",
        SymlinkDescriptor: "symlink",
    }

    def exec(self) -> None:
        if not self._system_state.check_system_formatted():
            raise FSNotFormatted("Can't perform actions on not formatted fs.")

        resolved_path = self.resolve_path(to_dir=True)

        links = resolved_path.directory.read_directory_links()
        output_info = []

        for fs_object_name, descriptor_id in links.items():
            descriptor_blocks = self._system_state.get_descriptor_blocks(descriptor_id)
            descriptor = self._memory_proxy.get_descriptor(
                descriptor_id, descriptor_blocks
            )

            descriptor_type = self.descriptor_types[type(descriptor)]

            output_info.append(
                [
                    fs_object_name,
                    descriptor.n,
                    descriptor_type,
                    descriptor.refs_count,
                    descriptor.size,
                ]
            )

            # Add also symlinks.
            symlink_resolved_path = self.resolve_path(fs_object_name)

            symlinks = [
                link
                for link, descriptor in self._system_state.get_path_to_descriptor_mapping().items()
                if (
                    link.replace(symlink_resolved_path.directory_path, "", 1)
                    and descriptor == descriptor_id
                    and symlink_resolved_path.fs_object_path != link
                    and resolved_path.directory_path != link
                )
            ]

            for symlink in symlinks:
                output_info.append(
                    [
                        symlink,
                        descriptor.n,
                        descriptor_type,
                        descriptor.refs_count,
                        descriptor.size,
                    ]
                )

        self._logger.info("\n" + tabulate(output_info, headers=self.output_headers))
