from fs.commands.base import BaseFSCommand
from fs.exceptions import FileDescriptorNotExists, FileNotExists


class CloseCommand(BaseFSCommand):
    def exec(self) -> None:
        fd = self.kwargs["df"]

        name = self._system_data.get_descriptor_name(fd)

        if not name:
            raise FileDescriptorNotExists(
                "Can't find file with such a file descriptor."
            )

        descriptor_id = self._system_data.get_descriptor_id(name)

        if not descriptor_id:
            raise FileNotExists("Can't find file with such a name.")

        descriptor_blocks = self._system_data.get_descriptor_blocks(descriptor_id)

        self._system_data.unmap_fd_from_name(fd)

        descriptor = self._memory_proxy.get_descriptor(descriptor_id, descriptor_blocks)
        descriptor.opened = False
        self._memory_proxy.write(descriptor)

        self._logger.info(f"Successfully closed file [{name}] with fd [{fd}].")
