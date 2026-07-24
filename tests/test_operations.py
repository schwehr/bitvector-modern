"""Tests BitVector operations (math, shifts, distance, GF arithmetic)."""

import copy

import pytest

import BitVector


def test_divide_into_two_raises_error() -> None:
    """Verifies dividing a vector with an odd number of bits raises ValueError."""
    bv_odd = BitVector.BitVector(bitstring="101")
    with pytest.raises(ValueError, match="must have even num bits"):
        bv_odd.divide_into_two()


@pytest.mark.parametrize(
    ("bitstring", "expected_left", "expected_right"),
    [
        ("11001011", "1100", "1011"),
        ("", "", ""),
    ],
)
def test_divide_into_two(
    bitstring: str, expected_left: str, expected_right: str
) -> None:
    """Tests divide_into_two on even-length and empty vectors.

    Args:
        bitstring: Input vector bitstring representation.
        expected_left: Expected bitstring of the left half vector.
        expected_right: Expected bitstring of the right half vector.
    """
    bv = (
        BitVector.BitVector(bitstring=bitstring)
        if bitstring
        else BitVector.BitVector(size=0)
    )
    left, right = bv.divide_into_two()
    assert str(left) == expected_left
    assert str(right) == expected_right


@pytest.mark.parametrize(
    ("bitstring", "perm_list", "err_match"),
    [
        ("1010", [0, 1, 2, 4], "Bad permutation index"),
    ],
)
def test_permute_raises_error(
    bitstring: str, perm_list: list[int], err_match: str
) -> None:
    """Verifies invalid permutation indices raise ValueError.

    Args:
        bitstring: Input vector bitstring representation.
        perm_list: List of target bit indices for permutation.
        err_match: Expected error message pattern.
    """
    bv = BitVector.BitVector(bitstring=bitstring)
    with pytest.raises(ValueError, match=err_match):
        bv.permute(perm_list)


@pytest.mark.parametrize(
    ("bitstring", "perm_list", "expected"),
    [
        ("1011", [3, 2, 1, 0], "1101"),
        ("1011", [0, 1, 0, 1, 2, 3], "101011"),
    ],
)
def test_permute(bitstring: str, perm_list: list[int], expected: str) -> None:
    """Tests bit permutation across identical and extended sizes.

    Args:
        bitstring: Input vector bitstring representation.
        perm_list: List of target bit indices for permutation.
        expected: Expected output vector bitstring.
    """
    bv = BitVector.BitVector(bitstring=bitstring)
    permuted = bv.permute(perm_list)
    assert str(permuted) == expected


@pytest.mark.parametrize(
    ("bitstring", "perm_list", "err_match"),
    [
        ("1010", [0, 1, 2, 4], "Bad permutation index"),
        ("1010", [0, 1, 2], "Bad size for permute list"),
    ],
)
def test_unpermute_raises_error(
    bitstring: str, perm_list: list[int], err_match: str
) -> None:
    """Verifies invalid unpermute indices or lengths raise ValueError.

    Args:
        bitstring: Input vector bitstring representation.
        perm_list: List of permutation indices.
        err_match: Expected error message pattern.
    """
    bv = BitVector.BitVector(bitstring=bitstring)
    with pytest.raises(ValueError, match=err_match):
        bv.unpermute(perm_list)


def test_unpermute() -> None:
    """Tests round-trip permutation and unpermutation."""
    bv_orig = BitVector.BitVector(bitstring="11001010")
    p_list = [7, 6, 5, 4, 3, 2, 1, 0]
    permuted = bv_orig.permute(p_list)
    unpermuted = permuted.unpermute(p_list)
    assert str(unpermuted) == str(bv_orig)


