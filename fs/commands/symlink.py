from fs.commands.base import BaseFSCommand


class SymlinkCommand(BaseFSCommand):
    def exec(self) -> None:
        contetn, path = self.kwargs["content"], self.kwargs["path"]
