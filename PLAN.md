# Design Options for `BitVector.from_file`

This document details 6 distinct API and architectural designs for adding a
`from_file` (or file-reading factory) class method to `BitVector`. Each design
addresses reading raw bytes from a file or stream and returning a `BitVector`
instance. A comparative analysis of strengths and weaknesses is provided
alongside a feature matrix and a comprehensive architectural recommendation for
`bitvector-modern`.

______________________________________________________________________

## 1. Context & Architectural Goals

The `BitVector` class currently supports various factory class methods such as
`from_bytes`, `from_int`, `from_bitstring`, `from_bitlist`, `from_hex`, and
`from_string`. However, reading binary data directly from a file currently
requires users to manually open the file, read `bytes`, and call
`BitVector.from_bytes()`.

### Key Design Considerations

1. **Resource Lifecycle**: Does the method open and automatically close the
   file, or rely on the caller?
1. **Input Type Ergonomics**: Should the method accept `str`, `os.PathLike`,
   and/or `BinaryIO` / `io.BufferedIOBase` streams?
1. **Partial Reading & Offsets**: Should the user be able to specify byte
   offsets or read limits?
1. **Bit Precision**: Should limits be specified in bytes, bits, or both?
1. **Memory Efficiency**: Does the method read the whole file into RAM at once,
   use OS-level virtual memory paging (memory mapping), or support chunked
   streaming?
1. **Type Safety & Strictness**: How well does the signature integrate with
   modern Python type checkers (`mypy`, `pyright`, `pyrefly`, `ty`) without
   ambiguous `Union` types?

______________________________________________________________________

## 2. Six Proposed Designs

### Design 1: Unified Polymorphic Reader (`str | PathLike | BinaryIO`)

#### Concept

A single, highly versatile `from_file` class method accepting either a file path
(string or `PathLike`) or an open binary file-like stream object (`BinaryIO`).

#### Proposed Signature

```python
@classmethod
def from_file(
    cls,
    file_or_path: str | os.PathLike[str] | BinaryIO,
    *,
    offset: int = 0,
    size: int | None = None,
) -> Self:
    """Creates a BitVector by reading bytes from a file path or binary stream.

    Args:
        file_or_path: Path to a file or an open binary stream supporting read().
        offset: Byte offset from which to start reading (default: 0).
        size: Number of bytes to read, or None to read until EOF.

    Returns:
        A new BitVector instance populated with bits from the file.

    Raises:
        TypeError: If file_or_path is neither a path-like object nor a binary stream.
        ValueError: If offset or size is negative.
    """
```

#### Implementation Behavior

- If `file_or_path` is a string or `os.PathLike`, it is opened in `"rb"` mode
  using a `with` block (ensuring automatic closure), seeked to `offset`, read up
  to `size` bytes, and converted via `cls.from_bytes(...)`.
- If `file_or_path` is a binary stream (satisfying
  `hasattr(file_or_path, "read")`), it seeks to `offset` if supported/requested,
  reads up to `size` bytes, and leaves the stream open for the caller.

______________________________________________________________________

### Design 2: Dual Specialized Factories (`from_file_path` & `from_stream`)

#### Concept

Strict separation of concerns into two explicit class methods: one for
path-based file access and one for open binary stream objects.

#### Proposed Signature

```python
@classmethod
def from_file_path(
    cls,
    path: str | os.PathLike[str],
    *,
    offset_bytes: int = 0,
    num_bytes: int | None = None,
) -> Self:
    """Reads bytes from a file on disk at the specified path."""

@classmethod
def from_stream(
    cls,
    stream: BinaryIO,
    *,
    num_bytes: int | None = None,
) -> Self:
    """Reads bytes from an open binary stream object."""
```

#### Implementation Behavior

- `from_file_path` strictly manages file opening (`open(path, "rb")`) and
  closing.
- `from_stream` strictly operates on an open stream object, performing no file
  open/close or seek side effects.

______________________________________________________________________

### Design 3: Path-Only Context-Managed Factory (`from_file`)

#### Concept

A minimal, opinionated `from_file` class method that *only* accepts filesystem
paths (`str` or `os.PathLike`), delegating stream operations to `from_bytes`.

#### Proposed Signature

