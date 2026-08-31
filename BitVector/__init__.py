"""BitVector package.

This package provides a memory-efficient packed representation of bit arrays
and bit vectors using standard library array.
"""

from BitVector.BitVector import BitVector, __version__
from BitVector.mmap_bitvector import MmapBitVector
from BitVector.protocol import BitVectorProtocol

__all__ = ["__version__", "BitVector", "BitVectorProtocol", "MmapBitVector"]
