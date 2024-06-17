from pydantic import BaseModel, Field, ValidationError

# see https://datatracker.ietf.org/doc/html/rfc7798#section-1.1.4
# NAL unit types in HEVC
#
# Conceptually, both technologies include a video coding layer (VCL),
# and a network abstraction layer (NAL).
#
# For a reference of all currently defined
# NAL unit types and their semantics, please refer to Section 7.4.2
# in HEVC (https://www.itu.int/rec/T-REC-H.265)
TRAIL_N = 0
"""
Coded slice segment of a non-TSA, non-STSA trailing picture
"""
TRAIL_R = 1
"""
Coded slice segment of a non-TSA, non-STSA trailing picture
"""
TSA_N = 2
"""
Coded slice segment of a TSA picture
"""
TSA_R = 3
"""
Coded slice segment of a TSA picture
"""
STSA_N = 4
"""
Coded slice segment of a STSA picture
"""
STSA_R = 5
"""
Coded slice segment of a STSA picture
"""
RADL_N = 6
"""
Coded slice segment of a RADL picture
"""
RADL_R = 7
"""
Coded slice segment of a RADL picture
"""
RASL_N = 8
"""
Coded slice segment of a RASL picture
"""
RASL_R = 9
"""
Coded slice segment of a RASL picture
"""
RSV_VCL_N10 = 10
RSV_VCL_R11 = 11
RSV_VCL_N12 = 12
RSV_VCL_R13 = 13
RSV_VCL_N14 = 14
RSV_VCL_R15 = 15
BLA_W_TFD = 16
"""
Coded slice segment of a BLA picture
"""
BLA_W_DLP = 17
"""
Coded slice segment of a BLA picture
"""
BLA_N_LP = 18
"""
Coded slice segment of a BLA picture
"""
IDR_W_LP = 19
"""
Coded slice segment of an IDR picture
"""
IDR_N_LP = 20
"""
Coded slice segment of an IDR picture
"""
CRA_NUT = 21
"""
Coded slice segment of a CRA picture
"""
RSV_RAP_VCL22 = 22
RSV_RAP_VCL23 = 23
RSV_NVCL24 = 24
RSV_NVCL25 = 25
RSV_NVCL26 = 26
RSV_NVCL27 = 27
RSV_NVCL28 = 28
RSV_NVCL29 = 29
RSV_NVCL30 = 30
RSV_NVCL31 = 31
VPS_NUT = 32
"""
Video parameter set
"""
SPS_NUT = 33
"""
Sequence parameter set
"""
PPS_NUT = 34
"""
Picture parameter set
"""
AUD_NUT = 35
"""
Access unit delimiter
"""
EOS_NUT = 36
"""
End of sequence
"""
EOB_NUT = 37
"""
End of bitstream
"""
FD_NUT = 38
"""
Filler data
"""
PREFIX_SEI_NUT = 39
"""
Supplemental enhancement information
"""
SUFIX_SEI_NUT = 40
"""
Supplemental enhancement information
"""
RSV_NVCL41 = 41
RSV_NVCL42 = 42
RSV_NVCL43 = 43
RSV_NVCL44 = 44
RSV_NVCL45 = 45
RSV_NVCL46 = 46
RSV_NVCL47 = 47
#
# NAL units with NAL unit type values in the range of 0 to 47,
# inclusive, may be passed to the decoder.  NAL-unit-like structures
# with NAL unit type values in the range of 48 to 63, inclusive, MUST
# NOT be passed to the decoder.
#
#
UNSPEC48 = 48
AGG_PKT = 48
"""
Aggregation Packet

https://datatracker.ietf.org/doc/html/rfc7798#section-4.4.2
"""
UNSPEC49 = 49
FRAG_UNIT = 49
"""
Fragmentation Unit

https://datatracker.ietf.org/doc/html/rfc7798#section-4.4.3
"""
UNSPEC50 = 50
PACI_PKT = 50
"""
PACI Packet

https://datatracker.ietf.org/doc/html/rfc7798#section-4.4.4
"""
# ...
UNSPEC51 = 51
UNSPEC52 = 52
UNSPEC53 = 53
UNSPEC54 = 54
UNSPEC55 = 55
UNSPEC56 = 56
UNSPEC57 = 57
UNSPEC58 = 58
UNSPEC59 = 59
UNSPEC60 = 60
UNSPEC61 = 61
UNSPEC62 = 62
UNSPEC63 = 63


