from constants import DIRECTORY_DEFAULT_LINKS_COUNT
from fs.commands.base import BaseFSCommand
from fs.exceptions import DirectoryNotEmpty, DirectoryNotExists


class RmdirCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]

        resolved_path = self.resolve_path(path)

        if not self._system_state.check_path_exists(resolved_path.fs_object_path):
            raise DirectoryNotExists("Can't delete not existing directory.")

        directory = self.get_directory_descriptor_by_path(resolved_path.fs_object_path)

        if len(directory.read_directory_links()) != DIRECTORY_DEFAULT_LINKS_COUNT:
            raise DirectoryNotEmpty("Can't delete non-empty directory")

        directory.clear()
        self._memory_proxy.write(directory)
        self._memory_proxy.add_ref_count(directory, -1)
        self._system_state.remove(directory, resolved_path.fs_object_path)

        resolved_path.directory.remove_directory_link(resolved_path.fs_object_name)
        resolved_path.directory.update_size()
        self.save(resolved_path.directory, resolved_path.directory_path)

        self._logger.info(f"Successfully created directory [{path}].")
