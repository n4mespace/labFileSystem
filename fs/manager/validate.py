from collections import Callable

from constants import FILENAME_MAXSIZE_BYTES, N_DESCRIPTORS, PATH_DIVIDER


def validate_path(path: str, error_cb: Callable[[str], None]) -> str:
    if len(path.split(PATH_DIVIDER)[-1]) > FILENAME_MAXSIZE_BYTES:
        error_cb(f"File name length must be less than {FILENAME_MAXSIZE_BYTES}.")

    if not all(path.split(PATH_DIVIDER)):
        error_cb("File path is incorrect.")

    return path


def validate_mkfs(n: int, error_cb: Callable[[str], None]) -> int:
    if n > N_DESCRIPTORS:
        error_cb(f"Cannot create FS with more than {N_DESCRIPTORS} descriptor.")

    if n < 1:
        error_cb(f"Cannot create FS with less than 1 descriptor.")

    return n


def validate_read(
    params: tuple[str, str, str], error_cb: Callable[[str], None]
) -> tuple[str, int, int]:
    fd, offset, size = params

    if int(offset) < 0:
        error_cb("Cannot use offset less than 0.")

    if int(size) <= 0:
        error_cb("Cannot use size less than 1.")

    return fd, int(offset), int(size)


def validate_write(
    params: tuple[str, str, str], error_cb: Callable[[str], None]
) -> tuple[str, int, str]:
    fd, offset, content = params

    if int(offset) < 0:
        error_cb("Cannot use offset less than 0.")

    return fd, int(offset), content


def validate_truncate(
    params: tuple[str, str], error_cb: Callable[[str], None]
) -> tuple[str, int]:
    path, size = params

    path = validate_path(path, error_cb)

    if int(size) < 0:
        error_cb("Cannot use size less than 0.")

    return path, int(size)


def validate_symlink(
    params: tuple[str, str], error_cb: Callable[[str], None]
) -> tuple[str, str]:
    content, path = params

    path = validate_path(path, error_cb)
    content = validate_path(content, error_cb)

    return content, path
