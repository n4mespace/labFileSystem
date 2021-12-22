from fs.commands.base import BaseFSCommand
from fs.exceptions import FileDescriptorNotExists, FileNotExists


class CloseCommand(BaseFSCommand):
    def exec(self) -> None:
        fd = self.kwargs["fd"]

        path = self._system_state.get_descriptor_path(fd)

        if not path:
            raise FileDescriptorNotExists(
                "Can't find file with such a file descriptor."
            )

        descriptor_id = self._system_state.get_descriptor_id(path)

        if not descriptor_id:
            raise FileNotExists("Can't find file with such a path.")

        descriptor_blocks = self._system_state.get_descriptor_blocks(descriptor_id)

        self._system_state.unmap_fd_from_path(fd)

        descriptor = self._memory_proxy.get_descriptor(descriptor_id, descriptor_blocks)
        descriptor.opened = False

        self.save(descriptor, path)
        self._logger.info(f"Successfully closed file [{path}] with fd [{fd}].")
