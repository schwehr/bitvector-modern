"""Tests for circular bit shift operations on BitVector."""

from typing import Literal

import pytest

import BitVector


@pytest.mark.parametrize(
    ("bitstring", "shift", "op", "expected"),
    [
        ("00110011", 3, ">>", "01100110"),
        ("00110011", 3, "<<", "10011001"),
        ("00110011", 0, ">>", "00110011"),
        ("00110011", 0, "<<", "00110011"),
        ("00110011", -3, ">>", "10011001"),
        ("00110011", -3, "<<", "01100110"),
        ("10000000000000000001", 1, "<<", "00000000000000000011"),
        ("10000000000000000001", 1, ">>", "11000000000000000000"),
    ],
)
def test_circular_shifts(
    bitstring: str, shift: int, op: Literal[">>", "<<"], expected: str
) -> None:
    """Tests circular shift operators >> and << on BitVector instances.

    Args:
        bitstring: The initial bitstring representation for the BitVector.
        shift: The integer number of bit positions to rotate.
        op: The shift operator to apply ('>>' or '<<').
        expected: The expected bitstring representation after rotation.
    """
    bv = BitVector.BitVector.from_bitstring(bitstring)
    if op == ">>":
        result = bv >> shift
    elif op == "<<":
        result = bv << shift
    else:
        raise ValueError(f"Unsupported operator: {op}")

    expected_bv = BitVector.BitVector.from_bitstring(expected)
    assert result == expected_bv
    assert str(bv) == bitstring
    assert result is not bv


@pytest.mark.parametrize(
    ("bitstring", "shift", "op", "expected"),
    [
        ("00110011", 3, ">>=", "01100110"),
        ("00110011", 3, "<<=", "10011001"),
        ("00110011", 0, ">>=", "00110011"),
        ("00110011", 0, "<<=", "00110011"),
        ("00110011", -3, ">>=", "10011001"),
        ("00110011", -3, "<<=", "01100110"),
        ("10000000000000000001", 1, "<<=", "00000000000000000011"),
        ("10000000000000000001", 1, ">>=", "11000000000000000000"),
    ],
)
def test_inplace_circular_shifts(
    bitstring: str, shift: int, op: Literal[">>=", "<<="], expected: str
) -> None:
    """Tests in-place circular shift operators >>= and <<= on BitVector instances."""
    bv = BitVector.BitVector.from_bitstring(bitstring)
    ref = bv
    if op == ">>=":
        bv >>= shift
    elif op == "<<=":
        bv <<= shift
    else:
        raise ValueError(f"Unsupported operator: {op}")

    expected_bv = BitVector.BitVector.from_bitstring(expected)
    assert bv == expected_bv
    assert bv is ref


@pytest.mark.parametrize("op", [">>", "<<", ">>=", "<<="])
def test_circular_shift_empty_vector_raises_error(op: str) -> None:
    """Verifies that circular shifting an empty BitVector raises a ValueError.

    Args:
        op: The shift operator to apply ('>>', '<<', '>>=', or '<<=').
    """
    bv = BitVector.BitVector(size=0)
    with pytest.raises(ValueError, match="Circular shift of an empty vector"):
        if op == ">>":
            _ = bv >> 1
        elif op == "<<":
            _ = bv << 1
        elif op == ">>=":
            bv >>= 1
        elif op == "<<=":
            bv <<= 1
