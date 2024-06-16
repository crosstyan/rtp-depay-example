import struct
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional

from loguru import logger
from pydantic import BaseModel


# https://www.iana.org/assignments/rtp-parameters/rtp-parameters.xhtml
class AssignedType(Enum):
    pcmu = 0
    gsm = 3
    g723 = 4
    dvi4_1 = 5
    dvi4_2 = 6
    lpc = 7
    pcma = 8
    g722 = 9
    l16_1 = 10
    l16_2 = 11
    qcelp = 12
    cn = 13
    mpa = 14
    g728 = 15
    dvi4_3 = 16
    dvi4_4 = 17
    g729 = 18
    celb = 25
    jpeg = 26
    nv = 28
    h261 = 31
    mpv = 32
    mp2t = 33
    h263 = 34
    mpeg_ps = 96


PayloadType = AssignedType | int


class RTPHeader(BaseModel):
    version: int
    has_padding: bool
    has_extension: bool
    # https://stackoverflow.com/questions/21775531/csrc-and-ssrc-in-rtp
    csrc_count: int
    is_marker: bool
    payload_type: PayloadType
    sequence_number: int
    timestamp: int
    ssrc: int


OUTPUT_DIR = Path("output")
GRP_DIR = OUTPUT_DIR / "2024-06-15_21-31-32"
PACKET_DIR = GRP_DIR / "packet"
RAW_DIR = GRP_DIR / "frame"

RTP_HEADER_FORMAT = '!BBHII'
RTP_HEADER_SIZE = struct.calcsize(RTP_HEADER_FORMAT)


def decode_rtp_header(packet: bytes):
    if len(packet) < RTP_HEADER_SIZE:
        raise ValueError("Packet is too short to contain a valid RTP header")

    rtp_header = struct.unpack(RTP_HEADER_FORMAT, packet[:RTP_HEADER_SIZE])

    # https://formats.kaitai.io/rtp_packet/index.html
    version = (rtp_header[0] >> 6) & 0x03
    padding = bool((rtp_header[0] >> 5) & 0x01)
    extension = bool((rtp_header[0] >> 4) & 0x01)
    csrc_count = rtp_header[0] & 0x0F
    marker = bool((rtp_header[1] >> 7) & 0x01)
    t = rtp_header[1] & 0x7F
    try:
        payload_type = AssignedType(t)
    except ValueError:
        payload_type = t
    sequence_number = rtp_header[2]
    timestamp = rtp_header[3]
    ssrc = rtp_header[4]

    return RTPHeader(version=version,
                     has_padding=padding,
                     has_extension=extension,
                     csrc_count=csrc_count,
                     is_marker=marker,
                     payload_type=payload_type,
                     sequence_number=sequence_number,
                     timestamp=timestamp,
                     ssrc=ssrc)


def header_length(packet: RTPHeader) -> int:
    return 12 + 4 * packet.csrc_count


def unwrap_rtp(packet: bytes) -> tuple[RTPHeader, bytes]:
    header = decode_rtp_header(packet)
    return header, packet[header_length(header):]


def stream_decode(packets: Iterable[bytes]):
    payload: Optional[bytes] = None
    for packet in packets:
        header, _payload = unwrap_rtp(packet)
        if payload is not None:
            payload += _payload
        else:
            payload = _payload
        if header.is_marker:
            yield payload
            payload = None


def iter_files(pathes: Iterable[Path]):
    for path in pathes:
        with open(path, "rb") as f:
            yield f.read()


def main():
    files: list[Path] = list(PACKET_DIR.glob("*.bin"))
    # sort files by name
    files.sort(key=lambda x: int(x.stem))
    for i, payload in enumerate(stream_decode(iter_files(files))):
        if not RAW_DIR.exists():
            RAW_DIR.mkdir(parents=True)
        with open(RAW_DIR / f"{i}.raw.bin", "wb") as f:
            logger.info("{} frames written", i)
            f.write(payload)


if __name__ == "__main__":
    main()