"""Tests BitVector constructors and initialization error validation."""

import re
from typing import Any

import pytest

import BitVector


class ZeroHex:
    """Helper class to test intVal == 0 branch with custom indexing."""

    def __eq__(self, other: object) -> bool:
        """Returns False to trigger fallback zero evaluation."""
        return False

    def __index__(self) -> int:
        """Returns 0 when converted to an integer index."""
        return 0


def test_positional_args_error() -> None:
    """Verifies that passing positional arguments raises TypeError."""
    with pytest.raises(TypeError, match="takes 1 positional argument"):
        BitVector.BitVector(123)  # type: ignore[misc,arg-type]  # ty: ignore[too-many-positional-arguments]


def test_invalid_keyword_error() -> None:
    """Verifies passing unexpected keyword arguments raises TypeError."""
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        # pylint: disable-next=unexpected-keyword-arg
        BitVector.BitVector(invalid_param=123)  # type: ignore[call-arg]  # ty: ignore[unknown-argument]


@pytest.mark.parametrize(
    ("kwargs", "err_match"),
    [
        (
            {"size": 10, "bitlist": [1, 0]},
            r"When size is specified",
        ),
        ({"size": -5}, r"wrong arg\(s\) for constructor"),
        ({}, r"wrong arg\(s\) for constructor"),
    ],
)
def test_constructor_conflicting_args_raises_error(
    kwargs: dict[str, Any], err_match: str
) -> None:
    """Verifies conflicting or invalid constructor arguments raise ValueError.

    Args:
        kwargs: Keyword arguments containing invalid or conflicting inputs.
        err_match: The expected regex error message pattern.
    """
    with pytest.raises(ValueError, match=err_match):
        BitVector.BitVector(**kwargs)


@pytest.mark.parametrize(
    ("kwargs", "err_match"),
    [
        ({"intVal": 5}, "unexpected keyword argument"),
        ({"bitstring": "1010"}, "unexpected keyword argument"),
        ({"rawbytes": b"xy"}, "unexpected keyword argument"),
    ],
)
def test_constructor_legacy_kwargs_raise_type_error(
    kwargs: dict[str, Any], err_match: str
) -> None:
    """Verifies that removed legacy constructor arguments raise TypeError.

    Args:
        kwargs: Legacy keyword arguments.
        err_match: The expected regex error message pattern.
    """
    with pytest.raises(TypeError, match=err_match):
        BitVector.BitVector(**kwargs)


@pytest.mark.parametrize(
    ("kwargs", "expected_str", "expected_size"),
    [
        ({"size": 10}, "0000000000", 10),
        ({"size": 0}, "", 0),
        ({"bitlist": [1, 1, 0, 1]}, "1101", 4),
        ({"bitlist": []}, "", 0),
    ],
)
def test_constructor_valid_kwargs(
    kwargs: dict[str, Any], expected_str: str, expected_size: int
) -> None:
    """Tests initializing BitVector from valid keyword arguments.

    Args:
        kwargs: Constructor keyword argument dictionary.
        expected_str: Expected bitstring representation.
        expected_size: Expected integer bit vector size.
    """
    bv = BitVector.BitVector(**kwargs)
    assert str(bv) == expected_str
    assert bv._size == expected_size


def test_from_string() -> None:
    """Tests initializing BitVector from a string via the from_string method."""
    bv = BitVector.BitVector.from_string("A")
    assert str(bv) == "01000001"

    bv2 = BitVector.BitVector.from_string("A\x05")
    assert bv2._size == 16


def test_from_hex() -> None:
    """Tests initializing BitVector from a hex string via the from_hex method."""
    bv = BitVector.BitVector.from_hex("0FaE")
    assert str(bv) == "0000111110101110"
    assert bv._size == 16

    bv2 = BitVector.BitVector.from_hex("")
    assert str(bv2) == ""
    assert bv2._size == 0


def test_intVal_zero_hex_helper() -> None:
    """Tests intVal zero evaluation using the ZeroHex helper class."""
    bv = BitVector.BitVector.from_int(
        val=ZeroHex(),  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
        size=0,
    )
    assert bv._size == 0
    assert str(bv) == ""

    bv2 = BitVector.BitVector.from_int(
        val=ZeroHex(),  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
        size=5,
    )
    assert bv2._size == 5
    assert str(bv2) == "00000"


def test_from_int() -> None:
    """Tests initializing BitVector via the from_int class method."""
    bv = BitVector.BitVector.from_int(5)
    assert str(bv) == "101"
    assert bv._size == 3

    bv_padded = BitVector.BitVector.from_int(5, size=8)
    assert str(bv_padded) == "00000101"
    assert bv_padded._size == 8

    bv_zero = BitVector.BitVector.from_int(0)
    assert str(bv_zero) == "0"
    assert bv_zero._size == 1

    bv_zero_padded = BitVector.BitVector.from_int(0, size=4)
    assert str(bv_zero_padded) == "0000"
    assert bv_zero_padded._size == 4

    with pytest.raises(
        ValueError, match="The value specified for size must be at least"
    ):
        BitVector.BitVector.from_int(255, size=2)

    with pytest.raises(ValueError, match="val must be non-negative"):
        BitVector.BitVector.from_int(-5)


def test_from_bytes() -> None:
    """Tests initializing BitVector via the from_bytes class method."""
    bv = BitVector.BitVector.from_bytes(b"\x00\xff")
    assert str(bv) == "0000000011111111"
    assert bv._size == 16

    bv_empty = BitVector.BitVector.from_bytes(b"")
    assert str(bv_empty) == ""
    assert bv_empty._size == 0


def test_from_bitstring() -> None:
    """Tests initializing BitVector via the from_bitstring class method."""
    bv = BitVector.BitVector.from_bitstring("1101")
    assert str(bv) == "1101"
    assert bv._size == 4

    bv_empty = BitVector.BitVector.from_bitstring("")
    assert str(bv_empty) == ""
    assert bv_empty._size == 0


def test_from_bitlist() -> None:
    """Tests initializing BitVector via the from_bitlist class method."""
    bv = BitVector.BitVector.from_bitlist([1, 0, 1, 0])
    assert str(bv) == "1010"
    assert bv._size == 4

    bv_empty = BitVector.BitVector.from_bitlist([])
    assert str(bv_empty) == ""
    assert bv_empty._size == 0


def test_version() -> None:
    """Tests that the package version string conforms to semantic versioning."""
    semver_pattern = (
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
        r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )
    assert isinstance(BitVector.__version__, str)
    assert re.fullmatch(semver_pattern, BitVector.__version__) is not None
