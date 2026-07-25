"""Property-based tests for BitVector using hypothesis."""

import copy

import hypothesis.strategies as st  # type: ignore[import-not-found]
from hypothesis import given  # type: ignore[import-not-found]

import BitVector


@given(
    st.text(alphabet="01", min_size=1, max_size=32),
    st.text(alphabet="01", min_size=1, max_size=32),
)
def test_addition_after_inversion(bits1: str, bits2: str) -> None:
    """Tests concatenation of an inverted bit vector with another bit vector.

    This test reproduces the issue described in GitHub Issue #36 where padding bits
    from __invert__ could corrupt subsequent in-place addition (__iadd__).

    Args:
        bits1: Bitstring representation for the first operand.
        bits2: Bitstring representation for the second operand.
    """
    expected = "".join("1" if b == "0" else "0" for b in bits1) + bits2
    bv1 = BitVector.BitVector.from_bitstring(bits1)
    bv2 = BitVector.BitVector.from_bitstring(bits2)
    result_bv = (~bv1) + bv2
    assert str(result_bv) == expected, f"Failed on inputs: {bits1}, {bits2}"


@given(
    st.text(alphabet="01", min_size=0, max_size=64),
    st.text(alphabet="01", min_size=0, max_size=64),
)
def test_addition_consistency(bits1: str, bits2: str) -> None:
    """Tests that __add__ and __iadd__ match standard string concatenation.

    Args:
        bits1: Bitstring representation for the first operand.
        bits2: Bitstring representation for the second operand.
    """
    expected = bits1 + bits2
    bv1 = BitVector.BitVector.from_bitstring(bits1)
    bv2 = BitVector.BitVector.from_bitstring(bits2)

    added_bv = bv1 + bv2
    assert str(added_bv) == expected

    bv1_copy = BitVector.BitVector.from_bitstring(bits1)
    bv1_copy += bv2
    assert str(bv1_copy) == expected


@given(st.text(alphabet="01", min_size=1, max_size=64))
def test_invert_involution(bits: str) -> None:
    """Tests that double inversion ~(~bv) returns the original bit vector.

    Args:
        bits: Bitstring representation of the test vector.
    """
    bv = BitVector.BitVector.from_bitstring(bits)
    double_inv = ~(~bv)
    assert str(double_inv) == bits
    assert double_inv == bv


@given(
    st.text(alphabet="01", min_size=1, max_size=32),
    st.text(alphabet="01", min_size=1, max_size=32),
)
def test_bitwise_commutativity(bits1: str, bits2: str) -> None:
    """Tests commutativity of bitwise AND, OR, and XOR for equal length vectors.

    Args:
        bits1: Bitstring representation for the first operand.
        bits2: Bitstring representation for the second operand.
    """
    min_len = min(len(bits1), len(bits2))
    bv1 = BitVector.BitVector.from_bitstring(bits1[:min_len])
    bv2 = BitVector.BitVector.from_bitstring(bits2[:min_len])

    assert str(bv1 & bv2) == str(bv2 & bv1)
    assert str(bv1 | bv2) == str(bv2 | bv1)
    assert str(bv1 ^ bv2) == str(bv2 ^ bv1)


@given(
    st.text(alphabet="01", min_size=1, max_size=50),
    st.integers(min_value=0, max_value=100),
)
def test_circular_rotation_reversibility(bits: str, shift: int) -> None:
    """Tests that circular left rotation followed by right rotation is an identity.

    Args:
        bits: Bitstring representation of the test vector.
        shift: Number of positions to rotate.
    """
    bv = BitVector.BitVector.from_bitstring(bits)
    rotated = bv << shift
    rotated = rotated >> shift
    assert str(rotated) == bits

    in_place = copy.deepcopy(bv)
    in_place.circular_rot_left()
    in_place.circular_rot_right()
    assert str(in_place) == bits


@given(st.text(alphabet="01", min_size=1, max_size=64))
def test_reverse_involution(bits: str) -> None:
    """Tests that reversing a bit vector twice returns the original vector.

    Args:
        bits: Bitstring representation of the test vector.
    """
    bv = BitVector.BitVector.from_bitstring(bits)
    bv.reverse()
    bv.reverse()
    assert str(bv) == bits


@given(st.text(alphabet="01", min_size=1, max_size=64))
def test_int_roundtrip(bits: str) -> None:
    """Tests converting to int and back to BitVector preserves bit string.

    Args:
        bits: Bitstring representation of the test vector.
    """
    bv = BitVector.BitVector.from_bitstring(bits)
    val = int(bv)
    expected_val = int(bits, 2)
    assert val == expected_val

    reconstructed = BitVector.BitVector.from_int(val, size=len(bits))
    assert str(reconstructed) == bits


@given(
    st.text(alphabet="01", min_size=0, max_size=80),
    st.one_of(st.none(), st.integers(min_value=0, max_value=80)),
    st.one_of(st.none(), st.integers(min_value=0, max_value=80)),
)
def test_slicing_consistency(bits: str, start: int | None, stop: int | None) -> None:
    """Tests that __getitem__ slicing matches standard Python string slicing.

    Verifies slice extraction across 16-bit word boundaries for arbitrary
    valid non-negative start and stop indices.

    Args:
        bits: Bitstring representation of the test vector.
        start: Optional start index for the slice.
        stop: Optional stop index for the slice.
    """
    if start is not None:
        start = min(start, len(bits))
    if stop is not None:
        stop = min(stop, len(bits))
    if start is not None and stop is not None and start > stop:
        start, stop = stop, start

    bv = (
        BitVector.BitVector.from_bitstring(bits)
        if bits
        else BitVector.BitVector(size=0)
    )
    sl = slice(start, stop)
    try:
        sliced_bv = bv[sl]
    except ValueError as e:
        if "illegal slice index values" in str(e):
            return
        raise
    assert str(sliced_bv) == bits[sl]


@given(st.text(alphabet="01", min_size=1, max_size=150))
def test_circular_rotation_equivalency(bits: str) -> None:
    """Tests that circular_rot_left and circular_rotate_left_by_one match.

    Also verifies that circular_rot_right and circular_rotate_right_by_one produce
    identical outputs across arbitrary vector sizes including multi-word (>64 bits).

    Args:
        bits: Bitstring representation of the test vector.
    """
    bv_left1 = BitVector.BitVector.from_bitstring(bits)
    bv_left2 = BitVector.BitVector.from_bitstring(bits)
    bv_left1.circular_rot_left()
    bv_left2.circular_rotate_left_by_one()
    assert str(bv_left1) == str(bv_left2)

    bv_right1 = BitVector.BitVector.from_bitstring(bits)
    bv_right2 = BitVector.BitVector.from_bitstring(bits)
    bv_right1.circular_rot_right()
    bv_right2.circular_rotate_right_by_one()
    assert str(bv_right1) == str(bv_right2)
