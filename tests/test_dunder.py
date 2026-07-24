"""Tests for BitVector dunder methods (__xor__, __and__, __add__, etc.)."""

import copy
from typing import Any, Literal, cast

import pytest

import BitVector


@pytest.mark.parametrize(
    ("left_str", "right_str", "op", "expected"),
    [
        ("10", "1100", "^", "1110"),
        ("1100", "10", "^", "1110"),
        ("1010", "1100", "^", "0110"),
        ("11", "0110", "&", "0010"),
        ("0110", "11", "&", "0010"),
        ("1010", "1100", "&", "1000"),
        ("10", "0100", "|", "0110"),
        ("0100", "10", "|", "0110"),
        ("1010", "0101", "|", "1111"),
    ],
)
def test_bitwise_dunder_operators(
    left_str: str, right_str: str, op: Literal["^", "&", "|"], expected: str
) -> None:
    """Tests dunder bitwise operators (__xor__, __and__, __or__) across lengths.

    Args:
        left_str: Bitstring representation for the left operand.
        right_str: Bitstring representation for the right operand.
        op: The bitwise operator string ('^', '&', or '|').
        expected: Expected output bitstring after applying the operator.
    """
    bv_left = BitVector.BitVector(bitstring=left_str)
    bv_right = BitVector.BitVector(bitstring=right_str)
    if op == "^":
        res = bv_left ^ bv_right
    elif op == "&":
        res = bv_left & bv_right
    elif op == "|":
        res = bv_left | bv_right
    else:
        raise ValueError(f"Unsupported operator: {op}")
    assert str(res) == expected


@pytest.mark.parametrize(
    ("left_str", "right_str", "expected"),
    [
        ("101", "010", "101010"),
        ("", "101", "101"),
        ("101", "", "101"),
        ("", "", ""),
    ],
)
def test_add(left_str: str, right_str: str, expected: str) -> None:
    """Tests concatenation dunder (__add__) across normal and empty vectors.

    Args:
        left_str: Bitstring for the left operand (empty string creates size=0).
        right_str: Bitstring for the right operand.
        expected: Expected output bitstring after concatenation.
    """
    left = (
        BitVector.BitVector(bitstring=left_str)
        if left_str
        else BitVector.BitVector(size=0)
    )
    right = (
        BitVector.BitVector(bitstring=right_str)
        if right_str
        else BitVector.BitVector(size=0)
    )
    assert str(left + right) == expected


def test_add_vector_type_fallback() -> None:
    """Tests __add__ fallback branches when self.vector is a list or tuple."""
    bv2 = BitVector.BitVector(bitstring="010")

    bv_tuple = BitVector.BitVector(bitstring="1001")
    bv_tuple.vector = tuple(bv_tuple.vector)  # type: ignore[assignment]  # ty: ignore[invalid-assignment]
    assert str(bv_tuple + bv2) == "1001010"


def test_iadd() -> None:
    """Tests in-place concatenation dunder (__iadd__) and type validation."""
    bv1 = BitVector.BitVector(bitstring="101")
    bv2 = BitVector.BitVector(bitstring="010")
    bv1 += bv2
    assert str(bv1) == "101010"

    with pytest.raises(TypeError, match="Can only join two BitVector objects, not"):
        bv1 += "010"  # type: ignore[arg-type]  # ty: ignore[unsupported-operator]


@pytest.mark.parametrize(
    ("s1", "s2"),
    [
        ("1", "0"),
        ("10101", "01101"),
        ("1" * 64, "0" * 64),
        ("1" * 64, "0" * 30),
        ("1" * 50, "0" * 30),
        ("1" * 60, "0" * 10),
        ("1" * 60, "0" * 100),
        ("1" * 100, "0" * 100),
        ("", "1010"),
        ("1010", ""),
        ("", ""),
    ],
)
def test_iadd_alignment_cases(s1: str, s2: str) -> None:
    """Tests __iadd__ across various word-alignment boundaries and sizes."""
    bv1 = BitVector.BitVector(bitstring=s1) if s1 else BitVector.BitVector(size=0)
    bv2 = BitVector.BitVector(bitstring=s2) if s2 else BitVector.BitVector(size=0)
    bv1 += bv2
    assert str(bv1) == s1 + s2
    assert len(bv1) == len(s1) + len(s2)


