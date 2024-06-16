import socket
from anyio import create_udp_socket, run, open_file
from datetime import datetime
from pathlib import Path
from loguru import logger
from pydantic import BaseModel
import struct

OUTPUT_DIR_PATH = Path("output")
PORT = 5600
HOST = "0.0.0.0"

MAGIC = bytes(map(ord, "cat"))


class CatHeader(BaseModel):
    length: int  # uint32_t

    @staticmethod
    def needed_bytes():
        return len(MAGIC) + 4

    @staticmethod
    def unpack_cat(data: bytes):
        SZ = CatHeader.needed_bytes()
        magic, length = struct.unpack(f"!{len(MAGIC)}sI", data[:SZ])
        assert magic == MAGIC
        return data[SZ:SZ + length], data[SZ + length:]

    @staticmethod
    def iter_stream(data: bytes):
        while len(data) >= CatHeader.needed_bytes():
            data, rest = CatHeader.unpack_cat(data)
            yield data
            data = rest

    @staticmethod
    def pack_with_cat(data: bytes):
        return MAGIC + struct.pack("!I", len(data)) + data


async def main():
    if not OUTPUT_DIR_PATH.exists():
        logger.info(f"Creating output directory: {OUTPUT_DIR_PATH}")
        OUTPUT_DIR_PATH.mkdir()
    logger.info(f"Listening on {HOST}:{PORT}")
    async with await create_udp_socket(family=socket.AF_INET,
                                       local_host=HOST,
                                       local_port=PORT) as udp:
        now = datetime.now()
        OUTPUT_GRP_DIR_PATH = OUTPUT_DIR_PATH / now.strftime(
            "%Y-%m-%d_%H-%M-%S")
        i = 0
        if not OUTPUT_GRP_DIR_PATH.exists():
            logger.info(
                f"Creating output group directory: {OUTPUT_GRP_DIR_PATH}")
            OUTPUT_GRP_DIR_PATH.mkdir()
        with open(OUTPUT_GRP_DIR_PATH / "cat.bin", "wb") as f:
            async for packet, (host, port) in udp:
                logger.info(
                    f"Received {len(packet)} bytes from {host}:{port} at {i}")
                f.write(CatHeader.pack_with_cat(packet))
                i += 1


if __name__ == "__main__":
    try:
        run(main)
    except KeyboardInterrupt:
        ...
