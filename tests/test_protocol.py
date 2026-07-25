"""Unit tests for BitVectorProtocol.

Verifies that the BitVector class complies with the BitVectorProtocol.
"""

from typing import cast

from BitVector import BitVector, BitVectorProtocol


def test_protocol() -> None:
    bv = BitVector.from_int(42, size=8)
    bv_proto = cast(BitVectorProtocol, bv)
    assert int(bv_proto) == 42
    assert len(bv_proto) == 8
    assert str(bv_proto) == "00101010"
