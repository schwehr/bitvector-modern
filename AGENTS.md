# AGENTS.md: AI Assistant & Developer Guidelines for bitvector-modern

This document provides guidelines, conventions, and architectural context for AI
assistants and developers contributing to `bitvector-modern`.

## 1. Project Overview & Architecture

`bitvector-modern` is a modern, pure-Python package for memory-efficient packed
representation of bit arrays and bit vectors.

- **Origin**: An unofficial git fork and modernization of Avi Kak's original
  `BitVector 3.5.0` (Purdue University).
- **Core Design**: Uses standard library `array` (`'H'` / unsigned short integer
  arrays) for compact bitwise storage, manipulation, and boolean logic
  operations.
- **Python Target**: Requires Python `>=3.13`. Employs modern Python features
  including type annotations (`Self`, `Sequence`), advanced f-strings, and clean
  modular structures.

## 2. Repository & File Layout

The project repository is structured as a modern Python package:

- **`BitVector/`**: Core package directory.
  - **`BitVector.py`**: Primary module implementing `BitVector`.
  - **`__init__.py`**: Package initialization and top-level symbols export.
- **`tests/`**: Automated test suites executed via `pytest`.
  - **`test_*.py`**: Unit and functional tests covering constructors, boolean
    logic, slicing, string output, and mathematical operations.
  - **`test_benchmarks.py`**: Performance regression benchmarks executed via
    `pytest-benchmark`.
- **`examples/`**: Reference usage scripts.
  - **`demo.py`**: Working demo script illustrating package features.
- **`.github/`**: CI/CD automation and templates, including GitHub Actions
  workflows (`test.yml`, `lychee.yml`), `CODEOWNERS`, and
  `PULL_REQUEST_TEMPLATE.md`.
- **`pyproject.toml`**: Modern project configuration defining package metadata,
  build system (`hatchling`), dependency groups (`uv`), and tool settings
  (`ruff`, `pytest`, `ty`, `codespell`, `mdformat`, `coverage`).
- **`uv.lock`**: Exact locked dependency resolution file managed by `uv`.
- **`.pre-commit-config.yaml`**: Configuration for pre-commit git hooks.
- **`AGENTS.md`**: AI assistant and developer guidelines (this document).
- **`README.md` & `LICENSE`**: Project documentation and PSF-2.0 license file.

## 3. BitVector Structure & API Summary

The core functionality of `bitvector-modern` is implemented in
`BitVector/BitVector.py`. Below is an overview of its data structures and API:

### Internal Storage & Representation

- **`BitVector` Class**: The primary class representing packed bit vectors.
  - **Memory Array (`self.vector`)**: Store bits in an `array.array('H')`
    (unsigned short integers, 16 bits per element) for memory compactness.
  - **Size (`self.size`)**: Tracks the exact integer number of valid bits.
  - **Iteration (`__iter__`, `__reversed__`)**: Supports sequentially yielding
    individual bits forward and in reverse via generator expressions.

### Constructors & Data Input (`__init__`)

- Supports flexible keyword arguments: `size`, `intVal`, `bitstring`, `bitlist`,
  `textstring`, `rawbytes`, `filename`, and `fp`.
- **Factory Methods**: Can be initialized from a string (`from_string`) or a hex
  string (`from_hex`).
- **File & Streaming Input**: Can read incrementally from files or file objects
  (`read_bits_from_file`, `read_bits_from_fileobject`), tracking remaining data
  via `self.more_to_read`.

### Core Operations & Methods

- **Bit Access & Mutators**: Indexing and slicing via `__getitem__` and
  `__setitem__`, bit assignment via `set_value`, and `reset()`.
- **Boolean Logic (Dunders)**: Bitwise AND (`&` / `__and__`), OR (`|` /
  `__or__`), XOR (`^` / `__xor__`), and NOT (`~` / `__invert__`).
- **Concatenation & Splitting**: Vector addition (`+` / `__add__`, `+=` /
  `__iadd__`), `divide_into_two()`, and padding (`pad_from_left`,
  `pad_from_right`).
