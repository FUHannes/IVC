# Based on https://en.wikipedia.org/wiki/Exponential-Golomb_coding
#
# The main functionality of this file is decode_signed_bitstream() and
# decode_signed_bytes_bitstream()

from typing import Tuple, List


def encode_unsigned_exponential_golomb(i: int) -> str:
    assert i >= 0
    binary = f"{i+1:b}"
    bit_count = len(binary)
    padding = "0" * (bit_count - 1)
    return padding + binary


def test_encode_unsigned_exponential_golomb():
    assert encode_unsigned_exponential_golomb(0) == "1"
    assert encode_unsigned_exponential_golomb(1) == "010"
    assert encode_unsigned_exponential_golomb(2) == "011"
    assert encode_unsigned_exponential_golomb(3) == "00100"


def encode_signed_exponential_golomb(i: int) -> str:
    if i <= 0:
        mapped = -2 * i
    else:
        mapped = 2 * i - 1
    return encode_unsigned_exponential_golomb(mapped)


def test_encode_exponential_signed_golomb():
    assert encode_signed_exponential_golomb(0) == "1"
    assert encode_signed_exponential_golomb(1) == "010"
    assert encode_signed_exponential_golomb(-1) == "011"
    assert encode_signed_exponential_golomb(2) == "00100"
    assert encode_signed_exponential_golomb(-2) == "00101"
    assert encode_signed_exponential_golomb(-4) == "0001001"


def decode_unsigned_exponential_golomb(s: str) -> Tuple[int, str]:
    binary = s.lstrip("0")
    bit_count = len(s) - len(binary) + 1
    integer_binary, rest_binary = binary[:bit_count], binary[bit_count:]
    i = int(integer_binary, 2)
    return i-1, rest_binary


def decode_signed_exponential_golomb(s: str) -> Tuple[int, str]:
    i, s = decode_unsigned_exponential_golomb(s)
    if i % 2 == 0:
        return -i//2, s
    else:
        return i//2 + 1, s


def decode_signed_bitstream(bitstream: str) -> List[int]:
    ret = []
    while bitstream:
        decoded_i, bitstream = decode_signed_exponential_golomb(bitstream)
        ret.append(decoded_i)
    return ret


def decode_signed_bytes_bitstream(bitstream: bytes) -> List[int]:
    str_bitstream = f"{bitstream:b}"
    return decode_signed_bitstream(bitstream)


def test_golomb_integration_test():
    for i in range(5):
        assert decode_unsigned_exponential_golomb(
            encode_unsigned_exponential_golomb(i)) == (i, "")

    for i in range(-4, 5):
        assert decode_signed_exponential_golomb(
            encode_signed_exponential_golomb(i)) == (i, "")

    r = range(-4, 5)
    bitstream = ""
    for i in r:
        bitstream += encode_signed_exponential_golomb(i)

    assert decode_signed_bitstream(bitstream) == list(r)