@pytest.mark.parametrize(
    ("method_name", "bitstring", "expected"),
    [
        ("circular_rot_left", "1000", "0001"),
        ("circular_rot_left", "10000000000000000001", "00000000000000000011"),
        ("circular_rot_left", "1" + "0" * 128 + "1", "0" * 128 + "11"),
        ("circular_rot_right", "0001", "1000"),
        ("circular_rot_right", "10000000000000000001", "11000000000000000000"),
        ("circular_rot_right", "1" + "0" * 128 + "1", "11" + "0" * 128),
        ("shift_left_by_one", "1011", "0110"),
        ("shift_left_by_one", "1" + "0" * 18 + "1", "0" * 18 + "10"),
        ("shift_left_by_one", "1" + "0" * 128 + "1", "0" * 128 + "10"),
        ("shift_right_by_one", "1101", "0110"),
        ("shift_right_by_one", "1" + "0" * 18 + "1", "01" + "0" * 18),
        ("shift_right_by_one", "1" + "0" * 128 + "1", "01" + "0" * 128),
    ],
)
def test_rotations_and_one_bit_shifts(
    method_name: str, bitstring: str, expected: str
) -> None:
    """Tests circular rotations and 1-bit shifts on short and long vectors.

    Args:
        method_name: Name of the BitVector rotation or shift method.
        bitstring: Initial vector bitstring representation.
        expected: Expected output vector bitstring after mutation.
    """
    bv = BitVector.BitVector(bitstring=bitstring)
    method = getattr(bv, method_name)
    method()
    assert str(bv) == expected


@pytest.mark.parametrize(
    ("direction", "shift_amount", "expected"),
    [
        ("left", 2, "110100"),
        ("left", 0, "101101"),
        ("right", 2, "001011"),
        ("right", 0, "101101"),
    ],
)
def test_shift_left_right(direction: str, shift_amount: int, expected: str) -> None:
    """Tests shift_left and shift_right in-place mutations and chaining.

    Args:
        direction: Shift direction ('left' or 'right').
        shift_amount: Number of bit positions to shift.
        expected: Expected output vector bitstring.
    """
    bv = BitVector.BitVector(bitstring="101101")
    if direction == "left":
        res = bv.shift_left(shift_amount)
    else:
        res = bv.shift_right(shift_amount)
    assert str(bv) == expected
    assert res is bv


@pytest.mark.parametrize(
    ("initial_bitstring", "shift_amount", "expected_bitstring"),
    [
        ("101101", 2, "110100"),
        ("101101", 0, "101101"),
        ("101101", -3, "101101"),
        ("", 5, ""),
        ("1" * 128, 0, "1" * 128),
        ("1" * 64 + "0" * 64 + "1" * 64, 64, "0" * 64 + "1" * 64 + "0" * 64),
        ("1" * 128, 10, "1" * 118 + "0" * 10),
        ("1" * 192, 130, "1" * 62 + "0" * 130),
        ("1" * 192, 200, "0" * 192),
    ],
)
def test_shift_left_comprehensive(
    initial_bitstring: str, shift_amount: int, expected_bitstring: str
) -> None:
    """Tests shift_left across single-word, multi-word, multiple-of-64, and boundary conditions.

    Args:
        initial_bitstring: Initial bitstring representation of the vector.
        shift_amount: Number of positions to shift left.
        expected_bitstring: Expected bitstring representation after shifting.
    """
    bv = BitVector.BitVector(bitstring=initial_bitstring)
    res = bv.shift_left(shift_amount)
    assert res is bv
    assert str(bv) == expected_bitstring


@pytest.mark.parametrize(
    ("initial_bitstring", "shift_amount", "expected_bitstring"),
    [
        ("101101", 2, "001011"),
        ("101101", 0, "101101"),
        ("101101", -3, "101101"),
        ("", 5, ""),
        ("1" * 128, 0, "1" * 128),
        ("1" * 64 + "0" * 64 + "1" * 64, 64, "0" * 64 + "1" * 64 + "0" * 64),
        ("1" * 65 + "0" * 65, 10, "0" * 10 + "1" * 65 + "0" * 55),
        ("1" * 192, 130, "0" * 130 + "1" * 62),
        ("1" * 192, 200, "0" * 192),
    ],
)
def test_shift_right_comprehensive(
    initial_bitstring: str, shift_amount: int, expected_bitstring: str
) -> None:
    """Tests shift_right across single-word, multi-word, multiple-of-64, and boundary conditions.

    Args:
        initial_bitstring: Initial bitstring representation of the vector.
        shift_amount: Number of positions to shift right.
        expected_bitstring: Expected bitstring representation after shifting.
    """
    bv = BitVector.BitVector(bitstring=initial_bitstring)
    res = bv.shift_right(shift_amount)
    assert res is bv
    assert str(bv) == expected_bitstring


