"""Tests file and stream I/O methods (read_bits, write_to_file, close)."""

import io

import pytest

import BitVector


def test_write_bits_to_stream_object() -> None:
    """Tests writing ASCII bit characters to a text stream object."""
    bv = BitVector.BitVector.from_bitstring("101100101")
    fp = io.StringIO()
    bv.write_bits_to_stream_object(fp)
    assert fp.getvalue() == "101100101"


def test_write_to_file_raises_error() -> None:
    """Verifies writing a vector not a multiple of 8 bits raises ValueError."""
    bv = BitVector.BitVector.from_bitstring("10101")
    with pytest.raises(
        ValueError, match="Only a bit vector whose length is a multiple of 8"
    ):
        bv.write_to_file(io.BytesIO())


def test_write_to_file() -> None:
    """Tests writing packed bytes to a binary stream and appending."""
    bv = BitVector.BitVector.from_bitstring("0100000101000010")  # 'AB'
    out_stream = io.BytesIO()
    bv.write_to_file(out_stream)
    assert out_stream.getvalue() == b"AB"

    bv.write_to_file(out_stream)
    assert out_stream.getvalue() == b"ABAB"


def test_write_bits_to_stream_object_empty() -> None:
    """Tests writing an empty bit vector to a stream."""
    bv = BitVector.BitVector(size=0)
    fp = io.StringIO()
    bv.write_bits_to_stream_object(fp)
    assert fp.getvalue() == ""


def test_write_bits_to_stream_object_not_multiple_of_8() -> None:
    """Tests writing a vector where length is not a multiple of 8."""
    bv = BitVector.BitVector.from_bitstring("101")
    fp = io.StringIO()
    bv.write_bits_to_stream_object(fp)
    assert fp.getvalue() == "101"


def test_write_bits_to_stream_object_all_zeros() -> None:
    """Tests writing a vector of all 0s."""
    bv = BitVector.BitVector(size=10)
    fp = io.StringIO()
    bv.write_bits_to_stream_object(fp)
    assert fp.getvalue() == "0000000000"


def test_write_bits_to_stream_object_all_ones() -> None:
    """Tests writing a vector of all 1s."""
    bv = ~BitVector.BitVector(size=10)
    fp = io.StringIO()
    bv.write_bits_to_stream_object(fp)
    assert fp.getvalue() == "1111111111"