@pytest.mark.parametrize(
    "s",
    [
        "1",
        "101",
        "1" * 5,
        "1" * 60,
        "10" * 32,
        "1" * 100,
    ],
)
def test_iadd_self_concatenation(s: str) -> None:
    """Tests in-place self-concatenation (bv += bv)."""
    bv = BitVector.BitVector(bitstring=s)
    bv += bv
    assert str(bv) == s + s
    assert len(bv) == len(s) * 2


@pytest.mark.parametrize(
    ("bitstring", "expected"),
    [
        ("10100111", "01011000"),
        ("", ""),
    ],
)
def test_invert(bitstring: str, expected: str) -> None:
    """Tests bitwise inversion dunder (__invert__ / ~) on vectors.

    Args:
        bitstring: Input bitstring to invert (empty string creates size=0).
        expected: Expected output bitstring after inversion.
    """
    bv = (
        BitVector.BitVector(bitstring=bitstring)
        if bitstring
        else BitVector.BitVector(size=0)
    )
    assert str(~bv) == expected


def test_deepcopy() -> None:
    """Tests deep copying via copy.deepcopy, memoization, and fallbacks."""
    bv = BitVector.BitVector(bitstring="10110")
    bv_copy = copy.deepcopy(bv)
    assert str(bv_copy) == "10110"
    assert bv_copy is not bv
    assert bv_copy.vector is not bv.vector

    memo: dict[int, Any] = {}
    bv_memo = copy.deepcopy(bv, memo)
    assert str(bv_memo) == "10110"
    # pylint: disable-next=unnecessary-dunder-call
    assert str(bv.__deepcopy__()) == "10110"

    bv_tuple = BitVector.BitVector(bitstring="1001")
    bv_tuple.vector = tuple(bv_tuple.vector)  # type: ignore[assignment]  # ty: ignore[invalid-assignment]
    bv_tuple_copy = copy.deepcopy(bv_tuple)
    assert str(bv_tuple_copy) == "1001"


@pytest.mark.parametrize(
    ("shift", "expected"),
    [
        (1, "0001"),
        (2, "0010"),
        (0, "1000"),
        (-1, "0100"),
    ],
)
def test_lshift(shift: int, expected: str) -> None:
    """Tests circular left shift dunder (__lshift__ / <<).

    Args:
        shift: Number of bit positions to rotate left.
        expected: Expected output bitstring.
    """
    bv = BitVector.BitVector(bitstring="1000")
    res = bv << shift
    assert str(res) == expected
    assert str(bv) == "1000"
    assert res is not bv


def test_ilshift() -> None:
    """Tests in-place circular left shift dunder (__ilshift__ / <<=)."""
    bv = BitVector.BitVector(bitstring="1000")
    ref = bv
    bv <<= 1
    assert str(bv) == "0001"
    assert bv is ref

    bv <<= -1
    assert str(bv) == "1000"
    assert bv is ref


@pytest.mark.parametrize("op", ["<<", ">>", "<<=", ">>="])
def test_shift_empty_vector_raises_error(op: str) -> None:
    """Verifies that circular shifting an empty vector raises ValueError.

    Args:
        op: The shift operator ('<<', '>>', '<<=', or '>>=').
    """
    bv_empty = BitVector.BitVector(size=0)
    with pytest.raises(ValueError, match="Circular shift of an empty vector"):
        if op == "<<":
            _ = bv_empty << 1
        elif op == ">>":
            _ = bv_empty >> 1
        elif op == "<<=":
            bv_empty <<= 1
        elif op == ">>=":
            bv_empty >>= 1


@pytest.mark.parametrize(
    ("shift", "expected"),
    [
        (1, "0100"),
        (2, "0010"),
        (0, "1000"),
        (-1, "0001"),
    ],
)
def test_rshift(shift: int, expected: str) -> None:
    """Tests circular right shift dunder (__rshift__ / >>).

    Args:
        shift: Number of bit positions to rotate right.
        expected: Expected output bitstring.
    """
    bv = BitVector.BitVector(bitstring="1000")
    res = bv >> shift
    assert str(res) == expected
    assert str(bv) == "1000"
    assert res is not bv