def test_shift_right_extended_vector() -> None:
    """Verifies shift_right clears trailing excess words when vector storage is over-allocated."""
    bv = BitVector.BitVector(bitstring="1" * 65)
    bv.vector.append(999)
    res = bv.shift_right(1)
    assert res is bv
    assert str(bv) == "0" + "1" * 64
    assert bv.vector[-1] == 0


@pytest.mark.parametrize(
    ("direction", "pad_count", "input_str", "expected_str"),
    [
        ("left", 2, "101", "00101"),
        ("left", 0, "101", "101"),
        ("left", -1, "101", "101"),
        ("left", 60, "1" * 10, "0" * 60 + "1" * 10),
        ("left", 64, "1" * 64, "0" * 64 + "1" * 64),
        ("left", 100, "1" * 50, "0" * 100 + "1" * 50),
        ("left", 10, "", "0" * 10),
        ("right", 2, "101", "10100"),
        ("right", 0, "101", "101"),
        ("right", -1, "101", "101"),
        ("right", 60, "1" * 10, "1" * 10 + "0" * 60),
        ("right", 64, "1" * 64, "1" * 64 + "0" * 64),
        ("right", 100, "1" * 50, "1" * 50 + "0" * 100),
        ("right", 10, "", "0" * 10),
    ],
)
def test_padding(
    direction: str, pad_count: int, input_str: str, expected_str: str
) -> None:
    """Tests pad_from_left and pad_from_right across positive, negative, and zero pads across word boundaries.

    Args:
        direction: Padding direction ('left' or 'right').
        pad_count: Number of zero bits to prepend or append.
        input_str: Input bitstring to construct vector.
        expected_str: Expected output vector bitstring.
    """
    bv = (
        BitVector.BitVector(bitstring=input_str)
        if input_str
        else BitVector.BitVector(size=0)
    )
    if direction == "left":
        resized = bv._resize_pad_from_left(pad_count)
        assert str(resized) == expected_str
        bv.pad_from_left(pad_count)
    else:
        bv.pad_from_right(pad_count)
    assert str(bv) == expected_str
    assert bv._size == len(expected_str)


def test_reset_raises_error() -> None:
    """Verifies calling reset with an invalid bit value raises ValueError."""
    bv = BitVector.BitVector(bitstring="101")
    with pytest.raises(ValueError, match="Incorrect reset argument"):
        bv.reset(2)


@pytest.mark.parametrize(
    ("val", "expected"),
    [
        (1, "111"),
        (0, "000"),
    ],
)
def test_reset(val: int, expected: str) -> None:
    """Tests setting all bits in a vector to 0 or 1 via reset.

    Args:
        val: The bit value (0 or 1) to reset all bits to.
        expected: Expected output vector bitstring.
    """
    bv = BitVector.BitVector(bitstring="101")
    res = bv.reset(val)
    assert str(bv) == expected
    assert res is bv


def test_reset_coverage() -> None:
    """Tests reset with vector size multiple of word size and size 0."""
    # rem == 0, len(self.vector) > 0
    bv_64 = BitVector.BitVector(size=64)
    bv_64.reset(1)
    assert str(bv_64) == "1" * 64

    # rem == 0, len(self.vector) == 0
    bv_0 = BitVector.BitVector(size=0)
    bv_0.reset(1)
    assert str(bv_0) == ""


@pytest.mark.parametrize(
    ("bitstring", "expected_count"),
    [
        ("100111", 4),
        ("", 0),
    ],
)
def test_bit_count(bitstring: str, expected_count: int) -> None:
    """Tests standard bit counting across normal and empty vectors.

    Args:
        bitstring: Initial vector bitstring representation.
        expected_count: Expected number of bits set to 1.
    """
    bv = (
        BitVector.BitVector(bitstring=bitstring)
        if bitstring
        else BitVector.BitVector(size=0)
    )
    assert bv.bit_count() == expected_count


