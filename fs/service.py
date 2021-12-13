import logging

from tabulate import tabulate

from constants import ROOT_DESCRIPTOR_N, ROOT_BLOCK_N, N_BLOCKS_MAX
from fs.config import SystemConfig
from fs.driver.memory import MemoryStorageProxy
from fs.exceptions import FSNotMounted, WrongDescriptorClass, FileAlreadyExists, FSNotFormatted, FileNotExists, \
    FileDescriptorNotExists
from fs.types import DirectoryDescriptor


class FsCommandHandlerService:
    def __init__(self) -> None:
        self._memory_proxy = MemoryStorageProxy()
        self._system_data = SystemConfig()

        self._logger = logging.getLogger(__name__)

    def mkfs(self, n: int) -> None:
        self._logger.info(f"Formatting fs with `{n}` descriptors.")

        if not self._system_data.config.mounted:
            raise FSNotMounted("Can't format fs on unmounted device.")

        self._system_data.init_descriptors(n)
        root = self._memory_proxy.create_directory(
            n=ROOT_DESCRIPTOR_N,
            block_n=ROOT_BLOCK_N,
            name="",
            opened=True,
            parent=None,  # noqa: For root dir we hardcode parent link.
            root=True,
        )
        root.parent = root

        self._system_data.write_descriptor_to_config(root.descriptor, name="")

        with self._memory_proxy as fs:
            fs.clear()
            fs.write(root.descriptor)
            fs.write_empty_blocks(N_BLOCKS_MAX - 1)

        self._logger.info("Successfully formatted.")

    def mount(self) -> None:
        self._memory_proxy.create_memory_file()
        self._system_data.set_mounted(True)

    def umount(self) -> None:
        self._memory_proxy.delete_memory_file()
        self._system_data.set_mounted(False)

    def fstat(self, fid: int) -> None:
        if self._system_data.check_for_descriptor(fid):
            descriptor_blocks = self._system_data.config.descriptors[fid].blocks

            with self._memory_proxy as fs:
                descriptor = fs.get_descriptor(fid, descriptor_blocks)

            self._logger.info(descriptor)

        else:
            self._logger.info(f"There is no such a descriptor: [{fid}].")

    def ls(self) -> None:
        if not self._system_data.config.descriptors:
            raise FSNotFormatted("Can't perform actions on not formatted fs.")

        root_blocks = self._system_data.config.descriptors[ROOT_DESCRIPTOR_N].blocks

        with self._memory_proxy as fs:
            current_directory = fs.get_descriptor(ROOT_DESCRIPTOR_N, root_blocks)

            if not isinstance(current_directory, DirectoryDescriptor):
                raise WrongDescriptorClass("Get wrong descriptor class.")

        links = current_directory.get_directory_links()

        output_headers = ["name", "descriptor", "directory", "refs_count", "size"]
        output_info = []

        for name, descriptor_id in links.items():
            descriptor_blocks = self._system_data.config.descriptors[descriptor_id].blocks

            with self._memory_proxy as fs:
                descriptor = fs.get_descriptor(descriptor_id, descriptor_blocks)

            output_info.append(
                [name, descriptor.n, isinstance(descriptor, DirectoryDescriptor), descriptor.refs_count,
                 descriptor.size]
            )

            # Add also symlinks.
            symlinks = [link for link, descriptor in self._system_data.config.name_to_descriptor.items()
                        if link and descriptor == descriptor_id and name != link]

            for symlink in symlinks:
                output_info.append(
                    [symlink, descriptor.n, isinstance(descriptor, DirectoryDescriptor), descriptor.refs_count,
                     descriptor.size]
                )

        self._logger.info("\n" + tabulate(output_info, headers=output_headers))

    def create(self, name: str) -> None:
        if self._system_data.check_name_exists(name):
            raise FileAlreadyExists("Can't create new file with name of already existing one.")

        n = self._system_data.get_new_descriptor_id()
        root_blocks = self._system_data.config.descriptors[ROOT_DESCRIPTOR_N].blocks

        with self._memory_proxy as fs:
            used_blocks = self._system_data.get_used_blocks()

            block_n = fs.get_available_block(used_blocks)
            current_directory_descriptor = fs.get_descriptor(ROOT_DESCRIPTOR_N, root_blocks)

            if not isinstance(current_directory_descriptor, DirectoryDescriptor):
                raise WrongDescriptorClass("Get wrong descriptor class.")

        file = self._memory_proxy.create_file(
            n=n, block_n=block_n, directory_descriptor=current_directory_descriptor, name=name
        )

        self._system_data.write_descriptor_to_config(file.descriptor, name)

        with self._memory_proxy as fs:
            fs.write(file.descriptor)
            fs.write(current_directory_descriptor)

    def open(self, name: str) -> None:
        descriptor_id = self._system_data.get_descriptor_id(name)

        if not descriptor_id:
            raise FileNotExists("Can't find file with such a name.")

        descriptor_blocks = self._system_data.config.descriptors[descriptor_id].blocks

        fd = self._system_data.map_file_to_fd(name)

        with self._memory_proxy as fs:
            descriptor = fs.get_descriptor(descriptor_id, descriptor_blocks)
            descriptor.opened = True
            fs.write(descriptor)

        self._logger.info(f"Successfully opened file [{name}] with fd [{fd}].")

    def close(self, fd: str) -> None:
        name = self._system_data.get_descriptor_name(fd)

        if not name:
            raise FileDescriptorNotExists("Can't find file with such a file descriptor.")

        descriptor_id = self._system_data.get_descriptor_id(name)

        if not descriptor_id:
            raise FileNotExists("Can't find file with such a name.")

        descriptor_blocks = self._system_data.config.descriptors[descriptor_id].blocks

        self._system_data.unmap_fd_from_name(fd)

        with self._memory_proxy as fs:
            descriptor = fs.get_descriptor(descriptor_id, descriptor_blocks)
            descriptor.opened = False
            fs.write(descriptor)

        self._logger.info(f"Successfully closed file [{name}] with fd [{fd}].")

    def read(self, fd: str, offset: int, size: int) -> None:
        ...

    def write(self, fd: str, offset: int, size: int) -> None:
        ...

    def link(self, name1: str, name2: str) -> None:
        descriptor_id = self._system_data.get_descriptor_id(name1)
        descriptor_blocks = self._system_data.config.descriptors[descriptor_id].blocks

        if descriptor_id:
            with self._memory_proxy as fs:
                descriptor = fs.get_descriptor(descriptor_id, descriptor_blocks)
                fs.add_ref_count(descriptor, 1)

            self._system_data.map_name_to_descriptor(name2, descriptor_id)
            self._logger.info(f"Successfully linked `{name2}` with `{name1}`.")
        else:
            self._logger.info(f"Can't create symlink for non existing file `{name1}`.")

    def unlink(self, name: str) -> None:
        descriptor_id = self._system_data.get_descriptor_id(name)
        descriptor_blocks = self._system_data.config.descriptors[descriptor_id].blocks

        root_blocks = self._system_data.config.descriptors[ROOT_DESCRIPTOR_N].blocks

        if descriptor_id:
            with self._memory_proxy as fs:
                descriptor = fs.get_descriptor(descriptor_id, descriptor_blocks)
                total_refs_count = fs.add_ref_count(descriptor, -1)

                if not total_refs_count:
                    current_directory_descriptor = fs.get_descriptor(ROOT_DESCRIPTOR_N, root_blocks)

                    if not isinstance(current_directory_descriptor, DirectoryDescriptor):
                        raise WrongDescriptorClass("Get wrong descriptor class.")

                    current_directory_descriptor.remove_directory_link(name)
                    fs.write(current_directory_descriptor)

                    self._system_data.remove_descriptor_from_config(descriptor, name)
                else:
                    self._system_data.unmap_name_from_descriptor(name)

            self._logger.info(
                f"Successfully unlinked `{name}` with descriptor `{descriptor_id}`."
            )
        else:
            self._logger.info(f"Can't delete symlink for non existing file `{name}`.")

    def truncate(self, name: str, size: int) -> None:
        ...
