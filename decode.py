import struct
from enum import Enum
from pathlib import Path
from token import OP
from typing import Generator, Iterable, Optional, Any

from os import PathLike
import click
from loguru import logger
from pydantic import BaseModel, Field
from serve import CatHeader
from frame import AGG_PKT, FRAG_UNIT, PACI_PKT, NetworkAbstractLayerHevc, can_be_passed_to_decoder, nal_unit_type_to_string


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


class AggregationPacketHeader(BaseModel):
    """
    https://datatracker.ietf.org/doc/html/rfc7798#section-4.4.2

    An AP MUST carry at least two aggregation units and can carry as many
    aggregation units as necessary; however, the total amount of data in
    an AP obviously MUST fit into an IP packet, and the size SHOULD be
    chosen so that the resulting IP packet is smaller than the MTU size
    so to avoid IP layer fragmentation.

    I don't think I would handle a conditional 8-bit DONL and 8-bit DOND,
    whose meaning are not clear to me.
    """
    nalu_size: int = Field(...,
                           description="Size of the NAL unit in bytes",
                           ge=1,
                           le=65535)


# https://datatracker.ietf.org/doc/html/rfc6185#section-6.1
# NOTE: sprop-max-don-diff
class FragmentUnitHeader(BaseModel):
    """
    https://datatracker.ietf.org/doc/html/rfc7798#section-4.4.3

    The FU payload consists of fragments of the payload of the fragmented
    NAL unit so that if the FU payloads of consecutive FUs, starting with
    an FU with the S bit equal to 1 and ending with an FU with the E bit
    equal to 1, are sequentially concatenated, the payload of the
    fragmented NAL unit can be reconstructed.  
    
    The NAL unit header of the fragmented NAL unit is not included as such in
    the FU payload, but rather the information of the NAL unit header of the
    fragmented NAL unit is conveyed in F, LayerId, and TID fields of the FU
    payload headers of the FUs and the FuType field of the FU header of the FUs.
    """
    S: bool
    """
    1 bit
    """
    E: bool
    """
    1 bit
    """
    unit_type: int
    """
    6 bit
    """

    @staticmethod
    def unmarshal(b: bytes):
        assert len(b) >= 1
        return FragmentUnitHeader(S=bool(b[0] & 0x80),
                                  E=bool(b[0] & 0x40),
                                  unit_type=b[0] & 0x1F)


def parse_fu(b: bytes):
    assert len(b) >= 4
    payload_hdr = NetworkAbstractLayerHevc.unmarshal(b[:2])
    assert payload_hdr.nal_unit_type == FRAG_UNIT
    FU_header = FragmentUnitHeader.unmarshal(b[2:3])
    return FU_header, b[3:]


class FragmentAssembler:
    """
    Assemble fragmented NAL units
    """
    _data: Optional[bytes] = None
    _first_header: Optional[FragmentUnitHeader] = None

    def __init__(self, data: bytes):
        h, r = parse_fu(data)
        assert h.S
        self._first_header = h
        self._data = r

    def reset(self):
        self._data = None
        self._first_header = None

    def next(self, data: bytes):
        assert self._data is not None
        assert self._first_header is not None
        h, r = parse_fu(data)
        assert not h.S
        self._data += r
        if h.E:
            h = self._first_header
            d = self._data
            self.reset()
            return h, d
        return None


NalLike = FragmentUnitHeader | NetworkAbstractLayerHevc


def parse_parse(data: bytes) -> Generator[tuple[NalLike, bytes], Any, None]:
    """
    This parser can't handle missing packets or packets that are not in order.

    Since it won't analyze the RTP header (which contains the timestamp and sequence number),
    timestamps are also discarded.

    This parser ignore all of the DONL and DOND fields, whose meaning are not clear to me.

    ffmpeg complains about the missing timestamps:

    > Timestamps are unset in a packet for stream 0. This is deprecated and will
    stop working in the future. Fix your code to set the timestamps properly
    """
    asm: Optional[FragmentAssembler] = None
    asm_s_idx: Optional[int] = None
    for i, cat in enumerate(CatHeader.iter_stream(data)):
        h, b = unwrap_rtp(cat)
        nal_header = NetworkAbstractLayerHevc.unmarshal(b[:2])
        if nal_header.nal_unit_type == FRAG_UNIT:
            if asm is None:
                asm = FragmentAssembler(b)
                asm_s_idx = i
            else:
                r = asm.next(b)
                if r is not None:
                    assert asm_s_idx is not None
                    h, b = r
                    suffix = f"({n})" if (n := nal_unit_type_to_string(
                        h.unit_type)) else ""
                    logger.debug(
                        f"{asm_s_idx}-{i} fragmented NAL unit: {len(b)} bytes with type {h.unit_type} {suffix}"
                    )
                    asm = None
                    asm_s_idx = None
                    yield h, b
        elif nal_header.nal_unit_type == AGG_PKT:
            logger.warning(f"{i} aggregation packet: {len(b)} bytes")
            raise NotImplementedError("Aggregation packet is not supported")
        elif nal_header.nal_unit_type == PACI_PKT:
            logger.warning(f"{i} PACI packet: {len(b)} bytes")
            raise NotImplementedError("PACI packet is not supported")
        else:
            suffix = f"({n})" if (n := nal_unit_type_to_string(
                nal_header.nal_unit_type)) else ""
            logger.debug(
                f"{i} single NAL unit {len(b)} bytes with type {nal_header.nal_unit_type} {suffix}"
            )
            yield nal_header, b


HEVC_NAL_MAGIC = bytes([0x00, 0x00, 0x01])


@click.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.option("-o",
              "--output",
              type=click.Path(file_okay=True),
              default="output.h265")
@click.option("--overwrite", is_flag=True)
def parse_cat(input_file: PathLike, output: PathLike, overwrite: bool = False):
    with open(input_file, "rb") as f:
        data = f.read()
    op = Path(output)
    if op.exists() and not overwrite:
        raise FileExistsError(
            f"{op} already exists, use `--overwrite` to overwrite it")
    with open(output, "wb") as o:
        for h, b in parse_parse(data):
            if isinstance(h, FragmentUnitHeader):
                # the assembled payload won't include the NAL header
                dummy_nal = NetworkAbstractLayerHevc(
                    forbidden_zero_bit=False,
                    nal_unit_type=h.unit_type,
                    nuh_layer_id=0,
                    nuh_temporal_id_plus_one=1,
                )
                o.write(HEVC_NAL_MAGIC + dummy_nal.marshal() + b)
            elif isinstance(h, NetworkAbstractLayerHevc):
                o.write(HEVC_NAL_MAGIC + b)
            else:
                raise ValueError(f"Unknown header type {type(h)}")


if __name__ == "__main__":
    parse_cat()  # pylint: disable=no-value-for-parameter