def test_irshift() -> None:
    """Tests in-place circular right shift dunder (__irshift__ / >>=)."""
    bv = BitVector.BitVector(bitstring="1000")
    ref = bv
    bv >>= 1
    assert str(bv) == "0100"
    assert bv is ref

    bv >>= -1
    assert str(bv) == "1000"
    assert bv is ref


@pytest.mark.parametrize(
    ("initial", "sl", "err_size", "err_match", "valid_str", "expected"),
    [
        (
            "0000",
            slice(None, 2),
            1,
            "incompatible lengths for slice assignment 1",
            "11",
            "1100",
        ),
        (
            "0000",
            slice(None, -1),
            2,
            "incompatible lengths for slice assignment 2",
            "111",
            "1110",
        ),
        (
            "0000",
            slice(2, None),
            1,
            "incompatible lengths for slice assignment 3",
            "11",
            "0011",
        ),
        (
            "0000",
            slice(-2, None),
            1,
            "incompatible lengths for slice assignment 4",
            "11",
            "0011",
        ),
        (
            "000000",
            slice(1, -1),
            2,
            "incompatible lengths for slice assignment 5",
            "1111",
            "011110",
        ),
        (
            "000000",
            slice(-5, 4),
            2,
            "incompatible lengths for slice assignment 6",
            "111",
            "011100",
        ),
        (
            "0000",
            slice(1, 3),
            1,
            "incompatible lengths for slice assignment 7",
            "11",
            "0110",
        ),
    ],
)
def test_setitem_slice_assignment(
    initial: str,
    sl: slice,
    err_size: int,
    err_match: str,
    valid_str: str,
    expected: str,
) -> None:
    """Tests __setitem__ slice assignment validation and success.

    Args:
        initial: Initial bitstring representation for the vector.
        sl: The slice object defining the target range.
        err_size: A vector size that triggers an incompatible length error.
        err_match: The expected error message substring.
        valid_str: A bitstring of valid length for assignment.
        expected: Expected vector bitstring after assignment.
    """
    bv = BitVector.BitVector(bitstring=initial)
    with pytest.raises(ValueError, match=err_match):
        bv[sl] = BitVector.BitVector(size=err_size)
    bv[sl] = BitVector.BitVector(bitstring=valid_str)
    assert str(bv) == expected


def test_setitem_index_assignment() -> None:
    """Tests __setitem__ with positive and negative integer indices."""
    bv = BitVector.BitVector(bitstring="000")
    bv[1] = 1
    bv[-1] = 1
    assert str(bv) == "011"
    bv[0] = 0
    assert str(bv) == "011"


def test_setitem_slice_type_error() -> None:
    """Verifies slice assignment with a non-BitVector raises TypeError."""
    bv = BitVector.BitVector(bitstring="000")
    with pytest.raises(
        TypeError,
        match="For slice assignment, the right hand side must be a BitVector",
    ):
        bv[0:1] = cast(Any, [1])


def test_setitem_full_slice() -> None:
    """Tests __setitem__ when replacing the entire slice ([:])."""
    bv = BitVector.BitVector(bitstring="1010")
    bv[:] = BitVector.BitVector(bitstring="0101")
    assert str(bv) == "1010"


@pytest.mark.parametrize(
    ("bitstring", "expected"),
    [
        ("", ""),
        ("10110", "10110"),
    ],
)
def test_str(bitstring: str, expected: str) -> None:
    """Tests __str__ representation on empty and non-empty vectors.

    Args:
        bitstring: Initial bitstring representation.
        expected: Expected string representation.
    """
    bv = (
        BitVector.BitVector(bitstring=bitstring)
        if bitstring
        else BitVector.BitVector(size=0)
    )
    assert str(bv) == expected


