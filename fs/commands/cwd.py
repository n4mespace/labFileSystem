from fs.commands.base import BaseFSCommand


class CwdCommand(BaseFSCommand):
    def exec(self) -> None:
        cwd = self._system_state.get_cwd() or "/"
        self._logger.info(f"Current working directory: {cwd}")