```python
@classmethod
def from_file(
    cls,
    path: str | os.PathLike[str],
    *,
    offset: int = 0,
    count: int | None = None,
) -> Self:
    """Creates a BitVector from a binary file at the given filesystem path.

    Args:
        path: File system path (str or Path).
        offset: Byte offset to seek before reading.
        count: Maximum number of bytes to read (None for entire file).

    Returns:
        A BitVector instance containing the read byte sequence.
    """
```

#### Implementation Behavior

- Exclusively handles file opening and resource cleanup.
- Users with `io.BytesIO` or active file handles pass `stream.read()` into
  `BitVector.from_bytes()`.

______________________________________________________________________

### Design 4: Chunked Streaming Generator (`read_file_chunks`)

#### Concept

An iterator/generator method designed for processing large binary files in
fixed-size `BitVector` blocks without loading entire files into memory.

#### Proposed Signature

```python
@classmethod
def read_file_chunks(
    cls,
    file_or_path: str | os.PathLike[str] | BinaryIO,
    chunk_size_bytes: int = 65536,
) -> Iterator[Self]:
    """Yields consecutive BitVector instances of up to chunk_size_bytes.

    Args:
        file_or_path: File path or open binary stream.
        chunk_size_bytes: Number of bytes per BitVector chunk (default: 64 KiB).

    Yields:
        BitVector chunks sequentially until EOF.
    """
```

#### Implementation Behavior

- Opens file if path is given (closing it automatically when iteration
  terminates or is closed).
- Continuously reads `chunk_size_bytes` until EOF, yielding
  `cls.from_bytes(chunk)` on each step.

______________________________________________________________________

### Design 5: Precision Bit-Windowing Reader (`from_file`)

#### Concept

An advanced factory method supporting sub-byte bit offsets, bit-length bounds
(`num_bits`), and bit endianness options.

#### Proposed Signature

```python
@classmethod
def from_file(
    cls,
    file_or_path: str | os.PathLike[str] | BinaryIO,
    *,
    byte_offset: int = 0,
    num_bytes: int | None = None,
    num_bits: int | None = None,
    endianness: Literal["big", "little"] = "big",
) -> Self:
    """Reads a precise bit vector from a file with byte/bit framing and endianness control.

    Args:
        file_or_path: Path or binary stream.
        byte_offset: Offset in bytes before reading starts.
        num_bytes: Capped bytes to read.
        num_bits: Exact bit length of output BitVector (truncating trailing bits if needed).
        endianness: Bit layout convention ("big" or "little").

    Returns:
        A BitVector trimmed to the exact bit length requested.
    """
```

#### Implementation Behavior

- Reads byte data, converts to `BitVector`, trims the vector if `num_bits` is
  specified (e.g. `bv[:num_bits]`), and adjusts bit ordering based on
  `endianness`.

______________________________________________________________________

### Design 6: Memory-Mapped Zero-Copy Reader (`from_mmap`)

#### Concept

A specialized high-performance factory method that uses Python's `mmap` module
to map an on-disk binary file directly into the process address space. Instead
of reading all file bytes into a temporary Python `bytes` object on the heap, it
leverages OS-level virtual memory paging and Python's buffer protocol for
zero-copy bit array initialization.

#### Proposed Signature

```python
@classmethod
def from_mmap(
    cls,
    path: str | os.PathLike[str],
    *,
    offset: int = 0,
    length: int = 0,
    access: int = mmap.ACCESS_READ,
) -> Self:
    """Creates a BitVector from a memory-mapped file using OS virtual memory paging.

    Args:
        path: File system path to open and memory-map.
        offset: Byte offset inside the file (must be non-negative; page-aligned on some OSes).
        length: Number of bytes to map (0 maps the entire file from offset to EOF).
        access: Memory protection mode (default: mmap.ACCESS_READ).

    Returns:
        A new BitVector instance initialized from the memory-mapped buffer.

    Raises:
        FileNotFoundError: If path does not exist.
        ValueError: If mapping an empty (0-byte) file or invalid offset/length.
    """
```

#### Implementation Behavior

- Opens the file in binary read mode and creates an `mmap.mmap` object.
- Passes the memory-mapped buffer directly into `array.array("H")` (or
  word-level unpacking logic) via the Python buffer protocol without allocating
  an intermediate `bytes` copy.
