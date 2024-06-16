import socket
from anyio import create_udp_socket, run, open_file
from datetime import datetime
from pathlib import Path
from loguru import logger

OUTPUT_DIR_PATH = Path("output")
PORT = 5600
HOST = "0.0.0.0"


async def main():
    if not OUTPUT_DIR_PATH.exists():
        logger.info(f"Creating output directory: {OUTPUT_DIR_PATH}")
        OUTPUT_DIR_PATH.mkdir()
    logger.info(f"Listening on {HOST}:{PORT}")
    async with await create_udp_socket(family=socket.AF_INET,
                                       local_host=HOST,
                                       local_port=PORT) as udp:
        i = 0
        now = datetime.now()
        OUTPUT_GRP_PATH = OUTPUT_DIR_PATH / now.strftime("%Y-%m-%d_%H-%M-%S") / "packet"
        async for packet, (host, port) in udp:
            # dump to file
            if not OUTPUT_GRP_PATH.exists():
                logger.info(
                    f"Creating output group directory: {OUTPUT_GRP_PATH}")
                OUTPUT_GRP_PATH.mkdir(parents=True)
            i += 1
            file_path = OUTPUT_GRP_PATH / f"{i}.bin"
            logger.info(
                f"Received {len(packet)} bytes from {host}:{port} as index {i}")
            async with await open_file(file_path, "wb") as f:
                await f.write(packet)


if __name__ == "__main__":
    try:
        run(main)
    except KeyboardInterrupt:
        ...