def test_format() -> None:
    """Tests __format__ string and integer interpolation."""
    bv = BitVector.BitVector(intVal=15, size=8)

    # Test formatting with no specifier (defaults to str)
    assert f"{bv}" == "00001111"

    # Test formatting as string (padding, alignment)
    assert f"{bv:<10}" == "00001111  "
    assert f"{bv:s}" == "00001111"

    # Test formatting as integer (hex, binary, decimal, etc.)
    assert f"{bv:x}" == "f"
    assert f"{bv:X}" == "F"
    assert f"{bv:08b}" == "00001111"
    assert f"{bv:d}" == "15"

    # Test formatting empty vector
    bv_empty = BitVector.BitVector(size=0)
    assert f"{bv_empty}" == ""
    assert f"{bv_empty:10}" == "          "
    assert f"{bv_empty:d}" == "0"


@pytest.mark.parametrize(
    ("bitstring", "expected"),
    [
        ("", 0),
        ("0", 0),
        ("1", 1),
        ("1010", 10),
        ("11111111", 255),
    ],
)
def test_int(bitstring: str, expected: int) -> None:
    """Tests integer conversion dunder (__int__ / int()) on empty and non-empty vectors.

    Args:
        bitstring: Initial bitstring representation.
        expected: Expected integer conversion output.
    """
    bv = (
        BitVector.BitVector(bitstring=bitstring)
        if bitstring
        else BitVector.BitVector(size=0)
    )
    assert int(bv) == expected


@pytest.mark.parametrize(
    ("bitstring", "expected_bits"),
    [
        ("", []),
        ("0", [0]),
        ("1", [1]),
        ("10110", [0, 1, 1, 0, 1]),
        # 63 bits (1 bit short of 64-bit block)
        ("1" + "0" * 61 + "1", [1] + [0] * 61 + [1]),
        # 64 bits (exact 1 block)
        ("1" + "0" * 62 + "1", [1] + [0] * 62 + [1]),
        # 65 bits (spans across 64-bit block boundary)
        ("1" + "0" * 63 + "1", [1] + [0] * 63 + [1]),
        # 128 bits (exact 2 blocks)
        ("1" + "0" * 126 + "1", [1] + [0] * 126 + [1]),
        # 129 bits (spans across 3 blocks)
        ("1" + "0" * 127 + "1", [1] + [0] * 127 + [1]),
        # Alternating bits right at index 63 & 64 (block boundary)
        ("0" * 63 + "11" + "0" * 64, [0] * 64 + [1, 1] + [0] * 63),
    ],
)
def test_reversed(bitstring: str, expected_bits: list[int]) -> None:
    """Tests reverse iteration via __reversed__ dunder and built-in reversed().

    Args:
        bitstring: Initial bitstring representation.
        expected_bits: Expected list of integer bits yielded in reverse order.
    """
    bv = (
        BitVector.BitVector(bitstring=bitstring)
        if bitstring
        else BitVector.BitVector(size=0)
    )
    assert list(reversed(bv)) == expected_bits
    # pylint: disable-next=unnecessary-dunder-call
    assert list(bv.__reversed__()) == expected_bits


@pytest.mark.parametrize(
    "size", [0, 1, 2, 31, 63, 64, 65, 127, 128, 129, 200, 256, 512]
)
def test_reversed_block_boundaries(size: int) -> None:
    """Tests __reversed__ across 64-bit block boundaries and arbitrary sizes.

    Args:
        size: Vector length in bits to test.
    """
    if size == 0:
        bv = BitVector.BitVector(size=0)
        assert not list(reversed(bv))
        # pylint: disable-next=unnecessary-dunder-call
        assert not list(bv.__reversed__())
        return

    bits = ["1" if (i % 7 == 0 or i == size - 1) else "0" for i in range(size)]
    bitstr = "".join(bits)
    bv = BitVector.BitVector(bitstring=bitstr)
    expected = [int(c) for c in reversed(bitstr)]

    assert list(reversed(bv)) == expected
    # pylint: disable-next=unnecessary-dunder-call
    assert list(bv.__reversed__()) == expected


