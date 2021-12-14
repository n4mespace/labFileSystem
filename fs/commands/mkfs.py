from constants import N_BLOCKS_MAX, ROOT_DESCRIPTOR_N
from fs.commands.base import BaseFSCommand
from fs.exceptions import FSNotMounted


class MkfsCommand(BaseFSCommand):
    def exec(self) -> None:
        n = self.kwargs["n"]

        self._logger.info(f"Formatting fs with `{n}` descriptors.")

        if not self._system_state.check_mounted():
            raise FSNotMounted("Can't format fs on unmounted device.")

        self._system_state.init_descriptors(n)
        root = self._memory_proxy.create_directory(
            n=ROOT_DESCRIPTOR_N,
            name="",
            opened=True,
            parent=None,  # noqa: For root dir we hardcode parent link.
            root=True,
        )
        root.parent = root

        self._system_state.write(root.descriptor, name="")

        self._memory_proxy.clear()
        self._memory_proxy.write(root.descriptor)
        self._memory_proxy.write_empty_blocks(N_BLOCKS_MAX, start_from=1)

        self._logger.info("Successfully formatted.")
