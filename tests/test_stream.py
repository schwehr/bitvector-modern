"""Tests file and stream I/O methods (read_bits, write_to_file, close)."""

import io
import pathlib

import pytest

from BitVector import BitVector


def test_write_bits_to_stream_object() -> None:
    """Tests writing ASCII bit characters to a text stream object."""
    bv = BitVector.from_bitstring("101100101")
    fp = io.StringIO()
    bv.write_bits_to_stream_object(fp)
    assert fp.getvalue() == "101100101"


def test_write_to_file_raises_error() -> None:
    """Verifies writing a vector not a multiple of 8 bits raises ValueError."""
    bv = BitVector.from_bitstring("10101")
    with pytest.raises(
        ValueError, match="Only a bit vector whose length is a multiple of 8"
    ):
        bv.write_to_file(io.BytesIO())


def test_write_to_file() -> None:
    """Tests writing packed bytes to a binary stream and appending."""
    bv = BitVector.from_bitstring("0100000101000010")  # 'AB'
    out_stream = io.BytesIO()
    bv.write_to_file(out_stream)
    assert out_stream.getvalue() == b"AB"

    bv.write_to_file(out_stream)
    assert out_stream.getvalue() == b"ABAB"


def test_write_bits_to_stream_object_empty() -> None:
    """Tests writing an empty bit vector to a stream."""
    bv = BitVector(size=0)
    fp = io.StringIO()
    bv.write_bits_to_stream_object(fp)
    assert fp.getvalue() == ""


def test_write_bits_to_stream_object_not_multiple_of_8() -> None:
    """Tests writing a vector where length is not a multiple of 8."""
    bv = BitVector.from_bitstring("101")
    fp = io.StringIO()
    bv.write_bits_to_stream_object(fp)
    assert fp.getvalue() == "101"


def test_write_bits_to_stream_object_all_zeros() -> None:
    """Tests writing a vector of all 0s."""
    bv = BitVector(size=10)
    fp = io.StringIO()
    bv.write_bits_to_stream_object(fp)
    assert fp.getvalue() == "0000000000"


def test_write_bits_to_stream_object_all_ones() -> None:
    """Tests writing a vector of all 1s."""
    bv = ~BitVector(size=10)
    fp = io.StringIO()
    bv.write_bits_to_stream_object(fp)
    assert fp.getvalue() == "1111111111"


def test_write_bits_to_stream_object_large() -> None:
    """Tests writing a vector with more than 64 bits."""
    s = "10101010" * 10  # 80 bits
    bv = BitVector.from_bitstring(s)
    fp = io.StringIO()
    bv.write_bits_to_stream_object(fp)
    assert fp.getvalue() == s


def test_from_stream() -> None:
    """Tests reading bytes from an open binary stream."""
    stream = io.BytesIO(b"ABC")
    bv = BitVector.from_stream(stream)
    assert bv == BitVector.from_bytes(b"ABC")


def test_from_stream_partial() -> None:
    """Tests reading a limited number of bytes from a stream."""
    stream = io.BytesIO(b"ABCDE")
    bv = BitVector.from_stream(stream, num_bytes=2)
    assert bv == BitVector.from_bytes(b"AB")
    assert len(bv) == 16


def test_from_stream_empty() -> None:
    """Tests reading from an empty stream."""
    stream = io.BytesIO(b"")
    bv = BitVector.from_stream(stream)
    assert len(bv) == 0
    assert bv == BitVector(size=0)


def test_from_stream_negative_num_bytes() -> None:
    """Tests that a negative num_bytes raises a ValueError."""
    stream = io.BytesIO(b"ABC")
    with pytest.raises(ValueError, match="num_bytes must be non-negative"):
        BitVector.from_stream(stream, num_bytes=-1)


def test_from_file_path(tmp_path: pathlib.Path) -> None:
    """Tests reading bytes from a filesystem path."""
    file_path = tmp_path / "test.bin"
    file_path.write_bytes(b"HELLO")
    bv = BitVector.from_file_path(file_path)
    assert bv == BitVector.from_bytes(b"HELLO")


def test_from_file_path_with_offset_and_limit(
    tmp_path: pathlib.Path,
) -> None:
    """Tests reading from a file path with byte offset and byte limit."""
    file_path = tmp_path / "test_slice.bin"
    file_path.write_bytes(b"0123456789")
    bv = BitVector.from_file_path(file_path, offset_bytes=2, num_bytes=4)
    assert bv == BitVector.from_bytes(b"2345")


def test_from_file_path_negative_offset(
    tmp_path: pathlib.Path,
) -> None:
    """Tests that offset_bytes < 0 raises a ValueError."""
    file_path = tmp_path / "test.bin"
    file_path.write_bytes(b"test")
    with pytest.raises(ValueError, match="offset_bytes must be non-negative"):
        BitVector.from_file_path(file_path, offset_bytes=-5)


def test_from_file_path_negative_num_bytes(
    tmp_path: pathlib.Path,
) -> None:
    """Tests that num_bytes < 0 raises a ValueError when calling from_file_path."""
    file_path = tmp_path / "test.bin"
    file_path.write_bytes(b"test")
    with pytest.raises(ValueError, match="num_bytes must be non-negative"):
        BitVector.from_file_path(file_path, num_bytes=-1)


def test_from_file_path_not_found() -> None:
    """Tests that from_file_path raises FileNotFoundError for nonexistent paths."""
    with pytest.raises(FileNotFoundError):
        BitVector.from_file_path("this_file_does_not_exist_12345.bin")


def test_from_file_path_large(tmp_path: pathlib.Path) -> None:
    """Tests reading a larger binary file from path."""
    file_path = tmp_path / "large.bin"
    data = bytes(i % 256 for i in range(1000))
    file_path.write_bytes(data)
    bv = BitVector.from_file_path(file_path)
    assert bv == BitVector.from_bytes(data)
    assert len(bv) == 8000