@pytest.mark.parametrize(
    ("bitstring", "expected_count"),
    [
        ("", 0),
        ("100111" + "0" * 20, 4),
        ("0" * 128, 0),
        ("1" * 64 + "0" * 64, 64),
    ],
)
def test_count_bits_sparse(bitstring: str, expected_count: int) -> None:
    """Tests sparse bit counting across empty and zero-padded vectors.

    Args:
        bitstring: Initial vector bitstring representation.
        expected_count: Expected number of bits set to 1.
    """
    bv = (
        BitVector.BitVector(bitstring=bitstring)
        if bitstring
        else BitVector.BitVector(size=0)
    )
    assert bv.count_bits_sparse() == expected_count


def test_set_value() -> None:
    """Tests mutating an existing BitVector via set_value."""
    bv = BitVector.BitVector(intVal=7, size=16)
    bv.set_value(intVal=45)
    assert str(bv) == "101101"

    bv.set_value(bitstring="1100")
    assert str(bv) == "1100"


def test_set_value_positional_args_error() -> None:
    """Verifies that passing positional arguments to set_value raises TypeError."""
    bv = BitVector.BitVector(intVal=7, size=16)
    with pytest.raises(TypeError, match="takes 1 positional argument"):
        bv.set_value(123)  # type: ignore[misc,arg-type]  # ty: ignore[too-many-positional-arguments]


def test_set_value_invalid_keyword_error() -> None:
    """Verifies passing unexpected keyword arguments to set_value raises TypeError."""
    bv = BitVector.BitVector(intVal=7, size=16)
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        # pylint: disable-next=unexpected-keyword-arg
        bv.set_value(invalid_param=123)  # type: ignore[call-arg]  # ty: ignore[unknown-argument]


@pytest.mark.parametrize(
    ("method_name", "bv1_str", "bv2_str", "err_match"),
    [
        ("jaccard_similarity", "000", "000", "Jaccard called on two zero vectors"),
        ("jaccard_similarity", "1", "10", "must be of equal length"),
        ("jaccard_distance", "1", "10", "vectors of unequal length"),
        ("hamming_distance", "1", "10", "vectors of unequal length"),
    ],
)
def test_distance_metrics_raise_error(
    method_name: str, bv1_str: str, bv2_str: str, err_match: str
) -> None:
    """Verifies distance metrics raise ValueError on invalid inputs.

    Args:
        method_name: Metric method name ('jaccard_similarity', etc.).
        bv1_str: Bitstring for the first vector.
        bv2_str: Bitstring for the second vector.
        err_match: Expected error message substring.
    """
    bv1 = BitVector.BitVector(bitstring=bv1_str)
    bv2 = BitVector.BitVector(bitstring=bv2_str)
    method = getattr(bv1, method_name)
    with pytest.raises(ValueError, match=err_match):
        method(bv2)


@pytest.mark.parametrize(
    ("method_name", "bv1_str", "bv2_str", "expected"),
    [
        ("jaccard_similarity", "11111111", "00101011", 0.5),
        ("jaccard_distance", "11111111", "00101011", 0.5),
        ("hamming_distance", "11111111", "00101011", 4),
    ],
)
def test_distance_metrics(
    method_name: str, bv1_str: str, bv2_str: str, expected: float | int
) -> None:
    """Tests similarity and distance metrics on equal-length vectors.

    Args:
        method_name: Metric method name ('jaccard_similarity', etc.).
        bv1_str: Bitstring for the first vector.
        bv2_str: Bitstring for the second vector.
        expected: Expected distance or similarity numerical result.
    """
    bv1 = BitVector.BitVector(bitstring=bv1_str)
    bv2 = BitVector.BitVector(bitstring=bv2_str)
    method = getattr(bv1, method_name)
    res = method(bv2)
    if isinstance(expected, float):
        assert abs(res - expected) < 1e-9
    else:
        assert res == expected


def test_next_set_bit_raises_error() -> None:
    """Verifies calling next_set_bit with a negative index raises ValueError."""
    bv = BitVector.BitVector(bitstring="00000000000001")
    with pytest.raises(ValueError, match="from_index must be nonnegative"):
        bv.next_set_bit(-1)


@pytest.mark.parametrize(
    ("bitstring", "start_idx", "expected_idx"),
    [
        ("00000000000001", 5, 13),
        ("0" * 20, 0, -1),
        ("0100000000000000", 2, -1),
    ],
)
def test_next_set_bit(bitstring: str, start_idx: int, expected_idx: int) -> None:
    """Tests scanning forward for the next bit set to 1.

    Args:
        bitstring: Initial vector bitstring representation.
        start_idx: The starting index for scanning.
        expected_idx: Expected index of the next set bit (-1 if none found).
    """
    bv = BitVector.BitVector(bitstring=bitstring)
    assert bv.next_set_bit(start_idx) == expected_idx


