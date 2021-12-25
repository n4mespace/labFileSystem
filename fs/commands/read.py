from fs.commands.base import BaseFSCommand
from fs.exceptions import FileDescriptorNotExists


class ReadCommand(BaseFSCommand):
    def exec(self) -> None:
        fd, offset, size = self.kwargs["fd"], self.kwargs["offset"], self.kwargs["size"]

        path = self._system_state.get_descriptor_path(fd)

        if not path:
            raise FileDescriptorNotExists(
                "Can't find file with such a file descriptor."
            )

        file_descriptor = self.get_file_descriptor_by_path(path)
        content = file_descriptor.read_content(size, offset)

        self._logger.info(f"Successfully read from fd [{fd}]:")
        self._logger.info(content)
