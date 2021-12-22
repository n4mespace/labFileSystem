from fs.commands.base import BaseFSCommand


class RmdirCommand(BaseFSCommand):
    def exec(self) -> None:
        path = self.kwargs["path"]
