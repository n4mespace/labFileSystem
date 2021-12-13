from constants import ROOT_DESCRIPTOR_N
from fs.commands.base import BaseFSCommand
from fs.exceptions import FileAlreadyExists


class CreateCommand(BaseFSCommand):
    def exec(self) -> None:
        name = self.kwargs["name"]

        if self._system_data.check_name_exists(name):
            raise FileAlreadyExists(
                "Can't create new file with name of already existing one."
            )

        n = self._system_data.get_new_descriptor_id()
        root_blocks = self._system_data.get_descriptor_blocks(ROOT_DESCRIPTOR_N)

        current_directory_descriptor = self._memory_proxy.get_directory_descriptor(
            ROOT_DESCRIPTOR_N, root_blocks
        )

        file = self._memory_proxy.create_file(
            n=n,
            directory_descriptor=current_directory_descriptor,
            name=name,
        )

        self._system_data.write_descriptor_to_config(file.descriptor, name)

        self._memory_proxy.write(file.descriptor)
        self._memory_proxy.write(current_directory_descriptor)
