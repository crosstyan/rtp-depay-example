from pydantic import BaseModel, Field, ValidationError
from pathlib import Path
from loguru import logger

OUTPUT_DIR = Path("output")
GRP_DIR = OUTPUT_DIR / "2024-06-16_10-41-13"
PACKET_DIR = GRP_DIR / "packet"
RAW_DIR = GRP_DIR / "frame"


def main():
    files = list(RAW_DIR.glob("*.raw.bin"))

    def sort_key(x: Path):
        xs = x.stem.split(".")
        return int(xs[0])

    files.sort(key=sort_key)

    o = OUTPUT_DIR / "o.265"
    with open(o, "wb") as o:
        HEADER = bytes([0x00, 0x00, 0x01])
        for file in files:
            with open(file, "rb") as f:
                data = f.read()
                name = file.name
                logger.info("Processing {}", name)
                o.write(HEADER + data)

if __name__ == "__main__":
    main()
