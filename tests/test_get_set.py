"""Tests bit retrieval and assignment (__getitem__, __setitem__, slicing, iteration)."""

from collections.abc import Iterator
from typing import Any, cast

import pytest

import BitVector


def test_setitem_type_error() -> None:
    """Verifies that non-integer bit assignment raises TypeError."""
    bv = BitVector.BitVector(size=5)
    with pytest.raises(TypeError, match="pos must be an integer"):
        bv[cast(Any, "0")] = 1


@pytest.mark.parametrize(
    "invalid_pos",
    [
        "0",
        3.14,
        [0],
        (0,),
        None,
        {"pos": 0},
    ],
)
def test_getitem_type_error(invalid_pos: Any) -> None:
    """Verifies that non-integer or non-slice bit retrieval raises TypeError.

    Args:
        invalid_pos: An object that is neither an integer nor a slice.
    """
    bv = BitVector.BitVector(size=5)
    with pytest.raises(TypeError, match="pos must be an integer or slice"):
        _ = bv[invalid_pos]  # type: ignore[index]


@pytest.mark.parametrize(
    ("index", "val", "err_match"),
    [
        (0, 2, "incorrect value for a bit"),
        (5, 1, "index range error"),
        (-6, 1, "index range error"),
    ],
)
def test_setitem_raises_error(index: int, val: int, err_match: str) -> None:
    """Verifies that invalid bit assignments raise ValueError.

    Args:
        index: The bit position index to modify.
        val: The bit value to assign (should be 0 or 1).
        err_match: The expected error message substring.
    """
    bv = BitVector.BitVector.from_bitstring("00000")
    with pytest.raises(ValueError, match=err_match):
        bv[index] = val


@pytest.mark.parametrize(
    ("initial", "index", "val", "expected"),
    [
        ("00000", (0,), 1, "10000"),
        ("00000", -1, 1, "00001"),
        ("10000", 0, 1, "10000"),
        ("11111", 2, 0, "11011"),
    ],
)
def test_setitem_valid(
    initial: str, index: int | tuple[int], val: int, expected: str
) -> None:
    """Tests __setitem__ with integer indices, tuple indices, and redundant values.

    Args:
        initial: The starting bitstring representation.
        index: The target bit index (integer or 1-tuple).
        val: The bit value (0 or 1) to assign.
        expected: The expected vector bitstring after modification.
    """
    bv = BitVector.BitVector.from_bitstring(initial)
    bv[cast(Any, index)] = val
    assert str(bv) == expected


@pytest.mark.parametrize("index", [5, -6])
def test_getitem_int_raises_error(index: int) -> None:
    """Verifies that out-of-bounds __getitem__ calls raise ValueError.

    Args:
        index: The out-of-bounds index to query.
    """
    bv = BitVector.BitVector.from_bitstring("10110")
    with pytest.raises(ValueError, match="index range error"):
        bv[index]  # pylint: disable=pointless-statement


@pytest.mark.parametrize(
    ("index", "expected"),
    [
        (0, 1),
        (1, 0),
        (-1, 0),
        (-2, 1),
    ],
)
def test_getitem_int(index: int, expected: int) -> None:
    """Tests __getitem__ with positive and negative integer indices.

    Args:
        index: The bit index to query.
        expected: The expected integer bit value (0 or 1).
    """
    bv = BitVector.BitVector.from_bitstring("10110")
    assert bv[index] == expected


@pytest.mark.parametrize(
    ("initial", "sl", "expected"),
    [
        ("10110", slice(None, None), "10110"),
        ("10110", slice(None, 3), "101"),
        ("10110", slice(None, -2), "101"),
        ("10110", slice(2, None), "110"),
        ("10110", slice(-3, None), "110"),
        ("10110", slice(1, -1), "011"),
        ("", slice(0, 0), ""),
        ("10110", slice(2, 2), ""),
        ("10110", slice(1, 4), "011"),
        ("10110", slice(-4, -1), "011"),
    ],
)
def test_getitem_slice(initial: str, sl: slice, expected: str) -> None:
    """Tests __getitem__ slicing across standard, negative, and open bounds.

    Args:
        initial: Initial bitstring representation for the vector.
        sl: The slice object defining the range to extract.
        expected: Expected bitstring representation of the extracted slice.
    """
    bv = (
        BitVector.BitVector.from_bitstring(initial)
        if initial
        else BitVector.BitVector(size=0)
    )
    assert str(bv[sl]) == expected


@pytest.mark.parametrize(
    "sl",
    [
        slice(None, 10),
        slice(None, -10),
        slice(10, None),
        slice(-10, None),
        slice(3, 1),
        slice(-1, 2),
        slice(4, -3),
    ],
)
def test_getitem_slice_raises_error(sl: slice) -> None:
    """Verifies out-of-bounds or inverted slice indices raise ValueError.

    Args:
        sl: The invalid slice object to test on a 5-bit vector.
    """
    bv = BitVector.BitVector.from_bitstring("10110")
    with pytest.raises(ValueError, match="illegal slice index values"):
        _ = bv[sl]


def test_bitvector_iterator() -> None:
    """Tests sequential iteration over bits in a BitVector."""
    bv = BitVector.BitVector.from_bitstring("101")
    it = iter(bv)
    assert isinstance(it, Iterator)
    assert iter(it) is it
    assert list(it) == [1, 0, 1]
    assert not list(iter(BitVector.BitVector(size=0)))
