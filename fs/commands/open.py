from fs.commands.base import BaseFSCommand
from fs.exceptions import FileNotExists


class OpenCommand(BaseFSCommand):
    def exec(self) -> None:
        name = self.kwargs["name"]

        descriptor_id = self._system_data.get_descriptor_id(name)

        if not descriptor_id:
            raise FileNotExists("Can't find file with such a name.")

        descriptor_blocks = self._system_data.get_descriptor_blocks(descriptor_id)

        fd = self._system_data.map_file_to_fd(name)

        descriptor = self._memory_proxy.get_descriptor(descriptor_id, descriptor_blocks)
        descriptor.opened = True
        self._memory_proxy.write(descriptor)

        self._logger.info(f"Successfully opened file [{name}] with fd [{fd}].")
