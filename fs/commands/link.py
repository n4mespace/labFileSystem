from fs.commands.base import BaseFSCommand


class LinkCommand(BaseFSCommand):
    def exec(self) -> None:
        path1, path2 = self.kwargs["path1"], self.kwargs["path2"]

        descriptor_id = self._system_state.get_descriptor_id(path1)

        if descriptor_id:
            descriptor_blocks = self._system_state.get_descriptor_blocks(descriptor_id)
            descriptor = self._memory_proxy.get_descriptor(
                descriptor_id, descriptor_blocks
            )
            self._memory_proxy.add_ref_count(descriptor, 1)

            self._system_state.map_path_to_descriptor(path2, descriptor_id)
            self._logger.info(f"Successfully linked `{path2}` with `{path1}`.")

        else:
            self._logger.info(f"Can't create symlink for non existing file `{path1}`.")
