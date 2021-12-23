from fs.commands.base import BaseFSCommand


class OpenCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]

        resolved_path = self.resolve_path(path)

        file_descriptor = self.get_file_descriptor_by_path(resolved_path.fs_object_path)
        file_descriptor.opened = True
        self.save(file_descriptor, path)

        fd = self._system_state.map_filepath_to_fd(resolved_path.fs_object_path)
        self._logger.info(f"Successfully opened file [{path}] with fd [{fd}].")
