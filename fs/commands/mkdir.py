from fs.commands.base import BaseFSCommand
from fs.exceptions import DirectoryAlreadyExists


class MkdirCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]
        resolved_path = self.resolve_path(path)

        if self._system_state.check_path_exists(resolved_path.fs_object_path):
            raise DirectoryAlreadyExists(
                "Can't create new directory, one is already exists."
            )

        n = self._system_state.get_new_descriptor_id()

        new_directory = self._memory_proxy.create_directory(
            n=n,
            name=resolved_path.fs_object_name,
            opened=False,
            parent=resolved_path.directory,
        )

        self.save(new_directory.descriptor, resolved_path.fs_object_path)
        self.save(resolved_path.directory, resolved_path.directory_path)

        self._logger.info(f"Successfully created directory [{path}].")
