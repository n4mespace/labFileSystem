from fs.commands.base import BaseFSCommand
from fs.exceptions import FileAlreadyExists


class CreateCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]

        if self._system_state.check_path_exists(path):
            raise FileAlreadyExists(
                "Can't create new file with name of already existing one."
            )

        resolved_path = self.resolve_path(path)
        n = self._system_state.get_new_descriptor_id()

        file = self._memory_proxy.create_file(
            n=n,
            directory_descriptor=resolved_path.directory,
            name=resolved_path.fs_object_path,
        )

        self.save(file.descriptor, resolved_path.fs_object_path)
        self.save(resolved_path.directory, resolved_path.directory_path)
