from fs.commands.base import BaseFSCommand
from fs.exceptions import FileNotExists


class LinkCommand(BaseFSCommand):
    def exec(self) -> None:
        path1, path2 = self.kwargs["path1"], self.kwargs["path2"]

        resolved_path1 = self.resolve_path(path1)
        resolved_path2 = self.resolve_path(path2, must_exists=False)

        try:
            file_descriptor = self.get_file_descriptor_by_path(
                resolved_path1.fs_object_path
            )
        except FileNotExists:
            self._logger.info(f"Can't create symlink for non existing file `{path1}`.")

        else:
            self._memory_proxy.add_ref_count(file_descriptor, 1)
            self._system_state.map_path_to_descriptor(
                resolved_path2.fs_object_path, file_descriptor
            )

            self._logger.info(f"Successfully linked `{path2}` with `{path1}`.")
