# Block wide.
N_BLOCKS_MAX = 100
ROOT_BLOCK_N = 0
BLOCK_SIZE_BYTES = 64
BLOCK_HEADER_SIZE_BYTES = 8
BLOCK_CONTENT_SIZE_BYTES = BLOCK_SIZE_BYTES - BLOCK_HEADER_SIZE_BYTES

# Descriptors wide.
ROOT_DESCRIPTOR_N = 0
ROOT_DIRECTORY_PATH = ""
N_DESCRIPTORS = 10
FD_GENERATION_RANGE = (100, 999)

# Files wide.
FILENAME_MAXSIZE_BYTES = 10
DIRECTORY_MAPPING_BYTES = FILENAME_MAXSIZE_BYTES + 1  # +1 for descriptor id.

# Symlinks wide.
MAX_SYMLINK_HOPS = 10

# Filesystem wide.
PATH_DIVIDER = "/"
DIRECTORY_DEFAULT_LINKS_COUNT = 2
MEMORY_PATH = "fake_memory.mem"
CONFIG_PATH = "system_config.json"
