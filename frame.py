from pydantic import BaseModel, Field, ValidationError

# see https://datatracker.ietf.org/doc/html/draft-schierl-payload-rtp-h265-01
# NAL unit types in HEVC
#
# Conceptually, both technologies include a video coding layer (VCL),
# and a network abstraction layer (NAL).
TRAIL_N = 0
TRAIL_R = 1
TSA_N = 2
TSA_R = 3
STSA_N = 4
STSA_R = 5
RADL_N = 6
RADL_R = 7
RASL_N = 8
RASL_R = 9
RSV_VCL_N10 = 10
RSV_VCL_R11 = 11
RSV_VCL_N12 = 12
RSV_VCL_R13 = 13
RSV_VCL_N14 = 14
RSV_VCL_R15 = 15
BLA_W_TFD = 16
BLA_W_DLP = 17
BLA_N_LP = 18
IDR_W_LP = 19
IDR_N_LP = 20
CRA_NUT = 21
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
SPS_NUT = 33
PPS_NUT = 34
AUD_NUT = 35
EOS_NUT = 36
EOB_NUT = 37
FD_NUT = 38
PREFIX_SEI_NUT = 39
SUFIX_SEI_NUT = 40
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
# https://www.rfc-editor.org/rfc/rfc7798
# Aggregation Packet Types
# rfc7798 4.4.2 Aggregation Packets
UNSPEC48 = 48
AGG_PKT = 48
# Fragmentation Unit Types
# rfc7798 4.4.3 Fragmentation Units
UNSPEC49 = 49
FRAG_UNIT = 49
# PACI Packet
# rfc7798 4.4.4 PACI Packets
UNSPEC50 = 50
PACI_PKT = 50
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


def can_be_passed_to_decoder(nal_unit_type: int):
    if not 0 <= nal_unit_type <= 63:
        raise ValueError("NAL unit type must be between 0 and 63")
    return 0 <= nal_unit_type <= 47


# Function to determine if a NAL unit type is VCL
def is_vcl(nal_unit_type: int):
    if not 0 <= nal_unit_type <= 63:
        raise ValueError("NAL unit type must be between 0 and 63")
    vcl_types = {
        TRAIL_N, TRAIL_R, TSA_N, TSA_R, STSA_N, STSA_R, RADL_N, RADL_R, RASL_N,
        RASL_R, RSV_VCL_N10, RSV_VCL_R11, RSV_VCL_N12, RSV_VCL_R13, RSV_VCL_N14,
        RSV_VCL_R15, BLA_W_TFD, BLA_W_DLP, BLA_N_LP, IDR_W_LP, IDR_N_LP,
        CRA_NUT, RSV_RAP_VCL22, RSV_RAP_VCL23, RSV_NVCL24, RSV_NVCL25,
        RSV_NVCL26, RSV_NVCL27, RSV_NVCL28, RSV_NVCL29, RSV_NVCL30, RSV_NVCL31
    }
    return nal_unit_type in vcl_types


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
