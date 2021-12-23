from fs.commands.base import BaseFSCommand


class TruncateCommand(BaseFSCommand):
    def exec(self) -> None:
        path, size = self.kwargs["path"], self.kwargs["size"]

        resolved_path = self.resolve_path(path)

        file_descriptor = self.get_file_descriptor_by_path(resolved_path.fs_object_path)
        old_size = file_descriptor.size

        blocks_deleted = file_descriptor.truncate(size)

        # Delete unused blocks.
        for block in blocks_deleted:
            self._memory_proxy.write_empty_blocks(block.n + 1, start_from=block.n)

        file_descriptor.update_size()

        self.save(file_descriptor, resolved_path.fs_object_path)
        self._logger.info(
            f"Successfully changed [{path}] size from [{old_size}] to [{size}]."
        )
