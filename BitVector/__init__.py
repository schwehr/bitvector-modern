"""BitVector package.

This package provides a memory-efficient packed representation of bit arrays
and bit vectors using standard library array.
"""

from BitVector.BitVector import BitVector, __version__
from BitVector.protocol import BitVectorProtocol

__all__ = ["BitVector", "BitVectorProtocol", "__version__"]
