"""Tests for bitwise boolean logic operators (&, |, ^, ~) on BitVector."""

import operator
from typing import Any, Callable, Literal

import pytest

import BitVector

BinaryOp = Literal["&", "|", "^"]

BINARY_OP_MAP: dict[BinaryOp, Callable[[Any, Any], Any]] = {
    "&": operator.and_,
    "|": operator.or_,
    "^": operator.xor,
}


@pytest.fixture
def bv1() -> BitVector.BitVector:
    """Returns an 8-bit vector constructed from a bitstring ('00110011')."""
    return BitVector.BitVector.from_bitstring("00110011")


@pytest.fixture
def bv2() -> BitVector.BitVector:
    """Returns an 8-bit vector constructed from a bitlist ('11110011')."""
    return BitVector.BitVector(bitlist=[1, 1, 1, 1, 0, 0, 1, 1])


@pytest.fixture
def bv3() -> BitVector.BitVector:
    """Returns a 23-bit vector constructed from a bitstring."""
    return BitVector.BitVector.from_bitstring("00000000111111110000000")


@pytest.fixture
def bv_empty() -> BitVector.BitVector:
    """Returns an empty 0-bit vector."""
    return BitVector.BitVector(size=0)


@pytest.mark.parametrize(
    ("left_name", "right_name", "op", "expected"),
    [
        ("bv1", "bv2", "&", "00110011"),
        ("bv1", "bv2", "|", "11110011"),
        ("bv1", "bv2", "^", "11000000"),
        ("bv1", "bv3", "&", "00000000000000000000000"),
        ("bv1", "bv3", "|", "00000000111111110110011"),
        ("bv1", "bv3", "^", "00000000111111110110011"),
        ("bv1", "bv_empty", "&", "00000000"),
        ("bv1", "bv_empty", "|", "00110011"),
        ("bv1", "bv_empty", "^", "00110011"),
        ("bv_empty", "bv_empty", "&", ""),
        ("bv_empty", "bv_empty", "|", ""),
        ("bv_empty", "bv_empty", "^", ""),
    ],
)
def test_binary_logic_operators(
    request: pytest.FixtureRequest,
    left_name: str,
    right_name: str,
    op: BinaryOp,
    expected: str,
) -> None:
    """Tests binary boolean operators (&, |, ^) across BitVector instances.

    Args:
        request: The pytest fixture request object used for dynamic lookup.
        left_name: The fixture name of the left-hand operand.
        right_name: The fixture name of the right-hand operand.
        op: The binary logic operator string ('&', '|', '^').
        expected: The expected bitstring representation of the result.
    """
    left: BitVector.BitVector = request.getfixturevalue(left_name)
    right: BitVector.BitVector = request.getfixturevalue(right_name)
    op_func = BINARY_OP_MAP[op]
    result = op_func(left, right)
    assert result == BitVector.BitVector.from_bitstring(expected)


@pytest.mark.parametrize(
    ("bv_name", "expected"),
    [
        ("bv1", "11001100"),
        ("bv2", "00001100"),
        ("bv_empty", ""),
    ],
)
def test_unary_not_operator(
    request: pytest.FixtureRequest, bv_name: str, expected: str
) -> None:
    """Tests the bitwise NOT (~ / __invert__) operator on BitVector instances.

    Args:
        request: The pytest fixture request object used for dynamic lookup.
        bv_name: The fixture name of the target BitVector instance.
        expected: The expected bitstring representation after bitwise inversion.
    """
    bv: BitVector.BitVector = request.getfixturevalue(bv_name)
    result = ~bv
    assert result == BitVector.BitVector.from_bitstring(expected)


