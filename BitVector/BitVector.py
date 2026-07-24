# SPDX-License-Identifier: PSF-2.0
# Copyright (c) 2021 Avinash Kak

"""A memory-efficient packed representation of bit arrays."""

from __future__ import annotations

__version__ = "0.0.4"

import array
import binascii
import copy
import itertools
import operator
import secrets
from typing import Any, BinaryIO, Iterator, Self, Sequence

_hexdict = {
    "0": "0000",
    "1": "0001",
    "2": "0010",
    "3": "0011",
    "4": "0100",
    "5": "0101",
    "6": "0110",
    "7": "0111",
    "8": "1000",
    "9": "1001",
    "a": "1010",
    "b": "1011",
    "c": "1100",
    "d": "1101",
    "e": "1110",
    "f": "1111",
}

# The internal storage type for the `array` standard library module.
# "Q" represents an unsigned long long integer (typically 64 bits),
# which is used for compact bitwise storage.
ARRAY_TYPE = "Q"

# Lookup table for 8-bit bit-reversal used in word/byte integer conversion.
_BIT_REV_8 = bytes(sum(((b >> i) & 1) << (7 - i) for i in range(8)) for b in range(256))


class BitVector:
    """A memory-efficient packed representation of bit arrays and bit vectors.

    Uses `array.array('Q')` unsigned integers for compact bitwise storage,
    manipulation, boolean logic, shifts, rotations, and GF(2^n) arithmetic.

    Attributes:
        vector: Underlying array storing packed integer words.
    """

    __slots__ = ("_size", "vector")
    _size: int
    vector: array.array[int]

    def __init__(
        self,
        *,
        size: int | None = None,
        intVal: int | None = None,
        bitlist: Any = None,
        bitstring: str | None = None,
        hexstring: str | None = None,
        rawbytes: bytes | None = None,
    ) -> None:
        """Initializes a BitVector instance from one of several possible input sources.

        You must specify exactly one keyword argument to determine the data
        source and size of the bit vector. Providing multiple data source
        arguments will raise a ValueError.

        Args:
            size: The desired number of bits for a zero-initialized vector (or
                used in conjunction with intVal).
            intVal: An integer value to convert into a bit vector.
            bitlist: A sequence or list of integers (0s and 1s) representing bits.
            bitstring: A string of binary characters ('0's and '1's).
            hexstring: A string of hexadecimal characters to convert to bits.
            rawbytes: A bytes object to unpack into a bit vector.

        Raises:
            ValueError: If no argument is provided, if mutually exclusive
                arguments are specified together, or if input values are invalid.
        """
        self._size = 0
        if intVal is not None:
            if (
                bitlist is not None
                or bitstring is not None
                or hexstring is not None
                or rawbytes is not None
            ):
                raise ValueError(
                    "When intVal is specified, you can only give a "
                    "value to the 'size' constructor arg"
                )
            if intVal == 0:
                bitlist = [0]
                if size is None:
                    self._size = 1
                elif size == 0:
                    raise ValueError(
                        "The value specified for size must be at least "
                        "as large as for the smallest bit vector possible "
                        "for intVal"
                    )
                else:
                    if size < len(bitlist):
                        raise ValueError(
                            "The value specified for size must be at least "
                            "as large as for the smallest bit vector "
                            "possible for intVal"
                        )
                    n = size - len(bitlist)
                    bitlist = [0] * n + bitlist
                    self._size = len(bitlist)
            else:
                hexVal = hex(intVal).lower().rstrip("l")
                hexVal = hexVal[2:]
                if len(hexVal) == 1:
                    hexVal = "0" + hexVal
                bitlist = [int(b) for h in hexVal for b in _hexdict[h]]
                i = 0
                while i < len(bitlist):
                    if bitlist[i] == 1:
                        break
                    i += 1
                del bitlist[0:i]
                if size is None:
                    self._size = len(bitlist)
                elif size == 0:
                    if size < len(bitlist):
                        raise ValueError(
                            "The value specified for size must be at least "
                            "as large as for the smallest bit vector possible "
                            "for intVal"
                        )
                else:
                    if size < len(bitlist):
                        raise ValueError(
                            "The value specified for size must be at least "
                            "as large as for the smallest bit vector possible "
                            "for intVal"
                        )
                    n = size - len(bitlist)
                    bitlist = [0] * n + bitlist
                    self._size = len(bitlist)
        elif size is not None and size >= 0:
            if (
                intVal is not None
                or bitlist is not None
                or bitstring is not None
                or hexstring is not None
                or rawbytes is not None
            ):
                raise ValueError(
                    "When size is specified (without an intVal), you cannot "
                    "give values to any other constructor args"
                )
            self._size = size
            eight_byte_ints_needed = (size + 63) // 64
            self.vector = array.array(ARRAY_TYPE, [0] * eight_byte_ints_needed)
            return
        elif bitstring is not None:
            if (
                size is not None
                or intVal is not None
                or bitlist is not None
                or hexstring is not None
                or rawbytes is not None
            ):
                raise ValueError(
                    "When a bitstring is specified, you cannot give "
                    "values to any other constructor args"
                )
            bitlist = list(map(int, list(bitstring)))
            self._size = len(bitlist)
        elif bitlist is not None:
            if (
                size is not None
                or intVal is not None
                or bitstring is not None
                or hexstring is not None
                or rawbytes is not None
            ):
                raise ValueError(
                    "When bits are specified, you cannot give values "
                    "to any other constructor args"
                )
            self._size = len(bitlist)
        elif hexstring is not None:
            if (
                size is not None
                or intVal is not None
                or bitlist is not None
                or bitstring is not None
                or rawbytes is not None
            ):
                raise ValueError(
                    "When bits are specified through hexstring, you "
                    "cannot give values to any other constructor args"
                )
            bitlist = [int(b) for h in hexstring.lower() for b in _hexdict[h]]
            self._size = len(bitlist)
        elif rawbytes is not None:
            if (
                size is not None
                or intVal is not None
                or bitlist is not None
                or bitstring is not None
                or hexstring is not None
            ):
                raise ValueError(
                    "When bits are specified through rawbytes, you "
                    "cannot give values to any other constructor args"
                )
            hex_str = binascii.hexlify(rawbytes).decode("ascii")
            bitlist = [int(b) for h in hex_str for b in _hexdict[h]]
            self._size = len(bitlist)
        else:
            raise ValueError("wrong arg(s) for constructor")
        eight_byte_ints_needed = (len(bitlist) + 63) // 64
        self.vector = array.array(ARRAY_TYPE, [0] * eight_byte_ints_needed)
        for idx, bit in enumerate(bitlist):
            self[idx] = bit

    @classmethod
    def from_string(cls, textstring: str) -> "BitVector":
        """Creates a BitVector instance from an ASCII or text string.

        Args:
            textstring: An ASCII or text string to convert to character bits.

        Returns:
            A new BitVector initialized with the bit representation of the string.
        """
        hex_str = "".join(f"{ord(c):02x}" for c in textstring)
        return cls(hexstring=hex_str)

    def __getitem__(self, pos: int | slice) -> Any:
        """Retrieves the bit or slice of bits from the designated position.

        Args:
            pos: An integer index or slice object specifying the bit position(s)
                to extract.

        Returns:
            An integer (0 or 1) if pos is an integer index, or a new BitVector
            instance containing the sliced bits if pos is a slice object.

        Raises:
            ValueError: If pos is out of valid bounds or if slice indices are
                illegal.
        """
        if not isinstance(pos, slice):
            if not isinstance(pos, int):
                raise TypeError("pos must be an integer or slice")
            if pos >= self._size or pos < -self._size:
                raise ValueError("index range error")
            if pos < 0:
                pos = self._size + pos
            return (self.vector[pos // 64] >> (pos & 63)) & 1
        slicebits = []
        i, j = pos.start, pos.stop
        if i is None and j is None:
            return copy.deepcopy(self)
        if i is None:
            if j >= 0:
                if j > len(self):
                    raise ValueError("illegal slice index values")
                for x in range(j):
                    slicebits.append(self[x])
                return BitVector(bitlist=slicebits)

            if abs(j) > len(self):
                raise ValueError("illegal slice index values")
            for x in range(len(self) - abs(j)):
                slicebits.append(self[x])
            return BitVector(bitlist=slicebits)
        if j is None:
            if i >= 0:
                if i > len(self):
                    raise ValueError("illegal slice index values")
                for x in range(i, len(self)):
                    slicebits.append(self[x])
                return BitVector(bitlist=slicebits)

            if abs(i) > len(self):
                raise ValueError("illegal slice index values")
            for x in range(len(self) - abs(i), len(self)):
                slicebits.append(self[x])
            return BitVector(bitlist=slicebits)
        if 0 <= j < i:
            raise ValueError("illegal slice index values")
        if i < 0 <= j < len(self) + i:
            raise ValueError("illegal slice index values")
        if j < 0 <= i:
            if len(self) + j < i:
                raise ValueError("illegal slice index values")

            for x in range(i, len(self) + j):
                slicebits.append(self[x])
            return BitVector(bitlist=slicebits)
        if self._size == 0:
            return BitVector(bitstring="")
        if i == j:
            return BitVector(bitstring="")
        for x in range(i, j):
            slicebits.append(self[x])
        return BitVector(bitlist=slicebits)

    def __xor__(self, other: BitVector) -> Self:
        """Performs a bitwise exclusive OR (XOR) with another bit vector.

        If the two bit vectors are not of equal length, the shorter vector is
        automatically padded with zero bits from the left before performing
        the XOR operation.

        Args:
            other: The second BitVector operand.

        Returns:
            A new BitVector instance containing the bitwise XOR result.
        """
        if self._size < other._size:
            bv1 = self._resize_pad_from_left(other._size - self._size)
            bv2 = other
        elif self._size > other._size:
            bv1 = self
            bv2 = other._resize_pad_from_left(self._size - other._size)
        else:
            bv1 = self
            bv2 = other
        res = self.__class__(size=bv1._size)
        lpb = map(operator.__xor__, bv1.vector, bv2.vector)
        res.vector = array.array(ARRAY_TYPE, lpb)
        return res

    def __and__(self, other: BitVector) -> Self:
        """Performs a bitwise AND with another bit vector.

        If the two bit vectors are not of equal length, the shorter vector is
        automatically padded with zero bits from the left before performing
        the AND operation.

        Args:
            other: The second BitVector operand.

        Returns:
            A new BitVector instance containing the bitwise AND result.
        """
        if self._size < other._size:
            bv1 = self._resize_pad_from_left(other._size - self._size)
            bv2 = other
        elif self._size > other._size:
            bv1 = self
            bv2 = other._resize_pad_from_left(self._size - other._size)
        else:
            bv1 = self
            bv2 = other
        res = self.__class__(size=bv1._size)
        lpb = map(operator.__and__, bv1.vector, bv2.vector)
        res.vector = array.array(ARRAY_TYPE, lpb)
        return res

    def __or__(self, other: BitVector) -> Self:
        """Performs a bitwise inclusive OR with another bit vector.

        If the two bit vectors are not of equal length, the shorter vector is
        automatically padded with zero bits from the left before performing
        the OR operation.

        Args:
            other: The second BitVector operand.

        Returns:
            A new BitVector instance containing the bitwise OR result.
        """
        if self._size < other._size:
            bv1 = self._resize_pad_from_left(other._size - self._size)
            bv2 = other
        elif self._size > other._size:
            bv1 = self
            bv2 = other._resize_pad_from_left(self._size - other._size)
        else:
            bv1 = self
            bv2 = other
        res = self.__class__(size=bv1._size)
        lpb = map(operator.__or__, bv1.vector, bv2.vector)
        res.vector = array.array(ARRAY_TYPE, lpb)
        return res

    def __invert__(self) -> Self:
        """Inverts all bits in the bit vector (bitwise NOT).

        Returns:
            A new BitVector instance where each 0 bit is replaced by 1 and
            each 1 bit is replaced by 0.
        """
        res = self.__class__(size=self._size)
        lpb = list(map(operator.__inv__, self.vector))
        res.vector = array.array(ARRAY_TYPE)
        for val in lpb:
            res.vector.append(val & 0xFFFFFFFFFFFFFFFF)
        return res

    def __add__(self, other: BitVector) -> Self:
        """Concatenates this bit vector with another bit vector.

        Creates a new bit vector containing all bits from this vector followed
        by all bits from the other vector.

        Args:
            other: The BitVector instance to append to the end of this vector.

        Returns:
            A new BitVector instance representing the concatenated bit string.
        """
        new_bv = self.__class__(size=0)
        if isinstance(self.vector, array.array) and isinstance(
            new_bv.vector, array.array
        ):
            new_bv.vector.frombytes(self.vector.tobytes())
        else:
            out_str = str(self) + str(other)
            return self.__class__(bitstring=out_str)
        new_bv._size = self._size
        new_bv += other
        return new_bv

    def __iadd__(self, other: BitVector) -> Self:
        """Appends another bit vector to this vector in-place.

        Extends the current bit vector's storage array by appending all bits
        from the argument vector without allocating a new BitVector object.

        Args:
            other: The BitVector instance to append to this vector.

        Returns:
            This BitVector instance (self) after in-place modification.

        Raises:
            TypeError: If the operand is not a BitVector instance.
        """
        if not isinstance(other, type(self)):
            raise TypeError(f"Can only join two BitVector objects, not {type(other)}")

        if not other._size:
            return self

        total_size = self._size + other._size
        start_word = self._size // 64
        offset = self._size % 64

        words_needed = (total_size + 63) // 64
        if words_needed > len(self.vector):
            self.vector.extend([0] * (words_needed - len(self.vector)))

        # Clean trailing unused bits in the current last word of self
        if offset > 0:
            self.vector[start_word] &= (1 << offset) - 1

        num_other_words = (other._size + 63) // 64

        if offset == 0:
            for i in range(num_other_words):
                self.vector[start_word + i] = other.vector[i]
        else:
            # Zero out remaining words in self to allow safe bitwise OR
            for idx in range(start_word + 1, words_needed):
                self.vector[idx] = 0

            shift_right = 64 - offset
            for i in range(num_other_words):
                w = other.vector[i]
                self.vector[start_word + i] |= (w << offset) & 0xFFFFFFFFFFFFFFFF
                high_part = w >> shift_right
                if high_part and (start_word + i + 1 < words_needed):
                    self.vector[start_word + i + 1] |= high_part

        last_word_bits = total_size % 64
        if last_word_bits != 0:
            self.vector[words_needed - 1] &= (1 << last_word_bits) - 1

        self._size = total_size
        return self

    def __len__(self) -> int:
        """Returns the number of bits stored in the bit vector.

        Returns:
            The integer number of valid bits in the vector.
        """
        return self._size

    def write_bits_to_stream_object(self, fp: Any) -> None:
        """Writes ASCII '0' and '1' characters representing vector bits to a stream.

        Unlike write_to_file, which writes packed binary bytes, this method
        outputs the text characters '0' and '1', making it suitable for text
        streams like io.StringIO.

        Args:
            fp: An open text stream or file-like object supporting write().
        """
        for bit_index in range(self._size):
            if self[bit_index] == 0:
                fp.write("0")
            else:
                fp.write("1")

    def divide_into_two(self) -> tuple[Self, Self]:
        """Splits an even-length bit vector into two equal halves.

        Returns:
            A tuple of two new BitVector instances: (left_half, right_half).

        Raises:
            ValueError: If the vector length is not even.
        """
        if self._size % 2 != 0:
            raise ValueError("must have even num bits")

        half = self._size // 2
        return self[:half], self[half:]

    def permute(self, permute_list: Sequence[int] | Any) -> Self:
        """Permutes the bits of the vector according to a permutation list.

        Args:
            permute_list: A sequence of integer indices specifying the new bit
                ordering.

        Returns:
            A new BitVector instance containing the permuted bits.

        Raises:
            ValueError: If any index in permute_list exceeds vector bounds.
        """
        if max(permute_list) > self._size - 1:
            raise ValueError("Bad permutation index")
        out_vector = self.__class__(size=len(permute_list))
        for i, idx in enumerate(permute_list):
            if self[idx]:
                out_vector[i] = 1
        return out_vector

    def unpermute(self, permute_list: Sequence[int] | Any) -> Self:
        """Restores the original bit ordering of a previously permuted vector.

        Args:
            permute_list: The sequence of integer indices that was originally
                used to permute the bit vector.

        Returns:
            A new BitVector instance with bits restored to their unpermuted order.

        Raises:
            ValueError: If indices are out of bounds or list size does not match.
        """
        if max(permute_list) > self._size - 1:
            raise ValueError("Bad permutation index")
        if self._size != len(permute_list):
            raise ValueError("Bad size for permute list")
        out_bv = self.__class__(size=self._size)
        for i, idx in enumerate(permute_list):
            if self[i]:
                out_bv[idx] = 1
        return out_bv

    def write_to_file(self, file_out: BinaryIO | Any) -> None:
        """Writes the packed binary byte representation of the vector to a file.

        The vector length must be an integral multiple of 8 bits. When opening
        files for writing on Windows, ensure binary mode ('wb') is used to avoid
        automatic newline translations.

        Args:
            file_out: An open binary file or stream object supporting write().

        Raises:
            ValueError: If the vector length is not a multiple of 8.
        """
        err_str = (
            "Only a bit vector whose length is a multiple of 8 can "
            "be written to a file. Use the padding functions to satisfy "
            "this constraint."
        )
        if self._size % 8:
            raise ValueError(err_str)
        for byte in range(int(self._size / 8)):
            value = 0
            for bit in range(8):
                value += self[byte * 8 + (7 - bit)] << bit
            file_out.write(bytes([value]))

    def __int__(self) -> int:
        """Calculates and returns the unsigned integer value of the bit vector.

        Returns:
            The integer represented by the binary bits in big-endian order.
        """
        if self._size == 0:
            return 0
        raw = self.vector.tobytes()
        int_val = int.from_bytes(raw.translate(_BIT_REV_8), "big")
        unused_bits = (len(raw) * 8) - self._size
        if unused_bits > 0:
            int_val >>= unused_bits
        return int_val

    def get_bitvector_in_ascii(self) -> str:
        """Converts the bit vector into an ASCII character string.

        Every 8 bits in the vector are converted into their corresponding ASCII
        character. The vector size must be a multiple of 8.

        Returns:
            An ASCII string decoded from the 8-bit blocks of the vector.

        Raises:
            ValueError: If the vector size is not an integral multiple of 8.
        """
        if self._size % 8:
            raise ValueError(
                "The bitvector for get_bitvector_in_ascii() "
                "must be an integral multiple of 8 bits"
            )
        return "".join(chr(int(self[i : i + 8])) for i in range(0, self._size, 8))

    def get_bitvector_in_hex(self) -> str:
        """Converts the bit vector into a hexadecimal representation string.

        Every 4 bits are converted into their corresponding hex digit (0-9, a-f).
        The vector size must be a multiple of 4.

        Returns:
            A lowercase hexadecimal string representing the vector bits.

        Raises:
            ValueError: If the vector size is not an integral multiple of 4.
        """
        if self._size % 4:
            raise ValueError(
                "The bitvector for get_bitvector_in_hex() "
                "must be an integral multiple of 4 bits"
            )
        return "".join(
            hex(int(self[i : i + 4])).replace("0x", "") for i in range(0, self._size, 4)
        )

    def __lshift__(self, n: int) -> Self:
        """Performs a circular left rotation by n bit positions.

        Rotates the bit vector circularly to the left n times, returning a new
        BitVector instance without modifying self. Negative values for n delegate
        to a circular right rotation.

        Args:
            n: The integer number of positions to circularly rotate left.

        Returns:
            A new BitVector instance containing the circularly rotated bits.

        Raises:
            ValueError: If attempting to rotate an empty bit vector.
        """
        res = copy.deepcopy(self)
        res <<= n
        return res

    def __ilshift__(self, n: int) -> Self:
        """Performs an in-place circular left rotation by n bit positions.

        Rotates the bit vector circularly to the left n times in-place. Negative
        values for n delegate to an in-place circular right rotation.

        Args:
            n: The integer number of positions to circularly rotate left.

        Returns:
            This BitVector instance (self) after in-place rotation.

        Raises:
            ValueError: If attempting to rotate an empty bit vector.
        """
        if self._size == 0:
            raise ValueError("Circular shift of an empty vector makes no sense")
        if n < 0:
            return self.__irshift__(abs(n))
        for _ in range(n):
            self.circular_rotate_left_by_one()
        return self

    def __rshift__(self, n: int) -> Self:
        """Performs a circular right rotation by n bit positions.

        Rotates the bit vector circularly to the right n times, returning a new
        BitVector instance without modifying self. Negative values for n delegate
        to a circular left rotation.

        Args:
            n: The integer number of positions to circularly rotate right.

        Returns:
            A new BitVector instance containing the circularly rotated bits.

        Raises:
            ValueError: If attempting to rotate an empty bit vector.
        """
        res = copy.deepcopy(self)
        res >>= n
        return res

    def __irshift__(self, n: int) -> Self:
        """Performs an in-place circular right rotation by n bit positions.

        Rotates the bit vector circularly to the right n times in-place. Negative
        values for n delegate to an in-place circular left rotation.

        Args:
            n: The integer number of positions to circularly rotate right.

        Returns:
            This BitVector instance (self) after in-place rotation.

        Raises:
            ValueError: If attempting to rotate an empty bit vector.
        """
        if self._size == 0:
            raise ValueError("Circular shift of an empty vector makes no sense")
        if n < 0:
            return self.__ilshift__(abs(n))
        for _ in range(n):
            self.circular_rotate_right_by_one()
        return self

    def circular_rotate_left_by_one(self) -> None:
        """Performs a one-bit in-place circular left rotation of the vector."""
        size = len(self.vector)
        bitstring_leftmost_bit = self.vector[0] & 1
        left_most_bits = list(map(operator.__and__, self.vector, [1] * size))
        left_most_bits.append(left_most_bits[0])
        del left_most_bits[0]
        self.vector = array.array(
            ARRAY_TYPE, map(operator.__rshift__, self.vector, [1] * size)
        )
        self.vector = array.array(
            ARRAY_TYPE,
            map(
                operator.__or__,
                self.vector,
                list(map(operator.__lshift__, left_most_bits, [63] * size)),
            ),
        )
        self[self._size - 1] = bitstring_leftmost_bit

    def circular_rotate_right_by_one(self) -> None:
        """Performs a one-bit in-place circular right rotation of the vector."""
        size = len(self.vector)
        bitstring_rightmost_bit = self[self._size - 1]
        right_most_bits = list(
            map(operator.__and__, self.vector, [0x8000000000000000] * size)
        )
        self.vector = array.array(
            ARRAY_TYPE, map(operator.__and__, self.vector, [~0x8000000000000000] * size)
        )
        right_most_bits.insert(0, bitstring_rightmost_bit)
        right_most_bits.pop()
        self.vector = array.array(
            ARRAY_TYPE, map(operator.__lshift__, self.vector, [1] * size)
        )
        self.vector = array.array(
            ARRAY_TYPE,
            map(
                operator.__or__,
                self.vector,
                list(map(operator.__rshift__, right_most_bits, [63] * size)),
            ),
        )
        self[0] = bitstring_rightmost_bit

    def circular_rot_left(self) -> None:
        """Performs a one-bit in-place circular left rotation without map()."""
        max_index = (self._size - 1) // 64
        left_most_bit = self.vector[0] & 1
        self.vector[0] = self.vector[0] >> 1
        for i in range(1, max_index + 1):
            left_bit = self.vector[i] & 1
            self.vector[i] = self.vector[i] >> 1
            self.vector[i - 1] |= left_bit << 63
        self[self._size - 1] = left_most_bit

    def circular_rot_right(self) -> None:
        """Performs a one-bit in-place circular right rotation without map()."""
        max_index = (self._size - 1) // 64
        right_most_bit = self[self._size - 1]
        self.vector[max_index] &= ~0x8000000000000000
        self.vector[max_index] = self.vector[max_index] << 1
        for i in range(max_index - 1, -1, -1):
            right_bit = self.vector[i] & 0x8000000000000000
            self.vector[i] &= ~0x8000000000000000
            self.vector[i] = self.vector[i] << 1
            self.vector[i + 1] |= right_bit >> 63
        self[0] = right_most_bit

    def shift_left_by_one(self) -> None:
        """Performs a one-bit in-place logical left shift (zero-filling right)."""
        size = len(self.vector)
        left_most_bits = list(map(operator.__and__, self.vector, [1] * size))
        left_most_bits.append(left_most_bits[0])
        del left_most_bits[0]
        self.vector = array.array(
            ARRAY_TYPE, map(operator.__rshift__, self.vector, [1] * size)
        )
        self.vector = array.array(
            ARRAY_TYPE,
            map(
                operator.__or__,
                self.vector,
                list(map(operator.__lshift__, left_most_bits, [63] * size)),
            ),
        )
        self[self._size - 1] = 0

    def shift_right_by_one(self) -> None:
        """Performs a one-bit in-place logical right shift (zero-filling left)."""
        size = len(self.vector)
        right_most_bits = list(
            map(operator.__and__, self.vector, [0x8000000000000000] * size)
        )
        self.vector = array.array(
            ARRAY_TYPE, map(operator.__and__, self.vector, [~0x8000000000000000] * size)
        )
        right_most_bits.insert(0, 0)
        right_most_bits.pop()
        self.vector = array.array(
            ARRAY_TYPE, map(operator.__lshift__, self.vector, [1] * size)
        )
        self.vector = array.array(
            ARRAY_TYPE,
            map(
                operator.__or__,
                self.vector,
                list(map(operator.__rshift__, right_most_bits, [63] * size)),
            ),
        )
        self[0] = 0

    def shift_left(self, n: int) -> Self:
        """Shifts the vector left by n bits in-place, filling right with zeros.

        Args:
            n: The integer number of bit positions to shift left.

        Returns:
            This BitVector instance (self) after in-place shifting.
        """
        if n <= 0:
            return self

        word_shift = n // 64
        bit_shift = n % 64

        vec = self.vector
        new_vec = array.array(ARRAY_TYPE, [0] * len(vec))

        if bit_shift == 0:
            for i in range(len(vec) - word_shift):
                new_vec[i] = vec[i + word_shift]
        else:
            for i in range(len(vec) - word_shift):
                val = vec[i + word_shift] >> bit_shift
                if i + word_shift + 1 < len(vec):
                    val |= (vec[i + word_shift + 1] & ((1 << bit_shift) - 1)) << (
                        64 - bit_shift
                    )
                new_vec[i] = val

        clear_from = max(0, self._size - n)
        clear_word = clear_from // 64
        clear_bit = clear_from % 64
        if clear_word < len(new_vec):
            new_vec[clear_word] &= (1 << clear_bit) - 1
            for i in range(clear_word + 1, len(new_vec)):
                new_vec[i] = 0

        self.vector = new_vec
        return self

    def shift_right(self, n: int) -> Self:
        """Shifts the vector right by n bits in-place, filling left with zeros.

        Args:
            n: The integer number of bit positions to shift right.

        Returns:
            This BitVector instance (self) after in-place shifting.
        """
        if n <= 0:
            return self

        word_shift = n // 64
        bit_shift = n % 64

        vec = self.vector
        new_vec = array.array(ARRAY_TYPE, [0] * len(vec))

        if bit_shift == 0:
            for i in range(word_shift, len(vec)):
                new_vec[i] = vec[i - word_shift]
        else:
            for i in range(word_shift, len(vec)):
                val = (vec[i - word_shift] << bit_shift) & 0xFFFFFFFFFFFFFFFF
                if i - word_shift - 1 >= 0:
                    val |= vec[i - word_shift - 1] >> (64 - bit_shift)
                new_vec[i] = val

        clear_until = min(self._size, n)
        clear_word = clear_until // 64
        clear_bit = clear_until % 64

        for i in range(clear_word):
            new_vec[i] = 0
        if clear_word < len(new_vec):
            new_vec[clear_word] &= ~((1 << clear_bit) - 1)

        last_word = self._size // 64
        last_bit = self._size % 64
        if last_bit > 0 and last_word < len(new_vec):
            new_vec[last_word] &= (1 << last_bit) - 1
            for i in range(last_word + 1, len(new_vec)):
                new_vec[i] = 0

        self.vector = new_vec
        return self

    def __setitem__(self, pos: int | slice, item: int | BitVector) -> None:
        """Assigns a bit or slice of bits at the specified position.

        Supports both index assignment (setting a single bit to 0 or 1) and
        slice assignment (replacing a slice of bits with another BitVector).

        Args:
            pos: An integer index or slice object indicating where to assign.
            item: An integer (0 or 1) for index assignment, or a BitVector for
                slice assignment.

        Raises:
            TypeError: If the assigned item has an incompatible type.
            ValueError: If slice lengths are incompatible or index is out of range.
        """
        # The following section is for slice assignment:
        if isinstance(pos, slice):
            if not isinstance(item, BitVector):
                raise TypeError(
                    "For slice assignment, the right hand side must be a BitVector"
                )
            if pos.start is None and pos.stop is None:
                return
            if pos.start is None:
                if pos.stop >= 0:
                    if pos.stop != len(item):
                        raise ValueError("incompatible lengths for slice assignment 1")
                    for i in range(pos.stop):
                        self[i] = item[i]
                else:
                    if len(self) - abs(pos.stop) != len(item):
                        raise ValueError("incompatible lengths for slice assignment 2")
                    for i in range(len(self) + pos.stop):
                        self[i] = item[i]
                return
            if pos.stop is None:
                if pos.start >= 0:
                    if (len(self) - pos.start) != len(item):
                        raise ValueError("incompatible lengths for slice assignment 3")
                    for i, val in enumerate(item):
                        self[pos.start + i] = val
                else:
                    if abs(pos.start) != len(item):
                        raise ValueError("incompatible lengths for slice assignment 4")
                    for i, val in enumerate(item):
                        self[len(self) + pos.start + i] = val
                return
            if pos.stop < 0 <= pos.start:
                if (len(self) + pos.stop - pos.start) != len(item):
                    raise ValueError("incompatible lengths for slice assignment 5")
                for i in range(pos.start, len(self) + pos.stop):
                    self[i] = item[i - pos.start]
                return
            if pos.start < 0 <= pos.stop:
                if (pos.stop - len(self) - pos.start) != len(item):
                    raise ValueError("incompatible lengths for slice assignment 6")
                for i in range(len(self) + pos.start, pos.stop):
                    self[i] = item[i - len(self) - pos.start]
                return
            if (pos.stop - pos.start) != len(item):
                raise ValueError("incompatible lengths for slice assignment 7")
            for i in range(pos.start, pos.stop):
                self[i] = item[i - pos.start]
            return
        # Index assignment:
        if item not in (0, 1):
            raise ValueError("incorrect value for a bit")
        if isinstance(pos, tuple):
            pos = pos[0]
        if not isinstance(pos, int):
            raise TypeError("pos must be an integer")
        if pos >= self._size or pos < -self._size:
            raise ValueError("index range error")
        if pos < 0:
            pos = self._size + pos
        block_index = pos // 64
        shift = pos & 63
        cv = self.vector[block_index]
        if (cv >> shift) & 1 != item:
            self.vector[block_index] = cv ^ (1 << shift)

    # Allow int() to work:

    def __iter__(self) -> Iterator[int]:
        """Yields individual bits sequentially from the vector.

        Yields:
            The integer bit value (0 or 1) at each position from left to right.
        """
        yield from (self[i] for i in range(self._size))

    def __reversed__(self) -> Iterator[int]:
        """Yields individual bits sequentially from right to left.

        Yields:
            The integer bit value (0 or 1) at each position from right to left.
        """
        size = self._size
        if size == 0:
            return
        vec = self.vector
        num_blocks = len(vec)
        val = vec[num_blocks - 1]
        for bit_idx in range((size - 1) & 63, -1, -1):
            yield (val >> bit_idx) & 1
        for b in range(num_blocks - 2, -1, -1):
            val = vec[b]
            for bit_idx in range(63, -1, -1):
                yield (val >> bit_idx) & 1

    def __str__(self) -> str:
        """Returns an ASCII string representation of the bit vector ('0's and '1's).

        Returns:
            A string of '0' and '1' characters matching the stored bits.
        """
        if self._size == 0:
            return ""
        return "".join(map(str, self))

    def __format__(self, format_spec: str) -> str:
        """Formats the bit vector for string interpolation.

        Attempts to format using the string representation first. If that raises
        a ValueError (e.g., when an integer format specifier like 'x' or 'b'
        is used), it falls back to formatting the integer representation.

        Args:
            format_spec: The format specification string.

        Returns:
            The formatted string.
        """
        try:
            return format(str(self), format_spec)
        except ValueError:
            return format(int(self), format_spec)

    def __eq__(self, other: object) -> bool:
        """Checks equality between this bit vector and another object.

        Args:
            other: The object to compare against.

        Returns:
            True if other is a BitVector of identical size and bit values,
            or if other is an int/float equal to the integer value of this
            vector. Otherwise False.
        """
        if isinstance(other, BitVector):
            if self._size != other._size:
                return False

            if self.vector == other.vector:
                return True

            rem = self._size & 63
            if rem == 0:
                return False

            mask = (1 << rem) - 1
            if len(self.vector) == 1:
                return (self.vector[0] & mask) == (other.vector[0] & mask)

            return self.vector[:-1] == other.vector[:-1] and (
                self.vector[-1] & mask
            ) == (other.vector[-1] & mask)

        if isinstance(other, (int, float)):
            return int(self) == other

        return False

    def __ne__(self, other: object) -> bool:
        """Checks inequality between this bit vector and another object.

        Args:
            other: The object to compare against.

        Returns:
            True if the objects are not equal, otherwise False.
        """
        return not self == other

    def __lt__(self, other: object) -> bool:
        """Checks if this bit vector is strictly less than another object.

        Comparison is performed by evaluating integer values.

        Args:
            other: The BitVector, int, or float instance to compare against.

        Returns:
            True if this vector's integer value is less than other's.

        Raises:
            TypeError: If other is not a BitVector, int, or float.
        """
        if isinstance(other, BitVector):
            return int(self) < int(other)

        if isinstance(other, (int, float)):
            return int(self) < other

        raise TypeError(
            f"'<' not supported between instances of 'BitVector' and '{type(other).__name__}'"
        )

    def __le__(self, other: object) -> bool:
        """Checks if this bit vector is less than or equal to another object.

        Comparison is performed by evaluating integer values.

        Args:
            other: The BitVector, int, or float instance to compare against.

        Returns:
            True if this vector's integer value is less than or equal to other's.

        Raises:
            TypeError: If other is not a BitVector, int, or float.
        """
        if isinstance(other, BitVector):
            return int(self) <= int(other)

        if isinstance(other, (int, float)):
            return int(self) <= other

        raise TypeError(
            f"'<=' not supported between instances of 'BitVector' and '{type(other).__name__}'"
        )

    def __gt__(self, other: object) -> bool:
        """Checks if this bit vector is strictly greater than another object.

        Comparison is performed by evaluating integer values.

        Args:
            other: The BitVector, int, or float instance to compare against.

        Returns:
            True if this vector's integer value is greater than other's.

        Raises:
            TypeError: If other is not a BitVector, int, or float.
        """
        if isinstance(other, BitVector):
            return int(self) > int(other)

        if isinstance(other, (int, float)):
            return int(self) > other

        raise TypeError(
            f"'>' not supported between instances of 'BitVector' and '{type(other).__name__}'"
        )

    def __ge__(self, other: object) -> bool:
        """Checks if this bit vector is greater than or equal to another object.

        Comparison is performed by evaluating integer values.

        Args:
            other: The BitVector, int, or float instance to compare against.

        Returns:
            True if this vector's integer value is greater than or equal to other's.

        Raises:
            TypeError: If other is not a BitVector, int, or float.
        """
        if isinstance(other, BitVector):
            return int(self) >= int(other)

        if isinstance(other, (int, float)):
            return int(self) >= other

        raise TypeError(
            f"'>=' not supported between instances of 'BitVector' and '{type(other).__name__}'"
        )

    def __deepcopy__(self, memo: dict[int, Any] | None = None) -> Self:
        """Creates a deep copy of the bit vector for the copy module.

        Args:
            memo: An optional dictionary tracking copied objects to prevent
                infinite recursion.

        Returns:
            A new BitVector instance identical to this vector.
        """
        if memo is None:
            memo = {}
        new_bv = self.__class__(size=0)
        memo[id(self)] = new_bv
        if isinstance(self.vector, array.array):
            new_bv.vector = array.array(ARRAY_TYPE, self.vector)
        else:
            new_bv.vector = copy.deepcopy(self.vector, memo)
        new_bv._size = self._size
        return new_bv

    def _resize_pad_from_left(self, n: int) -> Self:
        """Resizes the bit vector by padding with n zeros from the left.

        Args:
            n: The integer number of zero bits to prepend to the bit vector.

        Returns:
            A new BitVector instance containing the left-padded bits.
        """
        new_bv = copy.deepcopy(self)
        new_bv.pad_from_left(n)
        return new_bv

    def pad_from_left(self, n: int) -> None:
        """Pads the bit vector with n zeros from the left in-place.

        Args:
            n: The integer number of zero bits to prepend to the vector.
        """
        if n <= 0:
            return

        s1 = self._size
        if s1 == 0:
            self._size = n
            words_needed = (n + 63) // 64
            self.vector = array.array(ARRAY_TYPE, [0] * words_needed)
            return

        total_size = s1 + n
        words_needed = (total_size + 63) // 64
        word_shift = n // 64
        bit_shift = n % 64

        num_old_words = (s1 + 63) // 64
        new_vec = array.array(ARRAY_TYPE, [0] * words_needed)

        if bit_shift == 0:
            for i in range(num_old_words):
                new_vec[i + word_shift] = self.vector[i]
        else:
            shift_right = 64 - bit_shift
            for i in range(num_old_words):
                w = self.vector[i]
                new_vec[i + word_shift] |= (w << bit_shift) & 0xFFFFFFFFFFFFFFFF
                high_part = w >> shift_right
                if high_part and (i + word_shift + 1 < words_needed):
                    new_vec[i + word_shift + 1] |= high_part

        last_word_bits = total_size % 64
        if last_word_bits != 0:
            new_vec[words_needed - 1] &= (1 << last_word_bits) - 1

        self.vector = new_vec
        self._size = total_size

    def pad_from_right(self, n: int) -> None:
        """Pads the bit vector with n zeros from the right in-place.

        Args:
            n: The integer number of zero bits to append to the vector.
        """
        if n <= 0:
            return

        total_size = self._size + n
        words_needed = (total_size + 63) // 64
        if words_needed > len(self.vector):
            self.vector.extend([0] * (words_needed - len(self.vector)))

        self._size = total_size

    def __contains__(self, otherBitVec: BitVector) -> bool:
        """Checks if a sub-vector is contained within this bit vector.

        Supports the 'in' and 'not in' operators for subsequence searching.

        Args:
            otherBitVec: The BitVector subsequence to search for.

        Returns:
            True if otherBitVec appears as a contiguous subsequence, else False.

        Raises:
            ValueError: If this vector is empty or shorter than otherBitVec.
        """
        if self._size == 0:
            raise ValueError("First arg bitvec has no bits")

        if self._size < otherBitVec._size:
            raise ValueError("First arg bitvec too short")

        max_index = self._size - otherBitVec._size + 1
        for i in range(max_index):
            if self[i : i + otherBitVec._size] == otherBitVec:
                return True
        return False

    def reset(self, val: int) -> Self:
        """Resets all bits in the vector to either 0 or 1 in-place.

        Args:
            val: The target bit value (0 or 1) to set across the entire vector.

        Returns:
            This BitVector instance (self) after resetting.

        Raises:
            ValueError: If val is not 0 or 1.
        """
        if val not in (0, 1):
            raise ValueError("Incorrect reset argument")
        if val == 0:
            self.vector = array.array(ARRAY_TYPE, [0] * len(self.vector))
        else:
            word_size = self.vector.itemsize * 8
            full_word = (1 << word_size) - 1
            self.vector = array.array(ARRAY_TYPE, [full_word] * len(self.vector))
            rem = self._size % word_size
            if rem > 0 and len(self.vector) > 0:
                self.vector[-1] = (1 << rem) - 1
        return self

    def count_bits(self) -> int:
        """Counts the total number of set bits (1s) in the bit vector.

        Returns:
            The integer count of bits set to 1.
        """
        return sum(self)

    def set_value(
        self,
        *,
        size: int | None = None,
        intVal: int | None = None,
        bitlist: Any = None,
        bitstring: str | None = None,
        hexstring: str | None = None,
        rawbytes: bytes | None = None,
    ) -> None:
        """Reinitializes the bit vector in-place with new data.

        Accepts the same keyword arguments as the class constructor to overwrite
        the current vector's size and contents.

        Args:
            size: The desired number of bits for a zero-initialized vector (or
                used in conjunction with intVal).
            intVal: An integer value to convert into a bit vector.
            bitlist: A sequence or list of integers (0s and 1s) representing bits.
            bitstring: A string of binary characters ('0's and '1's).
            hexstring: A string of hexadecimal characters to convert to bits.
            rawbytes: A bytes object to unpack into a bit vector.

        Raises:
            ValueError: If no argument is provided, if mutually exclusive
                arguments are specified together, or if input values are invalid.
        """
        BitVector.__init__(
            self,
            size=size,
            intVal=intVal,
            bitlist=bitlist,
            bitstring=bitstring,
            hexstring=hexstring,
            rawbytes=rawbytes,
        )

    def count_bits_sparse(self) -> int:
        """Counts set bits using Brian Kernighan's algorithm for sparse vectors.

        Optimized for large bit vectors where very few bits are set to 1.

        Returns:
            The integer count of bits set to 1.
        """
        num = 0
        for intval in self.vector:
            if intval == 0:
                continue
            c = 0
            iv = intval
            while iv > 0:
                iv = iv & (iv - 1)
                c = c + 1
            num = num + c
        return num

    def jaccard_similarity(self, other: BitVector) -> float:
        """Calculates the Jaccard similarity coefficient between two vectors.

        Args:
            other: A BitVector of equal length to compare against.

        Returns:
            A floating-point coefficient between 0.0 and 1.0.

        Raises:
            ValueError: If vectors are of unequal length or both zero.
        """
        if int(self) == 0 and int(other) == 0:
            raise ValueError("Jaccard called on two zero vectors --- NOT ALLOWED")
        if self._size != other._size:
            raise ValueError(
                "bitvectors for comparing with Jaccard must be of equal length"
            )
        intersect = self & other
        union = self | other
        return intersect.count_bits_sparse() / float(union.count_bits_sparse())

    def jaccard_distance(self, other: BitVector) -> float:
        """Calculates the Jaccard distance coefficient between two vectors.

        Args:
            other: A BitVector of equal length to compare against.

        Returns:
            A floating-point distance between 0.0 and 1.0 (1 - similarity).

        Raises:
            ValueError: If vectors are of unequal length.
        """
        if self._size != other._size:
            raise ValueError("vectors of unequal length")
        return 1 - self.jaccard_similarity(other)

    def hamming_distance(self, other: BitVector) -> int:
        """Calculates the Hamming distance between two vectors of equal length.

        Args:
            other: A BitVector of equal length to compare against.

        Returns:
            The integer number of bit positions where the two vectors disagree.

        Raises:
            ValueError: If vectors are of unequal length.
        """
        if self._size != other._size:
            raise ValueError("vectors of unequal length")
        diff = self ^ other
        return diff.count_bits_sparse()

    def next_set_bit(self, from_index: int = 0) -> int:
        """Finds the index of the next set bit starting from from_index.

        Args:
            from_index: The non-negative bit index at which to start searching.

        Returns:
            The integer index of the next set bit (1), or -1 if none is found.

        Raises:
            ValueError: If from_index is negative.
        """
        if from_index < 0:
            raise ValueError("from_index must be nonnegative")
        i = from_index
        v = self.vector
        vec_len = len(v)
        o = i >> 6
        s = i & 0x3F
        i = o << 6
        while o < vec_len:
            h = v[o]
            if h:
                i += s
                m = 1 << s
                while m != (1 << 0x40):
                    if h & m:
                        return i
                    m <<= 1
                    i += 1
            else:
                i += 0x40
            s = 0
            o += 1
        return -1

    def rank_of_bit_set_at_index(self, position: int) -> int:
        """Calculates the rank (count of set bits up to position) of a set bit.

        Args:
            position: The target bit index, which must currently be set to 1.

        Returns:
            The total number of set bits from index 0 up to position (inclusive).

        Raises:
            ValueError: If the bit at position is not set to 1.
        """
        if self[position] != 1:
            raise ValueError("the arg bit not set")
        bv = self[0 : position + 1]
        return bv.count_bits()

    def is_power_of_2(self) -> bool:
        """Checks whether the integer value of the vector is a power of two.

        Returns:
            True if the integer representation is a power of two, else False.
        """
        if int(self) == 0:
            return False
        bv = self & BitVector(intVal=int(self) - 1)
        if int(bv) == 0:
            return True
        return False

    def is_power_of_2_sparse(self) -> bool:
        """Checks whether the vector is a power of two using sparse bit counting.

        Optimized for large vectors where sparse bit counting is faster.

        Returns:
            True if exactly one bit is set to 1, else False.
        """
        return self.count_bits_sparse() == 1

    def reverse(self) -> Self:
        """Reverses the order of bits in the vector (left-to-right becomes right-to-left).

        Returns:
            A new BitVector instance with bits in reversed order.
        """
        new_bv = self.__class__(size=self._size)
        for i in range(self._size):
            if self[self._size - 1 - i]:
                new_bv[i] = 1
        return new_bv

    def gcd(self, other: BitVector) -> Self:
        """Calculates the greatest common divisor (GCD) using Euclid's algorithm.

        Args:
            other: A BitVector representing the second integer operand.

        Returns:
            A new BitVector instance containing the GCD of the two integer values.
        """
        a = int(self)
        b = int(other)
        if a < b:
            a, b = b, a
        while b != 0:
            a, b = b, a % b
        return self.__class__(intVal=a)

    def multiplicative_inverse(self, modulus: BitVector) -> Self | None:
        """Calculates the modular multiplicative inverse using integer arithmetic.

        Uses the Extended Euclidean Algorithm. For field inverses in GF(2^n),
        use gf_MI instead.

        Args:
            modulus: A BitVector representing the integer modulus.

        Returns:
            A new BitVector with the multiplicative inverse modulo modulus,
            or None if no inverse exists.
        """
        MOD = mod = int(modulus)
        num = int(self)
        x, x_old = 0, 1
        y, y_old = 1, 0
        while mod:
            quotient = num // mod
            num, mod = mod, num % mod
            x, x_old = x_old - x * quotient, x
            y, y_old = y_old - y * quotient, y
        if num != 1:
            return None

        MI = (x_old + MOD) % MOD
        return self.__class__(intVal=MI)

    def gf_multiply(self, b: BitVector) -> Self:
        """Multiplies two polynomials in Galois Field GF(2).

        Args:
            b: The second polynomial BitVector operand.

        Returns:
            A new BitVector containing the GF(2) product of the two polynomials.
        """
        a = copy.deepcopy(self)
        b_copy = copy.deepcopy(b)
        result = self.__class__(size=len(a) + len(b_copy))
        a.pad_from_left(len(result) - len(a))
        b_copy.pad_from_left(len(result) - len(b_copy))
        for i, bit in enumerate(b_copy):
            if bit == 1:
                power = len(b_copy) - i - 1
                a_copy = copy.deepcopy(a)
                a_copy.shift_left(power)
                result ^= a_copy
        return result

    def gf_divide_by_modulus(self, mod: BitVector, n: int) -> tuple[Self, Self]:
        """Divides this polynomial by a modulus polynomial in GF(2^n).

        Args:
            mod: A BitVector representing the modulus polynomial.
            n: The integer degree n of the Galois Field GF(2^n).

        Returns:
            A tuple of two BitVectors: (quotient, remainder).

        Raises:
            ValueError: If the modulus polynomial is too long for GF(2^n).
        """
        num = self
        if len(mod) > n + 1:
            raise ValueError("Modulus bit pattern too long")
        quotient = self.__class__(intVal=0, size=len(num))
        remainder = copy.deepcopy(num)
        i = 0
        while 1:
            i = i + 1
            if i == len(num):
                break
            mod_highest_power = len(mod) - mod.next_set_bit(0) - 1
            if remainder.next_set_bit(0) == -1:
                remainder_highest_power = 0
            else:
                remainder_highest_power = len(remainder) - remainder.next_set_bit(0) - 1
            if (remainder_highest_power < mod_highest_power) or int(remainder) == 0:
                break

            exponent_shift = remainder_highest_power - mod_highest_power
            quotient[len(quotient) - exponent_shift - 1] = 1
            quotient_mod_product = copy.deepcopy(mod)
            quotient_mod_product.pad_from_left(len(remainder) - len(mod))
            quotient_mod_product.shift_left(exponent_shift)
            remainder = remainder ^ quotient_mod_product
        if len(remainder) > n:
            remainder = remainder[len(remainder) - n :]
        return quotient, remainder

    def gf_multiply_modular(self, b: BitVector | Any, mod: BitVector, n: int) -> Self:
        """Performs modular polynomial multiplication in Galois Field GF(2^n).

        Args:
            b: The second polynomial operand BitVector.
            mod: The modulus polynomial BitVector.
            n: The integer degree n of the Galois Field GF(2^n).

        Returns:
            A new BitVector containing the product modulo mod in GF(2^n).
        """
        a = self
        a_copy = copy.deepcopy(a)
        b_copy = copy.deepcopy(b)
        product = a_copy.gf_multiply(b_copy)
        _quotient, remainder = product.gf_divide_by_modulus(mod, n)
        return remainder

    def gf_MI(self, mod: BitVector, n: int) -> Self | str:
        """Calculates the multiplicative inverse in Galois Field GF(2^n).

        Args:
            mod: The modulus polynomial BitVector.
            n: The integer degree n of the Galois Field GF(2^n).

        Returns:
            A new BitVector with the multiplicative inverse in GF(2^n), or a
            string indicating that no inverse exists.
        """
        num: BitVector = self
        NUM = copy.deepcopy(num)
        MOD = copy.deepcopy(mod)
        x = self.__class__(size=len(mod))
        x_old = self.__class__(intVal=1, size=len(mod))
        y = self.__class__(intVal=1, size=len(mod))
        y_old = self.__class__(size=len(mod))
        while int(mod):
            quotient, remainder = num.gf_divide_by_modulus(mod, n)
            num, mod = mod, remainder
            x, x_old = x_old ^ quotient.gf_multiply(x), x
            y, y_old = y_old ^ quotient.gf_multiply(y), y
        if int(num) != 1:
            return f"NO MI. However, the GCD of {NUM} and {MOD} is {num}"

        z = x_old ^ MOD
        quotient, remainder = z.gf_divide_by_modulus(MOD, n)
        return remainder

    def runs(self) -> list[str]:
        """Extracts contiguous runs of identical bits ('0's and '1's).

        Returns:
            A list of binary strings, each representing a contiguous run of 0s
            or 1s.
        """
        allruns: list[str] = []
        if self._size == 0:
            return allruns
        run = ""
        previous_bit = self[0]
        if previous_bit == 0:
            run = "0"
        else:
            run = "1"
        for bit in itertools.islice(self, 1, None):
            if bit == 0 and previous_bit == 0:
                run += "0"
            elif bit == 1 and previous_bit == 0:
                allruns.append(run)
                run = "1"
            elif bit == 0 and previous_bit == 1:
                allruns.append(run)
                run = "0"
            else:
                run += "1"
            previous_bit = bit
        allruns.append(run)
        return allruns

    def test_for_primality(self) -> float:
        """Tests the integer value for primality using Miller-Rabin probabilistic test.

        Returns:
            A float probability close to 1.0 for prime numbers, or 0.0 for
            composites.
        """
        p = int(self)
        if p == 1:
            return 0
        probes = [2, 3, 5, 7, 11, 13, 17]
        for a in probes:
            if a == p:
                return 1
        if any(p % a == 0 for a in probes):
            return 0
        k, q = 0, p - 1
        while not q & 1:
            q >>= 1
            k += 1
        for a in probes:
            a_raised_to_q = pow(a, q, p)
            if a_raised_to_q in (1, p - 1):
                continue
            a_raised_to_jq = a_raised_to_q
            primeflag = 0
            for unused_j in range(k - 1):
                a_raised_to_jq = pow(a_raised_to_jq, 2, p)
                if a_raised_to_jq == p - 1:
                    primeflag = 1
                    break
            if not primeflag:
                return 0
        probability_of_prime = 1 - 1.0 / (4 ** len(probes))
        return probability_of_prime

    def gen_random_bits(self, width: int) -> Self:
        """Generates a random odd integer bit vector of specified bit width.

        Ensures the number spans the full width by setting the two most
        significant bits and the least significant bit to 1.

        Args:
            width: The desired integer bit width of the random vector.

        Returns:
            A new BitVector instance containing the generated random bits.
        """
        candidate = secrets.randbits(width)
        candidate |= 1
        candidate |= 1 << width - 1
        candidate |= 2 << width - 3
        return self.__class__(intVal=candidate)

    def min_canonical(self) -> Self:
        """Finds the minimum canonical circular rotation of the bit vector.

        Evaluates all circular shifts and selects the rotation with the minimum
        integer value (maximum leading zeros).

        Returns:
            A new BitVector instance representing the minimum canonical rotation.
        """
        intvals_for_circular_shifts = [int(self << i) for i in range(len(self))]
        return self.__class__(intVal=min(intvals_for_circular_shifts), size=len(self))
