from constants import ROOT_DESCRIPTOR_N
from fs.commands.base import BaseFSCommand


class UnlinkCommand(BaseFSCommand):
    def exec(self) -> None:
        name = self.kwargs["name"]

        descriptor_id = self._system_state.get_descriptor_id(name)

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
                current_directory_descriptor.remove_directory_link(name)

                self._memory_proxy.write(current_directory_descriptor)
                self._system_state.remove(descriptor, name)

            else:
                self._system_state.unmap_name_from_descriptor(name)

            self._logger.info(
                f"Successfully unlinked `{name}` with descriptor `{descriptor_id}`."
            )
        else:
            self._logger.info(f"Can't delete symlink for non existing file `{name}`.")
