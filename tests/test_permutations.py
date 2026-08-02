"""Tests for bit permutation and unpermutation operations on BitVector."""

from typing import Literal

import pytest

from BitVector import BitVector


@pytest.fixture
def bv1() -> BitVector:
    """Returns a 7-bit vector constructed from a bitlist ('1001101')."""
    return BitVector(bitlist=[1, 0, 0, 1, 1, 0, 1])


@pytest.fixture
def bv2() -> BitVector:
    """Returns a 7-bit vector constructed from a bitlist ('1010011')."""
    return BitVector(bitlist=[1, 0, 1, 0, 0, 1, 1])


@pytest.mark.parametrize(
    ("bv_name", "op", "perm_list", "expected"),
    [
        ("bv1", "permute", [6, 2, 0, 1, 5, 4, 3], "1010011"),
        ("bv2", "unpermute", [6, 2, 0, 1, 5, 4, 3], "1001101"),
        ("bv1", "permute", [0, 1, 2, 3, 4, 5, 6], "1001101"),
        ("bv1", "unpermute", [0, 1, 2, 3, 4, 5, 6], "1001101"),
        ("bv1", "permute", [6, 5, 4, 3, 2, 1, 0], "1011001"),
        ("bv1", "unpermute", [6, 5, 4, 3, 2, 1, 0], "1011001"),
    ],
)
def test_permutations(
    request: pytest.FixtureRequest,
    bv_name: str,
    op: Literal["permute", "unpermute"],
    perm_list: list[int],
    expected: str,
) -> None:
    """Tests permute and unpermute operations across various permutation lists.

    Args:
        request: The pytest fixture request object used for dynamic fixture lookup.
        bv_name: The fixture name of the target BitVector instance.
        op: The permutation operation string ('permute' or 'unpermute').
        perm_list: A sequence of integer indices specifying bit ordering.
        expected: The expected bitstring representation after operation.
    """
    bv: BitVector = request.getfixturevalue(bv_name)
    if op == "permute":
        result = bv.permute(perm_list)
    elif op == "unpermute":
        result = bv.unpermute(perm_list)
    else:
        raise ValueError(f"Unsupported operator: {op}")

    assert result == BitVector.from_bitstring(expected)


@pytest.mark.parametrize("op", ["permute", "unpermute"])
def test_permutation_out_of_bounds_raises_error(
    bv1: BitVector, op: Literal["permute", "unpermute"]
) -> None:
    """Verifies out-of-bounds indices in permutation lists raise ValueError.

    Args:
        bv1: A fixture providing a 7-bit BitVector instance.
        op: The permutation operation ('permute' or 'unpermute').
    """
    with pytest.raises(ValueError, match="Bad permutation index"):
        if op == "permute":
            _ = bv1.permute([7, 0, 1, 2, 3, 4, 5])
        elif op == "unpermute":
            _ = bv1.unpermute([7, 0, 1, 2, 3, 4, 5])


def test_unpermute_bad_size_raises_error(bv1: BitVector) -> None:
    """Verifies unpermute raises ValueError when list size mismatches.

    Args:
        bv1: A fixture providing a 7-bit BitVector instance.
    """
    with pytest.raises(ValueError, match="Bad size for permute list"):
        _ = bv1.unpermute([0, 1, 2])