def test_rank_of_bit_set_at_index_raises_error() -> None:
    """Verifies rank query on an unset bit raises ValueError."""
    bv = BitVector.BitVector(bitstring="01010101011100")
    with pytest.raises(ValueError, match="the arg bit not set"):
        bv.rank_of_bit_set_at_index(0)


def test_rank_of_bit_set_at_index() -> None:
    """Tests calculating the rank (number of preceding 1 bits) of a set bit."""
    bv = BitVector.BitVector(bitstring="01010101011100")
    assert bv.rank_of_bit_set_at_index(10) == 6


@pytest.mark.parametrize(
    ("bitstring", "sparse", "expected"),
    [
        ("0000", False, False),
        ("0010", False, True),
        ("0011", False, False),
        ("0010", True, True),
        ("0011", True, False),
    ],
)
def test_is_power_of_2(bitstring: str, sparse: bool, expected: bool) -> None:
    """Tests power-of-two verification across standard and sparse evaluators.

    Args:
        bitstring: Initial vector bitstring representation.
        sparse: Whether to use is_power_of_2_sparse.
        expected: Expected boolean result.
    """
    bv = BitVector.BitVector(bitstring=bitstring)
    res = bv.is_power_of_2_sparse() if sparse else bv.is_power_of_2()
    assert res is expected


@pytest.mark.parametrize(
    ("bitstring", "expected"),
    [
        ("0001100000000000001", "1000000000000011000"),
        ("", ""),
    ],
)
def test_reverse(bitstring: str, expected: str) -> None:
    """Tests vector reversal on populated and empty vectors.

    Args:
        bitstring: Initial vector bitstring representation.
        expected: Expected bitstring representation after reversal.
    """
    bv = (
        BitVector.BitVector(bitstring=bitstring)
        if bitstring
        else BitVector.BitVector(size=0)
    )
    assert str(bv.reverse()) == expected


def test_gcd() -> None:
    """Tests greatest common divisor calculation between two vectors."""
    bv1 = BitVector.BitVector(bitstring="01100110")  # 102
    bv2 = BitVector.BitVector(bitstring="011010")  # 26
    assert int(bv1.gcd(bv2)) == 2
    assert int(bv2.gcd(bv1)) == 2


def test_multiplicative_inverse() -> None:
    """Tests modular multiplicative inverse existence and calculation."""
    bv_mod = BitVector.BitVector(intVal=32)
    bv_has_mi = BitVector.BitVector(intVal=17)
    res = bv_has_mi.multiplicative_inverse(bv_mod)
    assert res is not None
    assert int(res) == 17

    bv_no_mi = BitVector.BitVector(intVal=2)
    res_none = bv_no_mi.multiplicative_inverse(bv_mod)
    assert res_none is None


def test_gf_multiply() -> None:
    """Tests polynomial multiplication over GF(2)."""
    a = BitVector.BitVector(bitstring="0110001")
    b = BitVector.BitVector(bitstring="0110")
    c = a.gf_multiply(b)
    assert str(c) == "00010100110"

    b_zero = BitVector.BitVector(bitstring="0000")
    c_zero = a.gf_multiply(b_zero)
    assert int(c_zero) == 0


def test_gf_divide_by_modulus() -> None:
    """Tests polynomial division by modulus over GF(2^n) and error checking."""
    mod = BitVector.BitVector(bitstring="100011011")  # AES modulus
    n = 8
    a = BitVector.BitVector(bitstring="11100010110001")

    mod_long = BitVector.BitVector(bitstring="1" * 15)
    with pytest.raises(ValueError, match="Modulus bit pattern too long"):
        a.gf_divide_by_modulus(mod_long, n)

    quotient, remainder = a.gf_divide_by_modulus(mod, n)
    assert str(quotient) == "00000000111010"
    assert str(remainder) == "10001111"

    a_equal = copy.deepcopy(mod)
    _, r_eq = a_equal.gf_divide_by_modulus(mod, n)
    assert int(r_eq) == 0

    _, r_zero = BitVector.BitVector(bitstring="0").gf_divide_by_modulus(
        BitVector.BitVector(bitstring="1"), 1
    )
    assert int(r_zero) == 0


