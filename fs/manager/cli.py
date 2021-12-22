from typing import Type

from fs.commands.base import BaseFSCommand
from fs.commands.cd import CdCommand
from fs.commands.close import CloseCommand
from fs.commands.create import CreateCommand
from fs.commands.fstat import FstatCommand
from fs.commands.link import LinkCommand
from fs.commands.ls import LsCommand
from fs.commands.mkdir import MkdirCommand
from fs.commands.mkfs import MkfsCommand
from fs.commands.mount import MountCommand
from fs.commands.open import OpenCommand
from fs.commands.read import ReadCommand
from fs.commands.rmdir import RmdirCommand
from fs.commands.symlink import SymlinkCommand
from fs.commands.truncate import TruncateCommand
from fs.commands.umount import UmountCommand
from fs.commands.unlink import UnlinkCommand
from fs.commands.write import WriteCommand
from fs.manager.parser import parser_factory
from fs.manager.validate import (validate_mkfs, validate_path, validate_read,
                                 validate_symlink, validate_truncate,
                                 validate_write)


class FsManager:
    """
    Logic for input args handling.
    """

    commands: dict[str, Type[BaseFSCommand]] = {
        "mkfs": MkfsCommand,
        "mount": MountCommand,
        "umount": UmountCommand,
        "fstat": FstatCommand,
        "create": CreateCommand,
        "ls": LsCommand,
        "open": OpenCommand,
        "close": CloseCommand,
        "read": ReadCommand,
        "write": WriteCommand,
        "link": LinkCommand,
        "unlink": UnlinkCommand,
        "truncate": TruncateCommand,
        "mkdir": MkdirCommand,
        "rmdir": RmdirCommand,
        "cd": CdCommand,
        "symlink": SymlinkCommand,
    }

    def __init__(self) -> None:
        self.parser = parser_factory()
        self.args = self.parser.parse_args()

    def handle_input(self) -> None:
        """
        Branching logic by input action.
        """

        if self.args.mkfs > -1:
            n = validate_mkfs(self.args.mkfs, self.parser.error)
            self.commands["mkfs"](n=n).exec()

        elif self.args.mount:
            self.commands["mount"]().exec()

        elif self.args.umount:
            self.commands["umount"]().exec()

        elif self.args.fstat > -1:
            self.commands["fstat"](fid=self.args.fstat).exec()

        elif self.args.ls:
            self.commands["ls"]().exec()

        elif self.args.create:
            filepath = validate_path(self.args.create, self.parser.error)
            self.commands["create"](path=filepath).exec()

        elif self.args.open:
            filepath = validate_path(self.args.open, self.parser.error)
            self.commands["open"](path=filepath).exec()

        elif self.args.close:
            self.commands["close"](fd=self.args.close).exec()

        elif self.args.read:
            fd, offset, size = validate_read(self.args.read, self.parser.error)
            self.commands["read"](fd=fd, offset=offset, size=size).exec()

        elif self.args.write:
            fd, offset, content = validate_write(self.args.write, self.parser.error)
            self.commands["write"](fd=fd, offset=offset, content=content).exec()

        elif self.args.link:
            path1, path2 = self.args.link
            self.commands["link"](path1=path1, path2=path2).exec()

        elif self.args.unlink:
            self.commands["unlink"](path=self.args.unlink).exec()

        elif self.args.truncate:
            path, size = validate_truncate(self.args.truncate, self.parser.error)
            self.commands["truncate"](path=path, size=size).exec()

        elif self.args.mkdir:
            self.commands["mkdir"](path=self.args.mkdir).exec()

        elif self.args.rmdir:
            self.commands["rmdir"](path=self.args.rmdir).exec()

        elif self.args.cd:
            self.commands["cd"](path=self.args.cd).exec()

        elif self.args.symlink:
            content, path = validate_symlink(self.args.symlink, self.parser.error)
            self.commands["symlink"](content=content, path=path).exec()