- Can either close the `mmap` after copying into the internal word array, or
  optionally retain a reference if backed by an immutable memory view.

______________________________________________________________________

## 3. Comprehensive Strengths & Weaknesses Comparison

### Design 1: Unified Polymorphic Reader (`file_or_path`)

- **Strengths**:
  - Maximum developer convenience: single method handles file paths,
    `pathlib.Path`, `io.BytesIO`, and standard file handles.
  - Familiar pattern matching standard library APIs (e.g., `numpy.fromfile`,
    `pandas.read_*`).
  - Supports basic byte offsets and sizing.
- **Weaknesses**:
  - Dynamic type checking required
    (`isinstance(file_or_path, (str, os.PathLike))`).
  - Ambiguity regarding stream closure: path inputs are closed automatically,
    whereas open streams must remain open.
  - Parameter name `size` can be ambiguous (bytes vs bits).
  - Union types complicate static type inference in strict mode.

### Design 2: Dual Specialized Factories (`from_file_path` & `from_stream`)

- **Strengths**:
  - Explicit and unambiguous API contracts.
  - Clear resource lifecycle: `from_file_path` guarantees opening/closing;
    `from_stream` leaves stream handling to the caller.
  - Precise type hints without union ambiguity (`PathLike` vs `BinaryIO`).
  - Highly aligned with strict static type checking (`mypy`, `pyright`,
    `pyrefly`).
- **Weaknesses**:
  - Two methods instead of one increases API surface area.
  - Users must choose the right method based on their data type.

### Design 3: Path-Only Context-Managed Factory (`from_file`)

- **Strengths**:
  - Clean, narrow implementation focused purely on filesystem interactions.
  - Guaranteed resource cleanup inside `with open(...)` block.
  - Avoids duplication with `from_bytes` (streams can use
    `from_bytes(stream.read())`).
- **Weaknesses**:
  - Inconvenient for users with `io.BytesIO` or network/pipe streams who might
    expect `from_file` to accept streams.
  - Requires callers to fallback to manual stream reading.

### Design 4: Chunked Streaming Generator (`read_file_chunks`)

- **Strengths**:
  - Crucial for processing large files (multi-gigabyte logs, disk images)
    without high memory overhead.
  - Efficient pipeline integration for stream processing.
- **Weaknesses**:
  - Returns an `Iterator[BitVector]` rather than a `BitVector` instance,
    breaking the standard `@classmethod -> Self` constructor contract.
  - Does not solve single-instance file loading directly; requires caller loop
    or concatenation.

### Design 5: Precision Bit-Windowing Reader (`from_file`)

- **Strengths**:
  - Supports domain-specific requirements like protocol header parsing and
    bitstream extraction.
  - Enables sub-byte bit resolution (`num_bits`).
- **Weaknesses**:
  - High signature complexity and steep learning curve.
  - Increased maintenance and validation overhead (e.g. handling conflicts
    between `num_bytes` and `num_bits`).
  - Potential performance overhead due to post-read bit slicing and masking.

### Design 6: Memory-Mapped Zero-Copy Reader (`from_mmap`)

- **Strengths**:
  - **Peak Memory Efficiency & Speed**: Bypasses intermediate heap allocations
    (`bytes`) by reading directly from OS virtual pages into `array.array("H")`.
  - **Ideal for Massive Disk Files**: Allows instant opening and slicing of very
    large binary files (such as genomic data or disk images) without RAM
    exhaustion.
  - **Buffer Protocol Native**: Integrates cleanly with Python >= 3.13 buffer
    protocol and zero-copy slicing.
- **Weaknesses**:
  - **Platform-Specific Edge Cases**: `mmap` behavior has subtle differences
    between Linux/macOS and Windows (e.g., page-alignment constraints on
    `offset`, file locking).
  - **No Stream/Pipe Support**: Requires a real filesystem path or file
    descriptor; cannot be used with `io.BytesIO`, sockets, or pipes.
  - **Zero-Length File Handling**: `mmap` raises a ValueError on empty (0-byte)
    files, requiring special-case fallback logic.

______________________________________________________________________

## 4. Feature & Tradeoff Comparison Matrix

