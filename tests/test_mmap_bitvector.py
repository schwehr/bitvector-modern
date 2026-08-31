from typing import cast

import pytest

from BitVector.mmap_bitvector import MmapBitVector
from BitVector.protocol import BitVectorProtocol


def test_mmap_basic():
    bv = MmapBitVector(size=4, intVal=0b1010)
    assert bv.int_val() == 10
    assert len(bv) == 4
    assert str(bv) == "1010"


def test_mmap_protocol_cast():
    bv = MmapBitVector(size=4, intVal=0b1010)
    p = cast(BitVectorProtocol, bv)
    assert p.int_val() == 10


def test_mmap_magic_methods():
    bv1 = MmapBitVector(size=4, intVal=0b1010)
    bv2 = MmapBitVector(size=4, intVal=0b0101)

    assert (bv1 ^ bv2).int_val() == 0b1111
    assert (bv1 & bv2).int_val() == 0b0000
    assert (bv1 | bv2).int_val() == 0b1111
    assert (~bv1).int_val() == 0b0101

    # __add__
    bv3 = bv1 + bv2
    assert len(bv3) == 8
    assert bv3.int_val() == 0b10100101

    # __iadd__
    bv4 = MmapBitVector(size=4, intVal=0b1010)
    bv4 += bv2
    assert len(bv4) == 8
    assert bv4.int_val() == 0b10100101

    # shifts
    assert (bv1 << 2).int_val() == 0b1000
    assert (bv1 >> 2).int_val() == 0b0010


def test_mmap_getitem_setitem():
    bv = MmapBitVector(size=4, intVal=0b1010)
    assert bv[0] == 1
    assert bv[1] == 0
    assert bv[2] == 1
    assert bv[3] == 0

    bv[0] = 0
    assert bv.int_val() == 0b0010

    bv[0:2] = MmapBitVector(size=2, intVal=0b11)
    assert bv.int_val() == 0b1110


def test_mmap_iter():
    bv = MmapBitVector(size=4, intVal=0b1010)
    assert list(bv) == [1, 0, 1, 0]


def test_mmap_comparisons():
    bv1 = MmapBitVector(size=4, intVal=0b1010)
    bv2 = MmapBitVector(size=4, intVal=0b1010)
    bv3 = MmapBitVector(size=4, intVal=0b1111)

    assert bv1 == bv2
    assert bv1 != bv3
    assert bv1 < bv3
    assert bv1 <= bv2
    assert bv3 > bv1
    assert bv2 >= bv1


def test_mmap_contains():
    bv = MmapBitVector(size=8, intVal=0b10101010)
    sub = MmapBitVector(size=4, intVal=0b1010)
    assert sub in bv


def test_mmap_properties():
    bv = MmapBitVector(size=8, intVal=0b00101000)
    assert bv.count_bits() == 2
    assert bv.count_bits_sparse() == 2
    assert bv.next_set_bit() == 2

    bv2 = MmapBitVector(size=8, intVal=0b00010000)
    assert bv2.is_power_of_2()
    assert bv2.is_power_of_2_sparse()


def test_mmap_bitstring_init():
    bv = MmapBitVector(bitstring="10101")
    assert len(bv) == 5
    assert bv.int_val() == 0b10101


def test_mmap_exceptions():
    bv = MmapBitVector(size=4, intVal=4)
    with pytest.raises(TypeError):
        bv["a"] = 1
    with pytest.raises(IndexError):
        bv[10] = 1
    with pytest.raises(TypeError):
        bv["a"]
    with pytest.raises(IndexError):
        bv[10]
    with pytest.raises(ValueError):
        bv[::2]
    with pytest.raises(ValueError):
        bv[::2] = 1


def test_mmap_slice_getitem():
    bv = MmapBitVector(size=8, intVal=0b11001010)
    sub = bv[2:6]
    assert len(sub) == 4
    assert sub.int_val() == 0b0010


def test_mmap_slice_out_of_bounds():
    bv = MmapBitVector(size=4, intVal=0b1010)
    sub = bv[5:8]
    assert len(sub) == 0


def test_mmap_del():
    bv = MmapBitVector(size=4, intVal=0b1010)
    bv.__del__()


def test_mmap_negative_indexing():
    bv = MmapBitVector(size=4, intVal=0b1010)
    assert bv[-1] == 0
    assert bv[-2] == 1
    bv[-1] = 1
    assert bv.int_val() == 0b1011


