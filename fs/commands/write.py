from fs.commands.base import BaseFSCommand


class WriteCommand(BaseFSCommand):
    def exec(self) -> None:
        fd, offset, size = self.kwargs["fd"], self.kwargs["offset"], self.kwargs["size"]