- **Shifts & Rotations**: Logical shifts (`<<` / `shift_left`, `>>` /
  `shift_right`) and circular rotations (`circular_rot_left`,
  `circular_rot_right`, `circular_rotate_left_by_one`).
- **Permutations**: Reordering bits via `permute()`, `unpermute()`, and
  `reverse()`.
- **Comparisons & Equality**: Full rich comparison support (`==`, `!=`, `<`,
  `<=`, `>`, `>=`) supporting `BitVector`, `int`, and `float` operands, and
  canonical ordering (`min_canonical`). `==` and `!=` also allow comparison with
  other types (evaluating to `False` and `True` respectively).
- **Conversions & Output**: Integer conversion (`int()`), string output
  (`get_bitvector_in_ascii()`, `get_bitvector_in_hex()`, `__str__`), and stream
  writing (`write_to_file`, `write_bits_to_stream_object`).
- **Analysis & Metrics**: Bit counting (`count_bits`, `count_bits_sparse`),
  distance/similarity (`hamming_distance`, `jaccard_similarity`,
  `jaccard_distance`), `runs()`, `next_set_bit()`, `rank_of_bit_set_at_index()`,
  and power-of-two checks (`is_power_of_2`).
- **Galois Field & Number Theory**: Modular arithmetic and polynomial operations
  over GF(2^n) (`gf_multiply`, `gf_divide_by_modulus`, `gf_multiply_modular`,
  `gf_MI`), greatest common divisor (`gcd`), multiplicative inverse
  (`multiplicative_inverse`), and primality testing (`test_for_primality`).
- **Utilities**: Random bit vector generation (`gen_random_bits`) and deep
  copying (`__deepcopy__`).

## 4. Development Environment & Tooling

We use modern Python tooling for dependency management, building, linting, and
static analysis:

- **Dependency Management (`uv`)**: Use `uv` for all virtual environments and
  package installations.
  ```bash
  uv sync
  ```
- **Linting & Formatting (`ruff`, `pylint`)**: Enforces code style, import
  sorting, formatting, and code quality checks.
  ```bash
  uv run ruff check --fix
  uv run ruff format
  uv run pylint BitVector tests
  ```
- **Static Type Checking (`ty`, `mypy`, `pyrefly`, & `pyright`)**: Enforces
  strict type annotations across all modules.
  ```bash
  uv run ty check
  uv run mypy .
  uv run pyrefly check
  uv run pyright
  ```
- **Markdown Formatting (`mdformat`)**: Enforces 80-column line wrapping and
  standard GFM formatting across Markdown files.
  ```bash
  uv run mdformat --wrap 80 .
  ```
- **Spelling (`codespell`)**: Checks for typos and misspelled identifiers.
  ```bash
  uv run codespell
  ```
- **Static Analysis & Security Scanning (`semgrep`)**: Enforces static analysis
  and security rules.
  ```bash
  uv run semgrep scan --config p/default
  ```
- **Pre-commit Hooks**: Enforces standards prior to commits. Must be installed
  when setting up a workspace:
  ```bash
  uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
  uv run pre-commit run --all-files
  ```

## 5. Testing Conventions & Standards

All testing is orchestrated via `pytest`, `pytest-cov`, and `pytest-benchmark`.

- **Running Tests**:
  ```bash
  uv run pytest
  ```
- **Continuous Fuzz Testing (`hypofuzz`)**: To continuously run adaptive,
  coverage-guided property-based fuzzing on our hypothesis test suite
  (`tests/test_properties.py`):
  ```bash
  uv run hypothesis fuzz tests/test_properties.py
  ```
- **Cross-Platform CI**: Automated matrix testing in GitHub Actions executes
  across Linux (`ubuntu-latest`), macOS (`macos-latest`), and Windows
  (`windows-latest`) for Python 3.14, while Python 3.13 testing is scoped to
  Linux. Benchmarks and type checks are also scoped to Linux.
