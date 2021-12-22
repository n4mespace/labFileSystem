from fs.commands.base import BaseFSCommand


class CdCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]