@pytest.mark.parametrize(
    ("left_str", "right_str", "expected"),
    [
        ("1010", "10100", False),
        ("1010", "1011", False),
        ("1010", "1010", True),
        ("", "", True),
    ],
)
def test_eq(left_str: str, right_str: str, expected: bool) -> None:
    """Tests equality dunder (__eq__ / ==) across various lengths and values.

    Args:
        left_str: Bitstring for the left operand.
        right_str: Bitstring for the right operand.
        expected: Expected boolean equality result.
    """
    left = (
        BitVector.BitVector(bitstring=left_str)
        if left_str
        else BitVector.BitVector(size=0)
    )
    right = (
        BitVector.BitVector(bitstring=right_str)
        if right_str
        else BitVector.BitVector(size=0)
    )
    assert (left == right) is expected


@pytest.mark.parametrize(
    ("left_str", "right_str", "expected"),
    [
        ("1010", "1010", False),
        ("1010", "0101", True),
    ],
)
def test_ne(left_str: str, right_str: str, expected: bool) -> None:
    """Tests inequality dunder (__ne__ / !=) across various bitstrings.

    Args:
        left_str: Bitstring for the left operand.
        right_str: Bitstring for the right operand.
        expected: Expected boolean inequality result.
    """
    left = BitVector.BitVector(bitstring=left_str)
    right = BitVector.BitVector(bitstring=right_str)
    assert (left != right) is expected


@pytest.mark.parametrize(
    ("val1", "val2", "op", "expected"),
    [
        (3, 5, "<", True),
        (5, 3, "<", False),
        (3, 3, "<", False),
        (3, 5, "<=", True),
        (3, 3, "<=", True),
        (5, 3, "<=", False),
        (5, 3, ">", True),
        (3, 5, ">", False),
        (3, 3, ">", False),
        (5, 3, ">=", True),
        (3, 3, ">=", True),
        (3, 5, ">=", False),
    ],
)
def test_relational_operators(
    val1: int, val2: int, op: Literal["<", "<=", ">", ">="], expected: bool
) -> None:
    """Tests relational dunder operators (__lt__, __le__, __gt__, __ge__).

    Args:
        val1: Integer value for the left operand.
        val2: Integer value for the right operand.
        op: Relational operator string ('<', '<=', '>', '>=').
        expected: Expected boolean comparison result.
    """
    bv1 = BitVector.BitVector(intVal=val1, size=8)
    bv2 = BitVector.BitVector(intVal=val2, size=8)
    if op == "<":
        res = bv1 < bv2
    elif op == "<=":
        res = bv1 <= bv2
    elif op == ">":
        res = bv1 > bv2
    elif op == ">=":
        res = bv1 >= bv2
    else:
        raise ValueError(f"Unsupported operator: {op}")
    assert res is expected


@pytest.mark.parametrize(
    ("pattern", "expected_in"),
    [
        ("010", True),
        ("111", False),
    ],
)
def test_contains(pattern: str, expected_in: bool) -> None:
    """Tests substring search dunder (__contains__ / in).

    Args:
        pattern: The bitstring pattern to search for.
        expected_in: True if pattern is found in the vector, otherwise False.
    """
    bv = BitVector.BitVector(bitstring="110100")
    sub_bv = BitVector.BitVector(bitstring=pattern)
    assert (sub_bv in bv) is expected_in


@pytest.mark.parametrize(
    ("target_str", "pattern_str", "err_match"),
    [
        ("", "1", "First arg bitvec has no bits"),
        ("110100", "1101000", "First arg bitvec too short"),
    ],
)
def test_contains_invalid_args_raises_error(
    target_str: str, pattern_str: str, err_match: str
) -> None:
    """Verifies that invalid __contains__ lookups raise ValueError.

    Args:
        target_str: The bitstring for the container vector.
        pattern_str: The bitstring for the substring pattern vector.
        err_match: The expected error message substring.
    """
    target = (
        BitVector.BitVector(bitstring=target_str)
        if target_str
        else BitVector.BitVector(size=0)
    )
    pattern = BitVector.BitVector(bitstring=pattern_str)
    with pytest.raises(ValueError, match=err_match):
        _ = pattern in target
