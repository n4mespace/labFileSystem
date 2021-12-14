from fs.commands.base import BaseFSCommand


class LinkCommand(BaseFSCommand):
    def exec(self) -> None:
        name1, name2 = self.kwargs["name1"], self.kwargs["name2"]

        descriptor_id = self._system_state.get_descriptor_id(name1)

        if descriptor_id:
            descriptor_blocks = self._system_state.get_descriptor_blocks(descriptor_id)
            descriptor = self._memory_proxy.get_descriptor(
                descriptor_id, descriptor_blocks
            )
            self._memory_proxy.add_ref_count(descriptor, 1)

            self._system_state.map_name_to_descriptor(name2, descriptor_id)
            self._logger.info(f"Successfully linked `{name2}` with `{name1}`.")

        else:
            self._logger.info(f"Can't create symlink for non existing file `{name1}`.")
