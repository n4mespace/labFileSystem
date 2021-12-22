from fs.commands.base import BaseFSCommand


class MkdirCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]
