from fs.commands.base import BaseFSCommand
from fs.exceptions import FileNotExists


class UnlinkCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]

        resolved_path = self.resolve_path(path, resolve_symlink=False)

        try:
            file_descriptor = self.get_file_descriptor_by_path(
                resolved_path.fs_object_path
            )
        except FileNotExists:
            self._logger.info(f"Can't delete symlink for non existing file `{path}`.")

        else:
            total_refs_count = self._memory_proxy.add_ref_count(file_descriptor, -1)

            if not total_refs_count:
                resolved_path.directory.remove_directory_link(path)

                self._memory_proxy.write(resolved_path.directory)
                self._system_state.remove(file_descriptor, resolved_path.fs_object_path)

            else:
                self._system_state.unmap_path_from_descriptor(
                    resolved_path.fs_object_path
                )

            self._logger.info(
                f"Successfully unlinked `{path}` with descriptor `{file_descriptor.n}`."
            )
