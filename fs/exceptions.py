class FSAlreadyMounted(Exception):
    """
    Can't mount new FS till current is unmounted.
    """

    pass


class FileNotExists(Exception):
    """
    Can't find file with such a name.
    """

    pass


class FileDescriptorNotExists(Exception):
    """
    Can't find file with such a file descriptor.
    """

    pass


class FileAlreadyExists(Exception):
    """
    Can't create new file with name of already existing one.
    """

    pass


class FSNotMounted(Exception):
    """
    Can't unmount new FS till one is not mounted.
    """

    pass


class FSNotFormatted(Exception):
    """
    Can't perform actions on not formatted fs.
    """

    pass


class OutOfDescriptors(Exception):
    """
    System run out of available descriptors.
    """

    pass


class OutOfBlocks(Exception):
    """
    System run out of available blocks.
    """

    pass


class WrongDescriptorClass(Exception):
    """
    Get wrong descriptor class.
    """

    pass


class BlockWriteDenied(Exception):
    """
    Something went wrong writing a block to memory.
    """

    pass