def nal_unit_type_to_string(nal_unit_type: int):
    nal_unit_types = {
        0: "TRAIL_N",
        1: "TRAIL_R",
        2: "TSA_N",
        3: "TSA_R",
        4: "STSA_N",
        5: "STSA_R",
        6: "RADL_N",
        7: "RADL_R",
        8: "RASL_N",
        9: "RASL_R",
        16: "BLA_W_TFD",
        17: "BLA_W_DLP",
        18: "BLA_N_LP",
        19: "IDR_W_LP",
        20: "IDR_N_LP",
        21: "CRA_NUT",
        32: "VPS_NUT",
        33: "SPS_NUT",
        34: "PPS_NUT",
        35: "AUD_NUT",
        36: "EOS_NUT",
        37: "EOB_NUT",
        38: "FD_NUT",
        39: "PREFIX_SEI_NUT",
        40: "SUFIX_SEI_NUT",
        48: "AGG_PKT",
        49: "FRAG_UNIT",
        50: "PACI_PKT"
    }

    return nal_unit_types.get(nal_unit_type, None)


def can_be_passed_to_decoder(nal_unit_type: int):
    if not 0 <= nal_unit_type <= 63:
        raise ValueError("NAL unit type must be between 0 and 63")
    return 0 <= nal_unit_type <= 47


def is_vcl(nal_unit_type: int):
    """
    If the most significant bit of this field
    of a NAL unit is equal to 0 (i.e., the value of this field is less
    than 32), the NAL unit is a VCL NAL unit.  Otherwise, the NAL unit
    is a non-VCL NAL unit.
    """
    if not 0 <= nal_unit_type <= 63:
        raise ValueError("NAL unit type must be between 0 and 63")
    msb = (nal_unit_type >> 5) & 0x01
    return msb == 0


class NetworkAbstractLayerHevc(BaseModel):
    """
    Describes the Network Abstraction Layer (NAL) like header.
    """

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
    nuh_temporal_id_plus_one: int = Field(..., gt=0, le=7)
    """
    3 bit
    """

    @staticmethod
    def unmarshal(data: bytes) -> "NetworkAbstractLayerHevc":
        if len(data) < 2:
            raise ValueError("NAL header must be at least 2 bytes long")
        forbidden_zero_bit = bool((data[0] >> 7) & 0x01)
        if forbidden_zero_bit:
            raise ValueError(
                "Forbidden zero bit is not zero, expected to be zero")
        nal_unit_type = (data[0] >> 1) & 0x3F
        nuh_layer_id = ((data[0] & 0x01) << 5) | ((data[1] >> 3) & 0x1F)
        # Required to be equal to zero in HEVC
        if nuh_layer_id != 0:
            raise ValueError("nuh_layer_id is not zero")
        nuh_temporal_id_plus_one = data[1] & 0x07
        # A TID value of 0 is illegal to ensure that there is at least
        # one bit in the NAL unit header equal to 1
        if nuh_temporal_id_plus_one == 0:
            raise ValueError("nuh_temporal_id_plus1 is zero")

        return NetworkAbstractLayerHevc(
            forbidden_zero_bit=forbidden_zero_bit,
            nal_unit_type=nal_unit_type,
            nuh_layer_id=nuh_layer_id,
            nuh_temporal_id_plus_one=nuh_temporal_id_plus_one,
        )

    def marshal(self) -> bytes:
        data = bytearray(2)
        data[0] = (int(self.forbidden_zero_bit) << 7) | (
            (self.nal_unit_type & 0x3F) << 1) | (self.nuh_layer_id >> 5)
        data[1] = ((self.nuh_layer_id & 0x1F) << 3) | (
            self.nuh_temporal_id_plus_one & 0x07)
        return bytes(data)
