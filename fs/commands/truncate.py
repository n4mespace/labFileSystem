from fs.commands.base import BaseFSCommand
from fs.exceptions import FileNotExists


class TruncateCommand(BaseFSCommand):
    def exec(self) -> None:
        path, size = self.kwargs["path"], self.kwargs["size"]

        descriptor_id = self._system_state.get_descriptor_id(path)

        if not descriptor_id:
            raise FileNotExists("Can't find file with such a path.")

        descriptor_blocks = self._system_state.get_descriptor_blocks(descriptor_id)
        descriptor = self._memory_proxy.get_descriptor(descriptor_id, descriptor_blocks)
        old_size = descriptor.size

        blocks_deleted = descriptor.truncate(size)

        # Delete unused blocks.
        for block in blocks_deleted:
            self._memory_proxy.write_empty_blocks(block.n + 1, start_from=block.n)

        descriptor.update_size()

        self.save(descriptor, path)
        self._logger.info(
            f"Successfully changed [{path}] size from [{old_size}] to [{size}]."
        )