def test_mmap_padding_invert():
    bv = MmapBitVector(size=3, intVal=0b010)
    # inverts to 101 within the 3 bits
    inv = ~bv
    assert len(inv) == 3
    assert inv.int_val() == 0b101


def test_mmap_contains_empty():
    bv = MmapBitVector(size=4, intVal=0b1010)
    assert MmapBitVector(size=0) in bv
    assert MmapBitVector(size=8) not in bv


def test_mmap_next_set_bit_none():
    bv = MmapBitVector(size=4, intVal=0b0000)
    assert bv.next_set_bit() == -1


def test_mmap_int():
    bv = MmapBitVector(size=4, intVal=0b1010)
    assert int(bv) == 10


def test_mmap_clone():
    bv = MmapBitVector(size=4, intVal=0b1010)
    bv2 = bv._clone_empty(4)
    assert len(bv2) == 4
    assert bv2.int_val() == 0


def test_mmap_contains_edge_cases():
    bv = MmapBitVector(size=4, intVal=0b1010)
    assert MmapBitVector(size=5, intVal=0) not in bv


def test_mmap_iter_empty():
    bv = MmapBitVector(size=0)
    assert list(bv) == []


def test_mmap_str_empty():
    bv = MmapBitVector(size=0)
    assert str(bv) == ""


def test_mmap_not_eq():
    bv = MmapBitVector(size=4, intVal=0b1010)
    assert bv != MmapBitVector(size=5, intVal=0b1010)
    assert bv != 0b1010


def test_mmap_comparisons_unsupported():
    bv = MmapBitVector(size=4, intVal=0b1010)
    with pytest.raises(TypeError):
        bv < "hello"
    with pytest.raises(TypeError):
        bv <= "hello"
    with pytest.raises(TypeError):
        bv > "hello"
    with pytest.raises(TypeError):
        bv >= "hello"
    assert bv != "hello"


def test_mmap_uncovered_methods():
    bv = MmapBitVector(intVal=4)
    assert bv.size == 3
    # int()
    assert int(bv) == 4
    # lshift / rshift
    assert (bv << 1).int_val() == 0  # 3 bits, << 1 on 100 becomes 000
    assert (bv >> 1).int_val() == 2
    # is_power_of_2
    assert bv.is_power_of_2_sparse()


def test_mmap_exceptions2():
    bv = MmapBitVector(size=4, intVal=4)
    with pytest.raises(TypeError):
        bv.__lt__("str")
    with pytest.raises(TypeError):
        bv.__le__("str")
    with pytest.raises(TypeError):
        bv.__gt__("str")
    with pytest.raises(TypeError):
        bv.__ge__("str")


def test_mmap_eq_unsupported():
    bv = MmapBitVector(size=4, intVal=4)

    # This invokes the part of __eq__ where other doesn't have size and returns NotImplemented.
    # Python falls back to id() check, which returns False
    class Dummy:
        pass

    assert bv != Dummy()


def test_mmap_eq_different_size():
    bv1 = MmapBitVector(size=4, intVal=4)
    bv2 = MmapBitVector(size=5, intVal=4)
    assert bv1 != bv2


def test_mmap_eq_mmap():
    bv1 = MmapBitVector(size=4, intVal=4)
    bv2 = MmapBitVector(size=4, intVal=5)
    assert bv1 != bv2


def test_mmap_eq_int_val_only():
    bv1 = MmapBitVector(size=4, intVal=4)

    class DummyWithIntVal:
        size = 4

        def int_val(self):
            return 4

    assert bv1 == DummyWithIntVal()

    class DummyWithIntValBad:
        size = 4

        def int_val(self):
            return 5

    assert bv1 != DummyWithIntValBad()

    class DummyWithoutMmapOrIntVal:
        size = 4

    assert bv1 != DummyWithoutMmapOrIntVal()


def test_mmap_slice_steps():
    bv = MmapBitVector(size=4, intVal=0b1010)
    with pytest.raises(ValueError):
        bv[0:4:2]
    with pytest.raises(ValueError):
        bv[0:4:2] = 1


def test_mmap_contains_miss():
    bv = MmapBitVector(size=4, intVal=0b1010)
    sub = MmapBitVector(size=2, intVal=0b11)
    assert sub not in bv
