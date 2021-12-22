from constants import ROOT_DESCRIPTOR_N
from fs.commands.base import BaseFSCommand
from fs.exceptions import FileAlreadyExists


class CreateCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]

        if self._system_state.check_path_exists(path):
            raise FileAlreadyExists(
                "Can't create new file with name of already existing one."
            )

        n = self._system_state.get_new_descriptor_id()
        root_blocks = self._system_state.get_descriptor_blocks(ROOT_DESCRIPTOR_N)

        current_directory_descriptor = self._memory_proxy.get_directory_descriptor(
            ROOT_DESCRIPTOR_N, root_blocks
        )
        file = self._memory_proxy.create_file(
            n=n,
            directory_descriptor=current_directory_descriptor,
            name=name,
        )

        self.save(file.descriptor, path)
        self.save(current_directory_descriptor, self._system_state.get_cwd_name())
