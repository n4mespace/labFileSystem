from collections import Callable

from constants import N_DESCRIPTORS, FILENAME_MAXSIZE_BYTES


def validate_mkfs(n: int, error_cb: Callable[[str], None]) -> int:
    if n > N_DESCRIPTORS:
        error_cb(f"Cannot create FS with more than {N_DESCRIPTORS} descriptor.")

    if n < 1:
        error_cb(f"Cannot create FS with less than 1 descriptor.")

    return n


def validate_read_and_write(
    params: tuple[str, str, str], error_cb: Callable[[str], None]
) -> tuple[str, int, int]:
    fd, offset, size = params
    print(params)

    if int(offset) < 0:
        error_cb("Cannot use offset less than 0.")

    if int(size) < 0:
        error_cb("Cannot use size less than 0.")

    return fd, int(offset), int(size)


def validate_truncate(
    params: tuple[str, str], error_cb: Callable[[str], None]
) -> tuple[str, int]:
    name, size = params

    if int(size) < 0:
        error_cb("Cannot use size less than 0.")

    return name, int(size)


def validate_filename(name: str, error_cb: Callable[[str], None]) -> str:
    if len(name) > FILENAME_MAXSIZE_BYTES:
        error_cb(f"File name length must be less than {FILENAME_MAXSIZE_BYTES}.")

    return name