| Feature / Criteria     | Design 1 (Unified)   | Design 2 (Dual)      | Design 3 (Path-Only) | Design 4 (Chunked) | Design 5 (Windowed)  | Design 6 (`from_mmap`) |
| :--------------------- | :------------------- | :------------------- | :------------------- | :----------------- | :------------------- | :--------------------- |
| **API Ergonomics**     | High                 | High                 | Moderate             | Moderate           | Moderate             | Moderate (Paths only)  |
| **Resource Safety**    | Moderate (Branching) | High (Explicit)      | High (Explicit)      | High (Managed)     | Moderate (Branching) | High (Explicit close)  |
| **Type Precision**     | Moderate (`Union`)   | High (Separate)      | High (`PathLike`)    | Moderate (`Union`) | Moderate (`Union`)   | High (`PathLike`)      |
| **Memory Efficiency**  | Moderate (Full file) | Moderate (Full file) | Moderate (Full file) | High (Chunked)     | Moderate (Full file) | Very High (Zero-copy)  |
| **Sub-byte Precision** | No                   | No                   | No                   | No                 | Yes (`num_bits`)     | No                     |
| **Stream Support**     | Yes                  | Yes (`from_stream`)  | No                   | Yes                | Yes                  | No (Requires fd/path)  |
| **Code Complexity**    | Low-Moderate         | Low                  | Low                  | Moderate           | High                 | Moderate               |

______________________________________________________________________

## 5. Re-evaluated Architectural Recommendation for `bitvector-modern`

### Overall Evaluation of All 6 Designs

When evaluating all 6 designs against `bitvector-modern`'s core
principles—**strict type safety**, **memory efficiency**, **clean Python >=3.13
idioms**, and **unambiguous resource management**—no single design is a silver
bullet for every use case:

- **Design 1 (Unified)** prioritizes caller convenience but introduces ambiguous
  `Union` types (`str | PathLike | BinaryIO`) that blur ownership of file
  handles and complicate static type checking (`pyright`, `mypy`).
- **Design 3 (Path-Only)** is clean but overly restrictive, leaving users with
  open file handles or `io.BytesIO` streams without a dedicated constructor.
- **Design 4 (Chunked)** and **Design 5 (Windowed)** serve specialized needs
  (streaming iterators and sub-byte protocol parsing, respectively) but are too
  specialized or complex to serve as the default general-purpose file reader.
- **Design 6 (`from_mmap`)** offers peak performance and zero-copy memory
  efficiency for large files on disk, but cannot operate on arbitrary streams,
  pipes, or in-memory buffers.

### Final Recommendation: Layered Architecture (Design 2 + Design 6)

We recommend adopting a **Layered Architecture** combining **Design 2 (Dual
Specialized Factories)** as the primary general-purpose API, supplemented by
**Design 6 (`from_mmap`)** for high-performance zero-copy disk I/O:

1. **Primary Standard Constructors (Design 2)**:

   - Implement
     `@classmethod def from_file_path(cls, path: str | os.PathLike[str], *, offset_bytes: int = 0, num_bytes: int | None = None) -> Self:`.
     - Automatically manages `with open(path, "rb") as f:` and guarantees clean
       resource disposal.
   - Implement
     `@classmethod def from_stream(cls, stream: BinaryIO, *, num_bytes: int | None = None) -> Self:`.
     - Operates strictly on open streams without side effects on stream
       lifecycle.
   - **Why this wins over Design 1**: It eliminates union-type ambiguity,
     provides crystal-clear static type signatures, and avoids confusing "who
     closes the handle?" runtime branches.

1. **High-Performance Companion Constructor (Design 6)**:

   - Implement
     `@classmethod def from_mmap(cls, path: str | os.PathLike[str], *, offset: int = 0, length: int = 0) -> Self:`.
   - Dedicated specifically to large binary files on disk where loading the
     entire file into a heap `bytes` object would cause high memory pressure.
   - Uses `mmap.mmap` and Python's buffer protocol to populate the internal
     `array.array("H")` with minimal memory footprint, directly aligning with
     `bitvector-modern`'s core mission of memory efficiency.

1. **Sub-Byte & Streaming Requirements**:

   - For sub-byte bit precision (Design 5), users should call
     `from_file_path(...)` and apply standard slicing (`bv[:num_bits]`).
   - For chunked streaming (Design 4), a separate utility function or iterator
     can be proposed in a future PR without overloading the core
     `Self`-returning class constructors.

______________________________________________________________________
