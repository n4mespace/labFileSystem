from fs.manager.parser import parser_factory
from fs.manager.validate import (
    validate_mkfs,
    validate_read_and_write,
    validate_truncate, validate_filename,
)
from fs.service import FsCommandHandlerService


class FsManager:
    """
    Logic for input args handling.
    """

    def __init__(self) -> None:
        self.parser = parser_factory()
        self.args = self.parser.parse_args()
        self.fs_handler = FsCommandHandlerService()

    def handle_input(self) -> None:
        """
        Branching logic by input action.
        """
        print(self.args)

        if self.args.mkfs > -1:
            n = validate_mkfs(self.args.mkfs, self.parser.error)
            self.fs_handler.mkfs(n)

        elif self.args.mount:
            self.fs_handler.mount()

        elif self.args.umount:
            self.fs_handler.umount()

        elif self.args.fstat > -1:
            self.fs_handler.fstat(fid=self.args.fstat)

        elif self.args.ls:
            self.fs_handler.ls()

        elif self.args.create:
            filename = validate_filename(self.args.create, self.parser.error)
            self.fs_handler.create(name=filename)

        elif self.args.open:
            filename = validate_filename(self.args.open, self.parser.error)
            self.fs_handler.open(name=filename)

        elif self.args.close:
            self.fs_handler.close(fd=self.args.close)

        elif self.args.read:
            fd, offset, size = validate_read_and_write(
                self.args.read, self.parser.error
            )
            self.fs_handler.read(fd, offset, size)

        elif self.args.write:
            fd, offset, size = validate_read_and_write(
                self.args.write, self.parser.error
            )
            self.fs_handler.write(fd, offset, size)

        elif self.args.link:
            name1, name2 = self.args.link
            self.fs_handler.link(name1, name2)

        elif self.args.unlink:
            self.fs_handler.unlink(self.args.unlink)

        elif self.args.truncate:
            name, size = validate_truncate(self.args.truncate, self.parser.error)
            self.fs_handler.truncate(name, size)
