from fs.commands.base import BaseFSCommand
from fs.exceptions import FileDescriptorNotExists, FileNotExists


class ReadCommand(BaseFSCommand):
    def exec(self) -> None:
        fd, offset, size = self.kwargs["fd"], self.kwargs["offset"], self.kwargs["size"]

        name = self._system_data.get_descriptor_name(fd)

        if not name:
            raise FileDescriptorNotExists(
                "Can't find file with such a file descriptor."
            )

        descriptor_id = self._system_data.get_descriptor_id(name)

        if not descriptor_id:
            raise FileNotExists("Can't find file with such a name.")

        descriptor_blocks = self._system_data.get_descriptor_blocks(descriptor_id)

        descriptor = self._memory_proxy.get_file_descriptor(
            descriptor_id, descriptor_blocks
        )
        content = descriptor.read_content(size, offset)

        self._logger.info(f"Successfully read from [{name}] with fd [{fd}]:")
        self._logger.info(content)