- **Best Pytest Form**:
  - **CRITICAL RULE**: Write all new and refactored tests in the **best modern
    `pytest` form** using standard Python `assert` statements (e.g.,
    `assert bv.size == 8`).
  - **Do NOT use legacy `unittest` style** assertions (`self.assertEqual`,
    `self.assertTrue`, `self.assertRaises`, etc.) or inherit from
    `unittest.TestCase`.
  - Use `pytest.raises(...)` for expected exceptions.
  - Use `@pytest.mark.parametrize` to cleanly test multiple input combinations
    without repetitive boilerplate.
  - Use standard pytest fixtures (like `tmp_path` for temporary files) instead
    of manual cleanup or `tempfile`.
- **Coverage & Performance**: Maintain 100% test coverage for new features and
  bug fixes (enforced with a 95% minimum threshold via `--fail-under=95`).
  Ensure benchmark suites (`test_benchmarks.py`) remain functional and
  non-regressing. Continuous integration automatically formats and outputs
  read-only Markdown coverage reports to GitHub Actions job summaries.

## 6. Code & Docstring Style

- **Docstrings**:
  - **CRITICAL RULE**: All module, class, method, and function docstrings must
    strictly follow **Standard Google Python Docstring Style**.
  - Include clearly formatted `Args:`, `Returns:`, `Raises:`, `Yields:`, and
    `Attributes:` sections as applicable.
  - Avoid unstructured, verbose, or legacy docstring formatting.
- **String Formatting**:
  - Always use modern Python **f-strings** (`f"Value: {val}"`) for string
    concatenation and formatting. Never use legacy `%` formatting or
    `.format()`.
- **Type Annotations**:
  - Provide precise, tight type annotations for all function signatures and
    return types.
  - Avoid generic `Any` types; prefer specific types such as `Sequence[int]`,
    `Buffer`, `Self`, `Literal`, or explicit `Union`/`Optional` types.

## 7. Version Control & Commit Messages

- **Feature Branches**:
  - **CRITICAL RULE**: All code changes and refactoring work MUST be performed
    on dedicated git feature branches (e.g., `git checkout -b <branch-name>`).
  - Never make direct commits on the `main` branch.
- **Code Review**:
  - Always do a code review before committing. In addition to finding and
    suggesting fixes to issues, try to create 1-3 suggestions for improvement to
    the code based on the current changes.
  - See if there needs to be any changes to `AGENTS.md` based on the current
    changes and propose improvements.
- **Conventional Commits**:
  - All git commit messages MUST adhere to the **Conventional Commits**
    specification (`<type>(<optional scope>): <subject>`).
  - Examples:
    - `feat(dunder): enable modern __add__ and __iadd__ support`
    - `refactor(tests): switch test_init.py from unittest to pytest`
    - `chore(license): replace __copyright__ variable with SPDX header`
    - `docs: import legacy manuals into docs/ directory`
- **NO Tag or Conversation ID Entries**:
  - **CRITICAL RULE**: Commit messages must **NEVER** contain `TAG=` or `CONV=`
    lines or entries. These are reserved for internal Piper/CL tools and must be
    omitted from all git commits in this repository.

## 8. Engineering Roadmap & Open Issues

When picking up work or assisting with refactoring, align with the active
project goals tracked in our
[GitHub Issues](https://github.com/schwehr/bitvector-modern/issues):

- **Issue #16 (Release Automation)**: Set up CI/CD workflows (GitHub Actions)
  for automating package publishing and release management.
- **Issue #13 (Documentation Migration)**: Create a dedicated `docs/` directory
  and import/format prior documentation and user manuals.
- **Issue #11 (f-strings)**: Convert remaining legacy string formatting across
  `BitVector.py` to modern f-strings.
- **Issue #10 (Modern Random Number Generator)**: Replace default
  `import random` usage with cryptographically secure or modern RNG practices
  (`secrets` / modern generators).
- **Issue #8 (Tighten Type Annotations)**: Replace ambiguous `Any` annotations
  with strict, precise type definitions.
- **Issue #7 (Pytest Migration)**: Systematically convert remaining
  `unittest.TestCase` test suites in `tests/` to idiomatic `pytest` functions
  and assertions.
