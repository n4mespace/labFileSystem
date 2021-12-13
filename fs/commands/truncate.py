from fs.commands.base import BaseFSCommand


class TruncateCommand(BaseFSCommand):
    def exec(self) -> None:
        name, size = self.kwargs["name"], self.kwargs["size"]
