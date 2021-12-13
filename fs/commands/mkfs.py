from constants import ROOT_DESCRIPTOR_N, ROOT_BLOCK_N, N_BLOCKS_MAX
from fs.commands.base import BaseFSCommand
from fs.exceptions import FSNotMounted


class MkfsCommand(BaseFSCommand):
    def exec(self) -> None:
        n = self.kwargs["n"]

        self._logger.info(f"Formatting fs with `{n}` descriptors.")

        if not self._system_data.check_mounted():
            raise FSNotMounted("Can't format fs on unmounted device.")

        self._system_data.init_descriptors(n)
        root = self._memory_proxy.create_directory(
            n=ROOT_DESCRIPTOR_N,
            block_n=ROOT_BLOCK_N,
            name="",
            opened=True,
            parent=None,  # noqa: For root dir we hardcode parent link.
            root=True,
        )
        root.parent = root

        self._system_data.write_descriptor_to_config(root.descriptor, name="")

        self._memory_proxy.clear()
        self._memory_proxy.write(root.descriptor)
        self._memory_proxy.write_empty_blocks(N_BLOCKS_MAX, start_from=1)

        self._logger.info("Successfully formatted.")
