from fs.commands.base import BaseFSCommand
from fs.exceptions import FileDescriptorNotExists, FileNotExists


class ReadCommand(BaseFSCommand):
    def exec(self) -> None:
        fd, offset, size = self.kwargs["fd"], self.kwargs["offset"], self.kwargs["size"]

        path = self._system_state.get_descriptor_path(fd)

        if not path:
            raise FileDescriptorNotExists(
                "Can't find file with such a file descriptor."
            )

        descriptor_id = self._system_state.get_descriptor_id(path)

        if not descriptor_id:
            raise FileNotExists("Can't find file with such a name.")

        descriptor_blocks = self._system_state.get_descriptor_blocks(descriptor_id)

        descriptor = self._memory_proxy.get_file_descriptor(
            descriptor_id, descriptor_blocks
        )
        content = descriptor.read_content(size, offset)

        self._logger.info(f"Successfully read from [{path}] with fd [{fd}]:")
        self._logger.info(content)
