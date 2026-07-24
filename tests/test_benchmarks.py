"""Benchmarking suite for core BitVector operations.

Note:
    This file strictly avoids testing file I/O operations and avoids
    invoking the unfinished methods _not_yet_ready__add__ and
    _not_yet_ready__iadd__.
"""

import copy
import operator

import pytest

import BitVector


@pytest.fixture
def sample_bv1():
    return BitVector.BitVector(bitstring="01" * 500)


@pytest.fixture
def sample_bv2():
    return BitVector.BitVector(bitstring="001" * 333 + "0")


@pytest.fixture
def sample_bv_small():
    return BitVector.BitVector(bitstring="01010111" * 8)


@pytest.fixture
def gf_a():
    return BitVector.BitVector(bitstring="0110001")


@pytest.fixture
def gf_b():
    return BitVector.BitVector(bitstring="0110")


@pytest.fixture
def gf_mod():
    return BitVector.BitVector(bitstring="100011011")  # AES modulus


# --- Constructor Benchmarks ---


def test_bench_init_zeros(benchmark):
    benchmark(BitVector.BitVector, size=1000)


def test_bench_init_int(benchmark):
    benchmark(BitVector.BitVector, intVal=0x123456789ABCDEF0, size=64)


def test_bench_init_bitstring(benchmark):
    bitstr = "1010" * 250
    benchmark(BitVector.BitVector, bitstring=bitstr)


def test_bench_init_rawbytes(benchmark):
    data = b"\xaa\x55" * 50
    benchmark(BitVector.BitVector, rawbytes=data)


# --- Bitwise Operation Benchmarks ---


def test_bench_bitwise_and(benchmark, sample_bv1, sample_bv2):
    benchmark(operator.and_, sample_bv1, sample_bv2)


def test_bench_bitwise_or(benchmark, sample_bv1, sample_bv2):
    benchmark(operator.or_, sample_bv1, sample_bv2)


def test_bench_bitwise_xor(benchmark, sample_bv1, sample_bv2):
    benchmark(operator.xor, sample_bv1, sample_bv2)


def test_bench_invert(benchmark, sample_bv1):
    benchmark(operator.invert, sample_bv1)


# --- Arithmetic and Concatenation Benchmarks ---


def test_bench_add(benchmark, sample_bv1, sample_bv2):
    # Tests __add__, avoiding _not_yet_ready__add__
    benchmark(operator.add, sample_bv1, sample_bv2)


def test_bench_iadd(benchmark, sample_bv1, sample_bv2):
    # Tests __iadd__, avoiding _not_yet_ready__iadd__.
    # Uses pedantic with a setup function so self is not mutated across rounds.
    def setup():
        return (copy.deepcopy(sample_bv1), sample_bv2), {}

    def target(a, b):
        a += b

    benchmark.pedantic(target, setup=setup, rounds=100)


# --- Shifting and Permutation Benchmarks ---


def test_bench_shift_left(benchmark, sample_bv1):
    benchmark(operator.lshift, sample_bv1, 10)


def test_bench_shift_right(benchmark, sample_bv1):
    benchmark(operator.rshift, sample_bv1, 10)


def test_bench_ilshift(benchmark, sample_bv1):
    def _run():
        bv = sample_bv1[:]
        bv <<= 10

    benchmark(_run)


def test_bench_irshift(benchmark, sample_bv1):
    def _run():
        bv = sample_bv1[:]
        bv >>= 10

    benchmark(_run)


def test_bench_permute(benchmark, sample_bv1):
    perm = list(reversed(range(1000)))
    benchmark(sample_bv1.permute, perm)


# --- Slicing, Indexing, and Conversion Benchmarks ---


def test_bench_slice(benchmark, sample_bv1):
    benchmark(operator.getitem, sample_bv1, slice(100, 900))


def test_bench_getitem(benchmark, sample_bv1):
    benchmark(operator.getitem, sample_bv1, 500)


def test_bench_bit_count(benchmark, sample_bv1):
    benchmark(sample_bv1.bit_count)


def test_bench_int(benchmark, sample_bv1):
    benchmark(int, sample_bv1)


def test_bench_get_hex_string(benchmark, sample_bv1):
    benchmark(sample_bv1.get_bitvector_in_hex)


# --- Group 3: Distance, Similarity & Sparse Bit Searching ---


def test_bench_hamming_distance(benchmark, sample_bv1, sample_bv2):
    benchmark(sample_bv1.hamming_distance, sample_bv2)


def test_bench_jaccard_distance(benchmark, sample_bv1, sample_bv2):
    benchmark(sample_bv1.jaccard_distance, sample_bv2)


def test_bench_jaccard_similarity(benchmark, sample_bv1, sample_bv2):
    benchmark(sample_bv1.jaccard_similarity, sample_bv2)


def test_bench_count_bits_sparse(benchmark, sample_bv1):
    benchmark(sample_bv1.count_bits_sparse)


def test_bench_is_power_of_2(benchmark, sample_bv1):
    benchmark(sample_bv1.is_power_of_2)


def test_bench_is_power_of_2_sparse(benchmark, sample_bv1):
    benchmark(sample_bv1.is_power_of_2_sparse)


def test_bench_next_set_bit(benchmark, sample_bv1):
    benchmark(sample_bv1.next_set_bit, 10)


def test_bench_rank_of_bit_set_at_index(benchmark, sample_bv1):
    # Index 101 is 1 in "01" * 500
    benchmark(sample_bv1.rank_of_bit_set_at_index, 101)


