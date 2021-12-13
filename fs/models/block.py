from dataclasses import asdict, dataclass, field

from constants import BLOCK_CONTENT_SIZE_BYTES, DIRECTORY_MAPPING_BYTES


@dataclass
class Block:
    n: int
    content: bytearray = field(
        default_factory=lambda: bytearray(BLOCK_CONTENT_SIZE_BYTES)
    )

    def write_content(self, content: str, offset: int = 0):
        self.content[offset : offset + len(content)] = [ord(ch) for ch in content]

    def write_link(self, name: str, descriptor_id: int) -> None:
        offset = 0

        for link_mapping_step in range(
            0,
            BLOCK_CONTENT_SIZE_BYTES - DIRECTORY_MAPPING_BYTES,
            DIRECTORY_MAPPING_BYTES,
        ):
            mapping_bytes = self.content[
                link_mapping_step : link_mapping_step + DIRECTORY_MAPPING_BYTES
            ]

            if not any(mapping_bytes):
                offset = link_mapping_step
                break
        # TODO: What if not find offset?

        self.content[offset : offset + len(name)] = [ord(ch) for ch in name]
        self.content[offset + DIRECTORY_MAPPING_BYTES - 1] = descriptor_id

    def get_links(self) -> dict:
        links = {}

        for link_mapping_step in range(
            0,
            BLOCK_CONTENT_SIZE_BYTES - DIRECTORY_MAPPING_BYTES,
            DIRECTORY_MAPPING_BYTES,
        ):
            mapping_bytes = self.content[
                link_mapping_step : link_mapping_step + DIRECTORY_MAPPING_BYTES
            ]

            # Run out of links.
            if not any(mapping_bytes):
                break

            descriptor_id = mapping_bytes[-1]
            name_bytes = mapping_bytes[:-1]
            name = "".join(chr(b) for b in name_bytes if b)

            links[name] = descriptor_id

        return links

    def remove_link(self, name: str) -> None:
        for link_mapping_step in range(
            0,
            BLOCK_CONTENT_SIZE_BYTES - DIRECTORY_MAPPING_BYTES,
            DIRECTORY_MAPPING_BYTES,
        ):
            mapping_bytes = self.content[
                link_mapping_step : link_mapping_step + DIRECTORY_MAPPING_BYTES
            ]

            # Run out of links.
            if not any(mapping_bytes):
                break

            name_bytes = mapping_bytes[:-1]
            link_name = "".join(chr(b) for b in name_bytes if b)

            if name == link_name:
                self.content[
                    link_mapping_step : link_mapping_step + DIRECTORY_MAPPING_BYTES
                ] = [0 for _ in range(DIRECTORY_MAPPING_BYTES)]
                break

    def __repr__(self):
        attrs_str = []

        for k, v in asdict(self).items():
            if k == "content":
                v = list(map(ord, self.content.decode("utf-8")))

            attrs_str.append(f"{k}={v}")

        return f"{type(self).__name__}({', '.join(attrs_str)})"
