from fs.commands.base import BaseFSCommand
from fs.exceptions import FileAlreadyExists


class SymlinkCommand(BaseFSCommand):
    def exec(self) -> None:
        content, path = self.kwargs["content"], self.kwargs["path"]

        resolved_path = self.resolve_path(path, resolve_symlink=False)

        if self._system_state.check_path_exists(resolved_path.fs_object_path):
            raise FileAlreadyExists(
                "Can't create new symlink with name of already existing one."
            )

        n = self._system_state.get_new_descriptor_id()

        symlink = self._memory_proxy.create_symlink(
            n=n,
            directory_descriptor=resolved_path.directory,
            name=resolved_path.fs_object_name,
            content=content,
        )

        self.save(symlink.descriptor, resolved_path.fs_object_path)
        self.save(resolved_path.directory, resolved_path.directory_path)