def test_gf_multiply_modular() -> None:
    """Tests modular polynomial multiplication over GF(2^8)."""
    mod = BitVector.BitVector(bitstring="100011011")  # AES modulus
    n = 8
    a = BitVector.BitVector(bitstring="0110001")
    b = BitVector.BitVector(bitstring="0110")
    c = a.gf_multiply_modular(b, mod, n)
    assert str(c) == "10100110"


def test_gf_mi() -> None:
    """Tests multiplicative inverse over GF(2^n) and non-existent fallback."""
    mod = BitVector.BitVector(bitstring="100011011")
    n = 8
    a = BitVector.BitVector(bitstring="00110011")
    mi = a.gf_MI(mod, n)
    assert str(mi) == "01101100"

    mod_no_mi = BitVector.BitVector(bitstring="1010")
    a_no_mi = BitVector.BitVector(bitstring="0010")
    res_no_mi = a_no_mi.gf_MI(mod_no_mi, 3)
    assert isinstance(res_no_mi, str)
    assert res_no_mi == "NO MI. However, the GCD of 0010 and 1010 is 010"


@pytest.mark.parametrize(
    ("bitstring", "bitlist", "expected"),
    [
        ("", None, []),
        (None, (1, 1, 1, 0, 0, 1), ["111", "00", "1"]),
        ("001100", None, ["00", "11", "00"]),
        ("0101", None, ["0", "1", "0", "1"]),
    ],
)
def test_runs(
    bitstring: str | None, bitlist: tuple[int, ...] | None, expected: list[str]
) -> None:
    """Tests extracting consecutive bit runs from vectors.

    Args:
        bitstring: Optional vector bitstring representation.
        bitlist: Optional vector bitlist representation.
        expected: Expected list of bit run strings.
    """
    if bitstring is not None:
        bv = (
            BitVector.BitVector(bitstring=bitstring)
            if bitstring
            else BitVector.BitVector(size=0)
        )
    elif bitlist is not None:
        bv = BitVector.BitVector(bitlist=list(bitlist))
    else:
        bv = BitVector.BitVector(size=0)
    assert bv.runs() == expected


def test_test_for_primality() -> None:
    """Tests Miller-Rabin and small-probe primality verification."""
    assert BitVector.BitVector(intVal=1, size=8).test_for_primality() == 0
    assert BitVector.BitVector(intVal=2, size=8).test_for_primality() == 1
    assert BitVector.BitVector(intVal=17, size=8).test_for_primality() == 1
    assert BitVector.BitVector(intVal=25, size=8).test_for_primality() == 0

    prob_19 = BitVector.BitVector(intVal=19, size=16).test_for_primality()
    assert prob_19 > 0.99
    prob_41 = BitVector.BitVector(intVal=41, size=16).test_for_primality()
    assert prob_41 > 0.99

    assert BitVector.BitVector(intVal=361, size=16).test_for_primality() == 0


def test_gen_random_bits(mocker) -> None:
    """Tests random bit vector generation with forced odd integer result."""
    bv = BitVector.BitVector(size=0).gen_random_bits(32)
    assert bv._size == 32
    # Check least significant bit is 1
    assert int(bv) & 1 == 1
    # Check the two most significant bits are 1
    assert bv[0] == 1
    assert bv[1] == 1

    # Check that it returns different values on consecutive calls
    bv2 = BitVector.BitVector(size=0).gen_random_bits(32)
    assert bv != bv2

    # Check that secrets.randbits is called
    mock_randbits = mocker.patch("BitVector.BitVector.secrets.randbits", return_value=0)
    bv_mock = BitVector.BitVector(size=0).gen_random_bits(32)
    mock_randbits.assert_called_once_with(32)
    assert int(bv_mock) == (1 | (1 << 31) | (2 << 29))


def test_min_canonical() -> None:
    """Tests finding the lexicographically smallest circular rotation."""
    bv = BitVector.BitVector(bitstring="1101")
    assert str(bv.min_canonical()) == "0111"