def test_bench_runs(benchmark, sample_bv1):
    benchmark(sample_bv1.runs)


def test_bench_min_canonical(benchmark, sample_bv_small):
    def setup():
        return (), {}

    def target():
        bv = copy.deepcopy(sample_bv_small)
        return bv.min_canonical()

    benchmark.pedantic(target, setup=setup, rounds=50)


def test_bench_divide_into_two(benchmark, sample_bv1):
    benchmark(sample_bv1.divide_into_two)


# --- Group 4: Comparison & Equality Magic Methods ---


def test_bench_eq(benchmark, sample_bv1, sample_bv2):
    benchmark(operator.eq, sample_bv1, sample_bv2)


def test_bench_ne(benchmark, sample_bv1, sample_bv2):
    benchmark(operator.ne, sample_bv1, sample_bv2)


def test_bench_lt(benchmark, sample_bv1, sample_bv2):
    benchmark(operator.lt, sample_bv1, sample_bv2)


def test_bench_le(benchmark, sample_bv1, sample_bv2):
    benchmark(operator.le, sample_bv1, sample_bv2)


def test_bench_gt(benchmark, sample_bv1, sample_bv2):
    benchmark(operator.gt, sample_bv1, sample_bv2)


def test_bench_ge(benchmark, sample_bv1, sample_bv2):
    benchmark(operator.ge, sample_bv1, sample_bv2)


# --- Group 5: Container, Slicing & Mutation Methods ---


def test_bench_setitem_index(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv[50] = 1

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_setitem_slice(benchmark, sample_bv1, sample_bv_small):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv[10:74] = sample_bv_small

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_contains(benchmark, sample_bv1, sample_bv_small):
    benchmark(operator.contains, sample_bv1, sample_bv_small)


def test_bench_iter(benchmark, sample_bv1):
    benchmark(lambda: list(iter(sample_bv1)))


def test_bench_reversed(benchmark, sample_bv1):
    benchmark(lambda: list(reversed(sample_bv1)))


def test_bench_len(benchmark, sample_bv1):
    benchmark(len, sample_bv1)


def test_bench_length(benchmark, sample_bv1):
    benchmark(len, sample_bv1)


def test_bench_str(benchmark, sample_bv1):
    benchmark(str, sample_bv1)


def test_bench_get_bitvector_in_ascii(benchmark, sample_bv1):
    benchmark(sample_bv1.get_bitvector_in_ascii)


def test_bench_deepcopy(benchmark, sample_bv1):
    benchmark(copy.deepcopy, sample_bv1)


# --- Group 6: Alternative Shifting & Rotation Methods ---


def test_bench_shift_left_method(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.shift_left(10)

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_shift_right_method(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.shift_right(10)

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_shift_left_by_one(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.shift_left_by_one()

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_shift_right_by_one(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.shift_right_by_one()

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_circular_rot_left(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.circular_rot_left()

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_circular_rot_right(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.circular_rot_right()

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_circular_rotate_left_by_one(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.circular_rotate_left_by_one()

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_circular_rotate_right_by_one(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.circular_rotate_right_by_one()

    benchmark.pedantic(target, setup=setup, rounds=100)


# --- Group 7: In-Place Modification & Padding Methods ---


def test_bench_pad_from_left(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.pad_from_left(10)

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_pad_from_right(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.pad_from_right(10)

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_reset(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.reset(0)

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_reverse(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.reverse()

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_set_value(benchmark, sample_bv1):
    def setup():
        return (copy.deepcopy(sample_bv1),), {}

    def target(bv):
        bv.set_value(intVal=0x1234567890ABCDEF, size=64)

    benchmark.pedantic(target, setup=setup, rounds=100)


def test_bench_unpermute(benchmark, sample_bv1):
    perm = list(reversed(range(1000)))
    benchmark(sample_bv1.unpermute, perm)


# --- Group 2: Galois Field (GF) & Advanced Cryptographic Math ---


def test_bench_gf_multiply(benchmark, gf_a, gf_b):
    benchmark(gf_a.gf_multiply, gf_b)


def test_bench_gf_divide_by_modulus(benchmark, gf_mod):
    a = BitVector.BitVector(bitstring="11100010110001")
    benchmark(a.gf_divide_by_modulus, gf_mod, 8)


def test_bench_gf_multiply_modular(benchmark, gf_a, gf_b, gf_mod):
    benchmark(gf_a.gf_multiply_modular, gf_b, gf_mod, 8)


def test_bench_gf_mi(benchmark, gf_mod):
    a = BitVector.BitVector(bitstring="00110011")
    benchmark(a.gf_MI, gf_mod, 8)


def test_bench_multiplicative_inverse(benchmark):
    bv_mod = BitVector.BitVector(intVal=32)
    bv_has_mi = BitVector.BitVector(intVal=17)
    benchmark(bv_has_mi.multiplicative_inverse, bv_mod)


def test_bench_gcd(benchmark):
    bv1 = BitVector.BitVector(bitstring="01100110")
    bv2 = BitVector.BitVector(bitstring="011010")
    benchmark(bv1.gcd, bv2)


def test_bench_test_for_primality(benchmark):
    prob_19 = BitVector.BitVector(intVal=19, size=16)
    benchmark(prob_19.test_for_primality)


def test_bench_gen_random_bits(benchmark):
    bv = BitVector.BitVector(size=0)
    benchmark(bv.gen_random_bits, 64)
