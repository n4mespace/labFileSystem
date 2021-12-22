from fs.commands.base import BaseFSCommand
from fs.exceptions import FileNotExists


class OpenCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]

        descriptor_id = self._system_state.get_descriptor_id(path)

        if not descriptor_id:
            raise FileNotExists("Can't find file with such a path.")

        descriptor_blocks = self._system_state.get_descriptor_blocks(descriptor_id)

        fd = self._system_state.map_filepath_to_fd(path)

        descriptor = self._memory_proxy.get_descriptor(descriptor_id, descriptor_blocks)
        descriptor.opened = True

        self.save(descriptor, path)
        self._logger.info(f"Successfully opened file [{path}] with fd [{fd}].")
