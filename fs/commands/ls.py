from tabulate import tabulate

from constants import ROOT_DESCRIPTOR_N
from fs.commands.base import BaseFSCommand
from fs.exceptions import FSNotFormatted
from fs.models.descriptor.directory import DirectoryDescriptor


class LsCommand(BaseFSCommand):
    def exec(self) -> None:
        if not self._system_data.check_system_formatted():
            raise FSNotFormatted("Can't perform actions on not formatted fs.")

        root_blocks = self._system_data.get_descriptor_blocks(ROOT_DESCRIPTOR_N)

        current_directory = self._memory_proxy.get_directory_descriptor(
            ROOT_DESCRIPTOR_N, root_blocks
        )
        links = current_directory.read_directory_links()

        output_headers = ["name", "descriptor", "directory", "refs_count", "size"]
        output_info = []

        for name, descriptor_id in links.items():
            descriptor_blocks = self._system_data.get_descriptor_blocks(descriptor_id)
            descriptor = self._memory_proxy.get_descriptor(
                descriptor_id, descriptor_blocks
            )

            output_info.append(
                [
                    name,
                    descriptor.n,
                    isinstance(descriptor, DirectoryDescriptor),
                    descriptor.refs_count,
                    descriptor.size,
                ]
            )

            # Add also symlinks.
            symlinks = [
                link
                for link, descriptor in self._system_data.get_name_to_descriptor_mapping().items()
                if link and descriptor == descriptor_id and name != link
            ]

            for symlink in symlinks:
                output_info.append(
                    [
                        symlink,
                        descriptor.n,
                        isinstance(descriptor, DirectoryDescriptor),
                        descriptor.refs_count,
                        descriptor.size,
                    ]
                )

        self._logger.info("\n" + tabulate(output_info, headers=output_headers))
