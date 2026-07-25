"""Tests for string output representations (ASCII, hex, and str) of BitVector."""

import pytest

import BitVector


@pytest.mark.parametrize(
    ("bitstring", "expected"),
    [
        ("01000001", "A"),
        ("", ""),
    ],
)
def test_get_bitvector_in_ascii(bitstring: str, expected: str) -> None:
    """Tests ASCII string conversion across valid BitVector instances.

    Args:
        bitstring: Input binary string.
        expected: The expected ASCII representation string.
    """
    bv = BitVector.BitVector.from_bitstring(bitstring)
    assert bv.get_bitvector_in_ascii() == expected


def test_get_bitvector_in_ascii_from_string() -> None:
    """Tests ASCII string conversion when initialized via from_string."""
    bv = BitVector.BitVector.from_string("hello")
    assert bv.get_bitvector_in_ascii() == "hello"


@pytest.mark.parametrize("bitstring", ["1", "101", "10101", "1010101"])
def test_get_bitvector_in_ascii_invalid_length_raises_error(bitstring: str) -> None:
    """Verifies that non-multiple-of-8 lengths raise ValueError in ASCII export.

    Args:
        bitstring: A bitstring whose length is not a multiple of 8.
    """
    bv = BitVector.BitVector.from_bitstring(bitstring)
    with pytest.raises(ValueError, match="must be an integral multiple of 8 bits"):
        bv.get_bitvector_in_ascii()


@pytest.mark.parametrize(
    ("bitstring", "expected"),
    [
        ("1111", "f"),
        ("10100000", "a0"),
        ("", ""),
    ],
)
def test_get_bitvector_in_hex(bitstring: str, expected: str) -> None:
    """Tests hexadecimal string conversion across valid BitVector instances.

    Args:
        bitstring: Input binary string.
        expected: The expected hexadecimal representation string.
    """
    bv = BitVector.BitVector.from_bitstring(bitstring)
    assert bv.get_bitvector_in_hex() == expected


def test_get_bitvector_in_hex_from_hex() -> None:
    """Tests hexadecimal string conversion when initialized via from_hex."""
    bv = BitVector.BitVector.from_hex("68656c6c6f")
    assert bv.get_bitvector_in_hex() == "68656c6c6f"


@pytest.mark.parametrize("bitstring", ["1", "101", "100001"])
def test_get_bitvector_in_hex_invalid_length_raises_error(bitstring: str) -> None:
    """Verifies that non-multiple-of-4 lengths raise ValueError in hex export.

    Args:
        bitstring: A bitstring whose length is not a multiple of 4.
    """
    bv = BitVector.BitVector.from_bitstring(bitstring)
    with pytest.raises(ValueError, match="must be an integral multiple of 4 bits"):
        bv.get_bitvector_in_hex()


@pytest.mark.parametrize(
    ("bitstring", "expected"),
    [
        ("01010111", "01010111"),
        ("", ""),
    ],
)
def test_str_representation(bitstring: str, expected: str) -> None:
    """Tests the string (__str__) representation of BitVector instances.

    Args:
        bitstring: Input binary string.
        expected: The expected binary string representation.
    """
    bv = BitVector.BitVector.from_bitstring(bitstring)
    assert str(bv) == expected


def test_str_representation_from_hex() -> None:
    """Tests the string (__str__) representation when initialized via from_hex."""
    bv = BitVector.BitVector.from_hex("f")
    assert str(bv) == "1111"