@pytest.mark.parametrize(
    ("left_name", "right_name", "op", "expected"),
    [
        ("bv1", "bv2", "&=", "00110011"),
        ("bv1", "bv2", "|=", "11110011"),
        ("bv1", "bv2", "^=", "11000000"),
        ("bv1", "bv3", "&=", "00000000000000000000000"),
        ("bv1", "bv3", "|=", "00000000111111110110011"),
        ("bv1", "bv3", "^=", "00000000111111110110011"),
        ("bv1", "bv_empty", "&=", "00000000"),
        ("bv1", "bv_empty", "|=", "00110011"),
        ("bv1", "bv_empty", "^=", "00110011"),
        ("bv_empty", "bv_empty", "&=", ""),
        ("bv_empty", "bv_empty", "|=", ""),
        ("bv_empty", "bv_empty", "^=", ""),
    ],
)
def test_inplace_binary_logic_operators(
    request: pytest.FixtureRequest,
    left_name: str,
    right_name: str,
    op: str,
    expected: str,
) -> None:
    """Tests in-place binary boolean operators (&=, |=, ^=) across BitVector instances.

    Verifies both that the target instance is mutated in-place (identity check)
    and that the resulting bitstring matches expected values.

    Args:
        request: The pytest fixture request object used for dynamic lookup.
        left_name: The fixture name of the left-hand operand.
        right_name: The fixture name of the right-hand operand.
        op: The in-place binary logic operator string ('&=', '|=', '^=').
        expected: The expected bitstring representation of the result.
    """
    left: BitVector.BitVector = request.getfixturevalue(left_name)[:]
    right: BitVector.BitVector = request.getfixturevalue(right_name)
    original_id = id(left)

    if op == "&=":
        left &= right
    elif op == "|=":
        left |= right
    elif op == "^=":
        left ^= right

    assert id(left) == original_id
    assert left == BitVector.BitVector.from_bitstring(expected)


def test_inplace_binary_logic_type_errors() -> None:
    """Tests TypeError exceptions raised when passing non-BitVector types to &=, |=, ^=."""
    bv = BitVector.BitVector.from_bitstring("1010")

    with pytest.raises(TypeError):
        bv &= "1010"  # type: ignore[arg-type]  # ty: ignore[unsupported-operator]

    with pytest.raises(TypeError):
        bv |= [1, 0, 1, 0]  # type: ignore[arg-type]  # ty: ignore[unsupported-operator]

    with pytest.raises(TypeError):
        bv ^= 10  # type: ignore[arg-type]  # ty: ignore[unsupported-operator]


def test_unused_bits_masked_after_invert() -> None:
    """Verifies that ~ (bitwise NOT) clears unused trailing bits in the last word."""
    bv = BitVector.BitVector(bitlist=[1, 0, 1])  # size = 3
    inv = ~bv
    assert inv._size == 3
    assert inv.vector[0] == 2  # bits 0..2 are 0, 1, 0; bits 3..63 must be 0
    assert int(inv) == 2


def test_unused_bits_masked_unequal_length_logical_ops() -> None:
    """Verifies that logical ops between unequal length vectors clear residual bits in final word."""
    bv_a = ~BitVector.BitVector(bitlist=[1, 0, 1])  # size 3, inverted
    bv_b = BitVector.BitVector(bitlist=[1, 1, 0, 1, 0])  # size 5

    # Binary operations
    for op_func in (operator.and_, operator.or_, operator.xor):
        res = op_func(bv_a, bv_b)
        rem = res._size % 64
        if rem != 0:
            assert (res.vector[-1] >> rem) == 0

        res_rev = op_func(bv_b, bv_a)
        rem_rev = res_rev._size % 64
        if rem_rev != 0:
            assert (res_rev.vector[-1] >> rem_rev) == 0

    # In-place operations
    for op_name in ("&=", "|=", "^="):
        target = ~BitVector.BitVector(bitlist=[1, 0, 1])
        operand = BitVector.BitVector(bitlist=[1, 1, 0, 1, 0])
        if op_name == "&=":
            target &= operand
        elif op_name == "|=":
            target |= operand
        elif op_name == "^=":
            target ^= operand

        rem = target._size % 64
        if rem != 0:
            assert (target.vector[-1] >> rem) == 0
