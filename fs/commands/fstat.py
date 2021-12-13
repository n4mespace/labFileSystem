from fs.commands.base import BaseFSCommand


class FstatCommand(BaseFSCommand):
    def exec(self) -> None:
        fid = self.kwargs["fid"]

        if self._system_data.check_for_descriptor(fid):
            descriptor_blocks = self._system_data.get_descriptor_blocks(fid)
            descriptor = self._memory_proxy.get_descriptor(fid, descriptor_blocks)

            self._logger.info(descriptor)

        else:
            self._logger.info(f"There is no such a descriptor: [{fid}].")
