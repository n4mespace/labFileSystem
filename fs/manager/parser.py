from argparse import ArgumentParser


def parser_factory() -> ArgumentParser:
    """
    Create arg parser configured for lab.
    """

    parser = ArgumentParser(
        description="Basic manipulation with file system.",
    )

    parser.add_argument(
        "--mkfs",
        action="store",
        type=int,
        default=-1,
        metavar="n",
        help="format FS, with `n` file descriptors.",
    )
    parser.add_argument(
        "--mount", action="store_true", default=False, help="mount FS to storage."
    )
    parser.add_argument(
        "--umount", action="store_true", default=False, help="unmount FS from storage."
    )
    parser.add_argument(
        "--fstat",
        action="store",
        type=int,
        default=-1,
        metavar="id",
        help="print info about descriptor with `id`.",
    )
    parser.add_argument(
        "--ls", action="store_true", default=False, help="list directory content."
    )
    parser.add_argument(
        "--create",
        action="store",
        type=str,
        metavar="name",
        help="create a file, link it to `name`.",
    )
    parser.add_argument(
        "--open",
        action="store",
        type=str,
        metavar="name",
        help="open a file linked with `name`, assign `fd`.",
    )
    parser.add_argument(
        "--close",
        action="store",
        type=str,
        metavar="fd",
        help="close a file linked with corresponding `fd`, delete `fd`.",
    )
    parser.add_argument(
        "--read",
        action="store",
        nargs=3,
        type=str,
        metavar=("fd", "offset", "size"),
        help="read from a file linked with corresponding `fd`. Use offset and size to adjust reading options.",
    )
    parser.add_argument(
        "--write",
        action="store",
        nargs=3,
        type=str,
        metavar=("fd", "offset", "data"),
        help="write to a file linked with corresponding `fd`. Use offset and size to adjust writing options.",
    )
    parser.add_argument(
        "--link",
        action="store",
        nargs=2,
        type=str,
        metavar=("name1", "name2"),
        help="link `name2` with a file which `name1` links.",
    )
    parser.add_argument(
        "--unlink",
        action="store",
        type=str,
        metavar="name",
        help="unlink `name` from a file.",
    )
    parser.add_argument(
        "--truncate",
        action="store",
        nargs=2,
        type=str,
        metavar=("name", "size"),
        help="change size of a file which `name` links to `size`.",
    )

    return parser
