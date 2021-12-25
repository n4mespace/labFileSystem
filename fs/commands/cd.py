from fs.commands.base import BaseFSCommand


class CdCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]

        current_resolved_path = self.resolve_path()

        current_directory_descriptor = self.get_directory_descriptor_by_path(
            current_resolved_path.fs_object_path
        )
        current_directory_descriptor.opened = False
        self.save(current_directory_descriptor, current_resolved_path.fs_object_path)

        resolved_path = self.resolve_path(path)
        directory_descriptor = self.get_directory_descriptor_by_path(
            resolved_path.fs_object_path
        )
        directory_descriptor.opened = True
        self.save(directory_descriptor, resolved_path.fs_object_path)

        self._system_state.set_cwd(resolved_path.fs_object_path)
