from fs.commands.base import BaseFSCommand


class MountCommand(BaseFSCommand):
    def exec(self) -> None:
        self._memory_proxy.create_memory_file()
        self._system_state.set_mounted(True)
