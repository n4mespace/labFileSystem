from fs.commands.base import BaseFSCommand
from fs.exceptions import DirectoryAlreadyExists


class MkdirCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]

        destination_directory, destination_name = ...

        if self._system_state.check_path_exists():
            raise DirectoryAlreadyExists(
                "Can't create new directory, one is already exists."
            )

        n = self._system_state.get_new_descriptor_id()

        new_directory = self._memory_proxy.create_directory(
            n=n,
            name=destination_name,
            opened=False,
            parent=destination_directory,
        )

        self.save(new_directory.descriptor, path)

        self._logger.info(f"Successfully created directory [{path}].")
