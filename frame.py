from pydantic import BaseModel, Field, ValidationError
from pathlib import Path
from loguru import logger


class HEVCNALHeader(BaseModel):
    forbidden_zero_bit: bool
    """
    1 bit
    """
    nal_unit_type: int = Field(..., ge=0, le=63)
    """
    6 bit
    """
    nuh_layer_id: int = Field(..., ge=0, le=63)
    """
    6 bit
    """
    nuh_temporal_id_plus1: int = Field(..., gt=0, le=7)
    """
    3 bit
    """

    @staticmethod
    def from_bytes(data: bytes) -> "HEVCNALHeader":
        if len(data) < 2:
            raise ValueError("NAL header must be at least 2 bytes long")
        forbidden_zero_bit = bool((data[0] >> 7) & 0x01)
        if forbidden_zero_bit:
            raise ValueError(
                "Forbidden zero bit is not zero, expected to be zero")
        nal_unit_type = (data[0] >> 1) & 0x3F
        nuh_layer_id = ((data[0] & 0x01) << 5) | ((data[1] >> 3) & 0x1F)
        nuh_temporal_id_plus1 = data[1] & 0x07

        return HEVCNALHeader(forbidden_zero_bit=forbidden_zero_bit,
                             nal_unit_type=nal_unit_type,
                             nuh_layer_id=nuh_layer_id,
                             nuh_temporal_id_plus1=nuh_temporal_id_plus1)


OUTPUT_DIR = Path("output")
GRP_DIR = OUTPUT_DIR / "2024-06-15_21-31-32"
PACKET_DIR = GRP_DIR / "packet"
RAW_DIR = GRP_DIR / "frame"


def main():
    files = list(RAW_DIR.glob("*.raw.bin"))

    def sort_key(x: Path):
        xs = x.stem.split(".")
        return int(xs[0])

    files.sort(key=sort_key)
    for file in files:
        with open(file, "rb") as f:
            data = f.read()
        try:
            name = file.name
            nal_header = HEVCNALHeader.from_bytes(data)
            logger.info("{} header: {}", name, nal_header)
        except ValidationError as e:
            logger.error("{} validation error: {}", name, e)
        except ValueError as e:
            logger.error("{} error: {}", name, e)


if __name__ == "__main__":
    main()
