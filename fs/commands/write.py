from fs.commands.base import BaseFSCommand
from fs.exceptions import FileDescriptorNotExists, FileNotExists


class WriteCommand(BaseFSCommand):
    def exec(self) -> None:
        fd, offset, content = (
            self.kwargs["fd"],
            self.kwargs["offset"],
            self.kwargs["content"],
        )

        name = self._system_state.get_descriptor_name(fd)

        if not name:
            raise FileDescriptorNotExists(
                "Can't find file with such a file descriptor."
            )

        descriptor_id = self._system_state.get_descriptor_id(name)

        if not descriptor_id:
            raise FileNotExists("Can't find file with such a name.")

        descriptor_blocks = self._system_state.get_descriptor_blocks(descriptor_id)

        descriptor = self._memory_proxy.get_file_descriptor(
            descriptor_id, descriptor_blocks
        )
        descriptor.write_content(content, offset)
        descriptor.update_size()

        self._memory_proxy.write(descriptor)
        self._system_state.write(descriptor, name)

        self._logger.info(
            f"Successfully written `{content}` to [{name}] with fd [{fd}]."
        )
