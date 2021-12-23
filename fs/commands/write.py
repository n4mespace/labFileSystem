from fs.commands.base import BaseFSCommand
from fs.exceptions import FileDescriptorNotExists


class WriteCommand(BaseFSCommand):
    def exec(self) -> None:
        fd, offset, content = (
            self.kwargs["fd"],
            self.kwargs["offset"],
            self.kwargs["content"],
        )

        path = self._system_state.get_descriptor_path(fd)

        if not path:
            raise FileDescriptorNotExists(
                "Can't find file with such a file descriptor."
            )

        file_descriptor = self.get_file_descriptor_by_path(path)
        file_descriptor.write_content(content, offset)
        file_descriptor.update_size()

        self.save(file_descriptor, path)
        self._logger.info(
            f"Successfully written `{content}` to [{path}] with fd [{fd}]."
        )
