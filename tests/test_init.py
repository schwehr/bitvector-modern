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
        ({"intVal": 5, "bitstring": "101"}, "When intVal is specified"),
        (
            {"intVal": 0, "size": 0},
            "The value specified for size must be at least",
        ),
        (
            {"intVal": 0, "size": -1},
            "The value specified for size must be at least",
        ),
        (
            {"intVal": 5, "size": 0},
            "The value specified for size must be at least",
        ),
        (
            {"intVal": 255, "size": 2},
            "The value specified for size must be at least",
        ),
        (
            {"size": 10, "bitlist": [1, 0]},
            r"When size is specified \(without an intVal\)",
        ),
        ({"size": -5}, r"wrong arg\(s\) for constructor"),
        ({"bitstring": "1010", "rawbytes": b"xy"}, "When a bitstring is specified"),
        (
            {"bitlist": [1, 0], "rawbytes": b"xy"},
            "When bits are specified, you cannot give values",
        ),
        (
            {"rawbytes": b"xy", "size": -5},
            "When bits are specified through rawbytes",
        ),
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
    ("kwargs", "expected_str", "expected_size"),
    [
        ({"intVal": 0}, "0", 1),
        ({"intVal": 0, "size": 5}, "00000", 5),
        ({"intVal": 5}, "101", 3),
        ({"intVal": 32}, "100000", 6),
        ({"intVal": 5, "size": 10}, "0000000101", 10),
        ({"size": 10}, "0000000000", 10),
        ({"size": 0}, "", 0),
        ({"bitstring": "00110011"}, "00110011", 8),
        ({"bitstring": ""}, "", 0),
        ({"bitlist": [1, 1, 0, 1]}, "1101", 4),
        ({"bitlist": []}, "", 0),
        ({"rawbytes": b"\x00\xff"}, "0000000011111111", 16),
        ({"rawbytes": b""}, "", 0),
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
    bv = BitVector.BitVector(
        intVal=ZeroHex(),  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
        size=0,
    )
    assert bv._size == 0
    assert str(bv) == ""

    bv2 = BitVector.BitVector(
        intVal=ZeroHex(),  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
        size=5,
    )
    assert bv2._size == 5
    assert str(bv2) == "00000"


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
