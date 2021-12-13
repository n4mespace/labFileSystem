#!/usr/bin/env python3

import logging

from fs.manager.cli import FsManager

logging.basicConfig(format="[fs] %(name)-30s %(message)s", level=logging.INFO)


def main() -> None:
    """
    Program entry point.
    """

    manager = FsManager()
    manager.handle_input()


if __name__ == "__main__":
    main()
