from constants import ROOT_DESCRIPTOR_N
from fs.commands.base import BaseFSCommand


class UnlinkCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]

        descriptor_id = self._system_state.get_descriptor_id(path)

        if descriptor_id:
            descriptor_blocks = self._system_state.get_descriptor_blocks(descriptor_id)
            root_blocks = self._system_state.get_descriptor_blocks(ROOT_DESCRIPTOR_N)

            descriptor = self._memory_proxy.get_descriptor(
                descriptor_id, descriptor_blocks
            )
            total_refs_count = self._memory_proxy.add_ref_count(descriptor, -1)

            if not total_refs_count:
                current_directory_descriptor = (
                    self._memory_proxy.get_directory_descriptor(
                        ROOT_DESCRIPTOR_N, root_blocks
                    )
                )
                current_directory_descriptor.remove_directory_link(path)

                self._memory_proxy.write(current_directory_descriptor)
                self._system_state.remove(descriptor, path)

            else:
                self._system_state.unmap_path_from_descriptor(path)

            self._logger.info(
                f"Successfully unlinked `{path}` with descriptor `{descriptor_id}`."
            )
        else:
            self._logger.info(f"Can't delete symlink for non existing file `{path}`.")
