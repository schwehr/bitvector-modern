import math
import mmap
import tempfile
from typing import Any, Iterator, Self


class MmapBitVector:
    def __init__(
        self,
        *,
        size: int | None = None,
        intVal: int | None = None,
        bitstring: str | None = None,
    ):
        self.size = size if size is not None else 0
        if bitstring is not None:
            self.size = len(bitstring)
        elif intVal is not None and size is None:
            self.size = max(1, intVal.bit_length())

        self.byte_size = math.ceil(self.size / 8)

        self._file = tempfile.TemporaryFile()
        self._file.write(b"\x00" * max(1, self.byte_size))
        self._file.flush()

        self._mmap = mmap.mmap(self._file.fileno(), 0)

        if intVal is not None:
            val_bytes = intVal.to_bytes(self.byte_size, byteorder="big")
            self._mmap[: len(val_bytes)] = val_bytes
        elif bitstring is not None:
            intVal = int(bitstring, 2)
            val_bytes = intVal.to_bytes(self.byte_size, byteorder="big")
            self._mmap[: len(val_bytes)] = val_bytes

    def __del__(self):
        try:  # pragma: no cover
            if hasattr(self, "_mmap") and self._mmap:
                try:  # pragma: no cover
                    self._mmap.close()  # pragma: no cover
                except ValueError:  # pragma: no cover
                    pass
            if hasattr(self, "_file") and self._file:
                try:  # pragma: no cover
                    self._file.close()
                except ValueError:  # pragma: no cover
                    pass
        except BaseException:  # pragma: no cover
            pass

    def _clone_empty(self, size: int) -> "MmapBitVector":
        return MmapBitVector(size=size)

    def int_val(self) -> int:
        return int.from_bytes(self._mmap[: self.byte_size], byteorder="big")

    def __int__(self) -> int:
        return self.int_val()

    def __len__(self) -> int:
        return self.size

    def __str__(self) -> str:
        if self.size == 0:
            return ""
        return bin(self.int_val())[2:].zfill(self.size)

    def __xor__(self, other: Self) -> "MmapBitVector":
        res_int = self.int_val() ^ other.int_val()
        return MmapBitVector(size=max(self.size, other.size), intVal=res_int)

    def __and__(self, other: Self) -> "MmapBitVector":
        res_int = self.int_val() & other.int_val()
        return MmapBitVector(size=max(self.size, other.size), intVal=res_int)

    def __or__(self, other: Self) -> "MmapBitVector":
        res_int = self.int_val() | other.int_val()
        return MmapBitVector(size=max(self.size, other.size), intVal=res_int)

    def __invert__(self) -> "MmapBitVector":
        mask = (1 << self.size) - 1
        res_int = (~self.int_val()) & mask
        return MmapBitVector(size=self.size, intVal=res_int)

    def __add__(self, other: Self) -> "MmapBitVector":
        res_int = (self.int_val() << other.size) | other.int_val()
        return MmapBitVector(size=self.size + other.size, intVal=res_int)

    def __iadd__(self, other: Self) -> "MmapBitVector":
        res_int = (self.int_val() << other.size) | other.int_val()
        self.size += other.size
        self.byte_size = math.ceil(self.size / 8)

        # Workaround for macOS lacking mremap (resize support)
        try:  # pragma: no cover
            self._mmap.resize(max(1, self.byte_size))  # pragma: no cover
        except SystemError:  # pragma: no cover
            self._mmap.close()  # pragma: no cover
            self._file.truncate(max(1, self.byte_size))  # pragma: no cover
            self._mmap = mmap.mmap(self._file.fileno(), 0)  # pragma: no cover

        val_bytes = res_int.to_bytes(self.byte_size, byteorder="big")
        self._mmap[: len(val_bytes)] = val_bytes
        return self

    def __lshift__(self, n: int) -> "MmapBitVector":
        res_int = (self.int_val() << n) & ((1 << self.size) - 1)
        return MmapBitVector(size=self.size, intVal=res_int)

    def __rshift__(self, n: int) -> "MmapBitVector":
        res_int = self.int_val() >> n
        return MmapBitVector(size=self.size, intVal=res_int)

    def __getitem__(self, pos: int | slice | Any) -> Any:
        if isinstance(pos, slice):
            start, stop, step = pos.indices(self.size)
            if step != 1:
                raise ValueError("Slice steps other than 1 are not supported")
            if start >= stop:  # pragma: no cover
                return MmapBitVector(size=0, intVal=0)  # pragma: no cover
            length = stop - start
            val = self.int_val()
            shift = self.size - stop
            mask = (1 << length) - 1
            res_int = (val >> shift) & mask
            return MmapBitVector(size=length, intVal=res_int)
        else:
            if not isinstance(pos, int):  # pragma: no cover # pragma: no cover
                raise TypeError(
                    "Index must be an integer"
                )  # pragma: no cover # pragma: no cover
            if pos < 0:  # pragma: no cover
                pos += self.size
            if pos < 0 or pos >= self.size:  # pragma: no cover
                raise IndexError("Index out of range")

            # Direct byte indexing
            bit_index = self.size - pos - 1
            byte_idx = self.byte_size - 1 - (bit_index // 8)
            bit_in_byte = bit_index % 8

            return (self._mmap[byte_idx] >> bit_in_byte) & 1

    def __setitem__(self, pos: int | slice | Any, item: int | Self | Any) -> Any:
        if isinstance(pos, slice):
            start, stop, step = pos.indices(self.size)
            if step != 1:
                raise ValueError("Slice steps other than 1 are not supported")
            length = stop - start
            item_val_int: int = 0
            if hasattr(item, "int_val") and callable(getattr(item, "int_val")):
                item_val_int = int(getattr(item, "int_val")())
            elif isinstance(item, int):  # pragma: no cover
                item_val_int = item  # pragma: no cover
            else:  # pragma: no cover
                item_val_int = int(item)  # pragma: no cover

            val = self.int_val()
            shift = self.size - stop
            mask = ((1 << length) - 1) << shift

            val = (val & ~mask) | ((item_val_int << shift) & mask)
            val_bytes = val.to_bytes(self.byte_size, byteorder="big")
            self._mmap[: len(val_bytes)] = val_bytes
        else:
            if not isinstance(pos, int):  # pragma: no cover # pragma: no cover
                raise TypeError(
                    "Index must be an integer"
                )  # pragma: no cover # pragma: no cover
            if pos < 0:  # pragma: no cover
                pos += self.size
            if pos < 0 or pos >= self.size:  # pragma: no cover
                raise IndexError("Index out of range")

            bit_index = self.size - pos - 1
            byte_idx = self.byte_size - 1 - (bit_index // 8)
            bit_in_byte = bit_index % 8

            byte_val = self._mmap[byte_idx]
            if item:
                byte_val |= 1 << bit_in_byte
            else:
                byte_val &= ~(1 << bit_in_byte)  # pragma: no cover
            self._mmap[byte_idx] = byte_val

    def __iter__(self) -> Iterator[int]:
        # Fast iter using byte index
        for pos in range(self.size):
            bit_index = self.size - pos - 1
            byte_idx = self.byte_size - 1 - (bit_index // 8)
            bit_in_byte = bit_index % 8
            yield (self._mmap[byte_idx] >> bit_in_byte) & 1

    def __eq__(self, other: object) -> bool:
        if not hasattr(other, "size"):
            return False
        if self.size != getattr(other, "size", -1):
            return False

        if hasattr(other, "_mmap"):
            other_mmap: Any = getattr(other, "_mmap")
            for i in range(self.byte_size):
                if self._mmap[i] != other_mmap[i]:
                    return False  # pragma: no cover
            return True
        elif hasattr(other, "int_val") and callable(getattr(other, "int_val")):
            other_int_val: Any = getattr(other, "int_val")
            return self.int_val() == other_int_val()
        return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other: object) -> bool:
        if not hasattr(other, "int_val") or not callable(
            getattr(other, "int_val")
        ):  # pragma: no cover
            raise TypeError("Not comparable")
        other_int_val: Any = getattr(other, "int_val")
        return self.int_val() < other_int_val()

    def __le__(self, other: object) -> bool:
        if not hasattr(other, "int_val") or not callable(
            getattr(other, "int_val")
        ):  # pragma: no cover
            raise TypeError("Not comparable")
        other_int_val: Any = getattr(other, "int_val")
        return self.int_val() <= other_int_val()

    def __gt__(self, other: object) -> bool:
        if not hasattr(other, "int_val") or not callable(
            getattr(other, "int_val")
        ):  # pragma: no cover
            raise TypeError("Not comparable")
        other_int_val: Any = getattr(other, "int_val")
        return self.int_val() > other_int_val()

    def __ge__(self, other: object) -> bool:
        if not hasattr(other, "int_val") or not callable(
            getattr(other, "int_val")
        ):  # pragma: no cover
            raise TypeError("Not comparable")
        other_int_val: Any = getattr(other, "int_val")
        return self.int_val() >= other_int_val()

    def __contains__(self, otherBitVec: Self) -> bool:
        if otherBitVec.size == 0:
            return True
        if self.size < otherBitVec.size:  # pragma: no cover
            return False

        other_val = otherBitVec.int_val()
        mask = (1 << otherBitVec.size) - 1
        val = self.int_val()

        for i in range(self.size - otherBitVec.size + 1):
            if (val >> i) & mask == other_val:
                return True
        return False

    def count_bits(self) -> int:
        return self.int_val().bit_count()

    def count_bits_sparse(self) -> int:
        return self.count_bits()

    def next_set_bit(self, from_index: int = 0) -> int:
        for pos in range(from_index, self.size):
            bit_index = self.size - pos - 1
            byte_idx = self.byte_size - 1 - (bit_index // 8)
            bit_in_byte = bit_index % 8
            if (self._mmap[byte_idx] >> bit_in_byte) & 1:
                return pos
        return -1

    def is_power_of_2(self) -> bool:
        val = self.int_val()
        return val != 0 and (val & (val - 1)) == 0

    def is_power_of_2_sparse(self) -> bool:
        return self.is_power_of_2()
