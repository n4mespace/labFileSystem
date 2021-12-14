from fs.commands.base import BaseFSCommand


class UmountCommand(BaseFSCommand):
    def exec(self) -> None:
        self._memory_proxy.delete_memory_file()
        self._system_state.clear_config_file()
        self._system_state.set_mounted(False)
