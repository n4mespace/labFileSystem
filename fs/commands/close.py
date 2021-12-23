from fs.commands.base import BaseFSCommand
from fs.exceptions import FileDescriptorNotExists


class CloseCommand(BaseFSCommand):
    def exec(self) -> None:
        fd = self.kwargs["fd"]

        path = self._system_state.get_descriptor_path(fd)

        if not path:
            raise FileDescriptorNotExists(
                "Can't find file with such a file descriptor."
            )

        file_descriptor = self.get_file_descriptor_by_path(path)
        file_descriptor.opened = False

        self._system_state.unmap_fd_from_path(fd)

        self.save(file_descriptor, path)
        self._logger.info(f"Successfully closed file [{path}] with fd [{fd}].")
