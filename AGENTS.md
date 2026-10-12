# AGENTS.md: AI Assistant & Developer Guidelines for bitvector-modern

This document provides guidelines, conventions, and architectural context for AI
assistants and developers contributing to `bitvector-modern`.

Companion documents:

- [PLAN.md](PLAN.md) — the long-range modernization plan: audit findings, target
  1.0 design, phased roadmap, and open decisions (`D1`–`D13`).
- [TASKS.md](TASKS.md) — the checkable work items derived from the plan.

**When you finish a task, tick it in `TASKS.md` in the same PR. When you make a
design choice that answers an open decision, record it in `PLAN.md` §6.**

## 1. Project Overview & Architecture

`bitvector-modern` is a modern, pure-Python package for memory-efficient packed
representation of bit arrays and bit vectors.

- **Origin**: A git fork of Avi Kak's `BitVector 3.5.0` (Purdue University).
  Origin is history, not a constraint: **no code, test, fixture, name, or error
  message is kept for 3.5.0 compatibility.** The only place 3.5.0 names may
  appear is `docs/porting.md`, which maps them to the modern API.
- **Core Design**: Bits are packed into a standard library `array.array('Q')`
  (unsigned 64-bit words). Bit `i` is stored at word `i // 64`, bit position
  `i & 63` (LSB-first within a word). A 256-entry byte-reversal table
  (`_BIT_REV_8`) converts between this layout and big-endian integers/bytes at C
  speed via `bytes.translate`.
- **Python Target**: Requires Python `>=3.14`. Uses `Self`, PEP 604 unions, PEP
  649 lazy annotations (no quoted forward references needed), `collections.abc`
  generics, `__slots__`, and f-strings throughout.

### Core invariants

Every public operation, including in-place ones, must leave an instance in this
state. Tests in `tests/` are expected to assert them (see `TASKS.md` P1-17).

1. `len(bv) == bv._size`.
1. `len(bv.vector) == (len(bv) + 63) // 64` — storage is never over-allocated.
1. All bits at positions `>= len(bv)` in the final word are zero. Call
   `_mask_unused_bits()` after any word-level write that may dirty them.
1. `BitVector.from_bitstring(str(bv)) == bv` and
   `BitVector.from_int(int(bv), size=len(bv)) == bv`.

## 2. Repository & File Layout

- **`BitVector/`**: Core package directory (slated to move to
  `src/bitvector_modern/` — see `PLAN.md` D1).
  - **`BitVector.py`**: The `BitVector` class.
  - **`protocol.py`**: `BitVectorProtocol`, the structural type that alternative
    backends must satisfy.
  - **`__init__.py`**: Re-exports `BitVector`, `BitVectorProtocol`,
    `__version__`.
  - **`py.typed`**: PEP 561 marker.
- **`tests/`**: `pytest` suites.
  - **`test_*.py`**: Unit/functional tests grouped by concern (constructors,
    dunders, get/set, boolean logic, comparisons, shifts, permutations, strings,
    streams, operations, protocol).
  - **`test_properties.py`**: Hypothesis property tests; also the HypoFuzz
    target.
  - **`test_benchmarks.py`**: `pytest-benchmark` suite (skipped by default in CI
    test runs; run alone in the benchmark job).
- **`examples/`**: `demo.py` (a legacy linear script scheduled for replacement —
  `TASKS.md` P2-11) and `README.md`.
- **`docs/`** + **`mkdocs.yml`**: MkDocs Material site (`index.md`, `api.md` via
  mkdocstrings, `development.md`, `porting.md`, `modernize.md`).
- **`scripts/fuzz.sh`**: Runs HypoFuzz against the property tests.
- **`.github/`**: `workflows/test.yml` (lint + tests + coverage summary + `ty`,
  plus a separate benchmark job), `workflows/release.yml` (tag-triggered build,
  PyPI publish, GitHub Release), `workflows/lychee.yml` (link check),
  `workflows/zizmor.yml` (Actions security), `dependabot.yml`, `CODEOWNERS`,
  `PULL_REQUEST_TEMPLATE.md`.
- **`pyproject.toml`**: Metadata (hatchling build), `uv` dependency groups, and
  tool config for `ruff`, `pytest`, `coverage`, `codespell`, `pyrefly`,
  `pyright`, `pylint`.
- **`uv.lock`**, **`.python-version`**, **`.pre-commit-config.yaml`**,
  **`.editorconfig`**, **`.lycheeignore`**.
- **`AGENTS.md`**, **`PLAN.md`**, **`TASKS.md`**, **`README.md`**,
  **`CODE_OF_CONDUCT.md`**, **`SECURITY.md`**, **`LICENSE`** (PSF-2.0).

## 3. BitVector API Summary (current)

This describes the code as it is today. The target 1.0 API is in `PLAN.md` §4.2;
where they differ, the plan wins for new work.

### Storage & representation

- `vector: array.array[int]` — packed 64-bit words (public today; becoming
  private, `PLAN.md` L18).
- `_size: int` — number of valid bits. There is **no** public `size` attribute;
  use `len(bv)`.
- `__iter__` / `__reversed__` yield bits as `int` (0/1) from word data.

### Construction

- `BitVector(*, size=None, bitlist=None)` — keyword-only; exactly one of the
  two.
- Factories: `from_int(val, size=None)`, `from_bytes(rawbytes)`,
  `from_bitstring(s)`, `from_bitlist(seq)`, `from_hex(s)`, `from_string(s)`,
  `from_stream(stream, *, num_bytes=None)`,
  `from_file_path(path, *, offset_bytes=0, num_bytes=None)`.

### Access & mutation

- `__getitem__` (int → bit, slice → new `BitVector`; **step is currently ignored
  — bug B1**), `__setitem__` (int ← 0/1, slice ← `BitVector` of equal length;
  **`bv[:] = x` is currently a no-op — bug B2**), `set_value(...)`,
  `reset(0|1)`, `pad_from_left(n)`, `pad_from_right(n)`.

### Operators

- Bitwise `& | ^ ~` and `&= |= ^=` — shorter operand is zero-padded on the left.
- `+` / `+=` — concatenation.
- `<<` / `>>` and `<<=` / `>>=` — **circular rotation** (not shifts; see
  `PLAN.md` D12). `shift_left(n)` / `shift_right(n)` are in-place logical
  shifts.
- `== != < <= > >=` — `==`/`!=` compare `BitVector`s by size and bits, and also
  compare equal to `int`/`float` by integer value (see D3); ordering is by
  integer value and raises `TypeError` for other types.
- `in` — sub-vector containment (raises `ValueError` on an empty or too-short
  container).

### Conversion & I/O

- `int(bv)`, `str(bv)` (bitstring), `format(bv, spec)` (string spec, falling
  back to integer spec), `get_bitvector_in_hex()`, `get_bitvector_in_ascii()`,
  `write_to_file(binary_stream)` (length must be a multiple of 8),
  `write_bits_to_stream_object(text_stream)`.

### Analysis

- `bit_count()`, `bit_count_sparse()`, `next_set_bit(from_index=0)`,
  `rank_of_bit_set_at_index(i)`, `is_power_of_2()`, `is_power_of_2_sparse()`,
  `runs()`, `hamming_distance(other)`, `jaccard_similarity(other)`,
  `jaccard_distance(other)`, `min_canonical()`, `reverse()`, `permute(list)`,
  `unpermute(list)`, `divide_into_two()`.

### GF(2^n) and number theory

- `gf_multiply(b)`, `gf_divide_by_modulus(mod, n)`,
  `gf_multiply_modular(b, mod, n)`, `gf_MI(mod, n)` (returns a `str` on failure
  — B20).
- `gcd(other)`, `multiplicative_inverse(mod)`, `test_for_primality()`,
  `gen_random_bits(width)` — slated for removal (`PLAN.md` D4).

### Copying

- `copy.deepcopy(bv)` and `bv[:]` are safe. **`copy.copy(bv)` currently aliases
  the storage — bug B3.** Do not rely on it until P1-5 lands.

## 4. Development Environment & Tooling

Use `uv` for everything. The full local gate is the same as CI:

```bash
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
uv run pre-commit run --all-files      # ruff, pyupgrade, ty, mypy, pyrefly,
                                       # pyright, pylint, mdformat, codespell,
                                       # zizmor, bandit, semgrep, ...
uv run pytest --benchmark-skip         # tests + coverage (fail-under 95%)
uv run pytest --benchmark-only --no-cov
```

Individual tools, when iterating:

```bash
uv run ruff check --fix && uv run ruff format
uv run ty check
uv run mypy .
uv run pyrefly check
uv run pyright
uv run pylint BitVector tests
uv run codespell
uv run mdformat --wrap 80 .
uv run semgrep scan --config p/default
uv run mkdocs serve
uv run hypothesis fuzz tests/test_properties.py   # or scripts/fuzz.sh
```

Before proposing a tool-configuration change, check `PLAN.md` I12/I13 and
`TASKS.md` Phase 4 so the change lands in the intended shape (e.g. prefer
`per-file-ignores` over new global ruff ignores).

## 5. Testing Conventions & Standards

- **Modern pytest only.** Plain `assert`, `pytest.raises(..., match=...)`,
  `@pytest.mark.parametrize`, fixtures (`tmp_path`, `monkeypatch`). Never
  `unittest.TestCase` or `self.assert*`.
- **Regression test first.** Every bug fix adds a failing test before the fix.
- **Test through the public API.** Do not read `_size` or `vector` in new tests;
  use `len()`, `str()`, `int()`, iteration, and equality. Existing
  private-attribute tests are being migrated (`TASKS.md` P2-13).
- **Properties over examples** for anything with an obvious reference model
  (slicing vs `str` slicing, shifts vs `int` shifts, etc.). Put strategies in
  `tests/conftest.py` once it exists (P3-16).
- **Invariants.** New mutators must be exercised by the invariant test (P1-17).
- **Coverage**: 100% for new code; the CI threshold is 95% and is scheduled to
  rise to 100% (P4-8).
- **Benchmarks**: Any change to a hot path adds or updates a benchmark in
  `tests/test_benchmarks.py`; do not add duplicate benchmarks.
- **CI reality**: `test.yml` currently runs **Linux only** (macOS/Windows are
  commented out pending P4-12). Do not claim cross-platform coverage in docs
  until it is back.

## 6. Code & Docstring Style

- **Docstrings**: Google style with `Args:`, `Returns:`, `Raises:`, `Yields:`,
  `Attributes:` as applicable. Describe behaviour and contracts, not the
  implementation ("uses a lookup table to avoid string formatting" belongs in a
  comment, if anywhere).
- **Strings**: f-strings only. No `%`, no `.format()`, no `"a" + str(b)`.
- **Typing**: Precise annotations everywhere, including tests. No `Any` — use
  `Sequence[int]`, `collections.abc.Buffer`, `SupportsRead[bytes]`,
  `SupportsWrite[str]`, `Self`, `Literal`, `@overload`. Use `X | None`, never
  `Optional`/`Union`.
- **Exceptions**: `IndexError` for positions, `ValueError` for values,
  `TypeError` for types. Messages name the offending value and the constraint:
  `f"index {pos} out of range for BitVector of length {n}"`. Binary dunders
  return `NotImplemented` for foreign operands.
- **Constants**: Use named module constants for word geometry (`_WORD_BITS`,
  `_WORD_MASK` — being introduced, I7) instead of literal `64`/`63`/`0xFFFF…`.
- **Performance**: No bit-at-a-time Python loops on hot paths. Prefer word-level
  `array` operations, `int` arithmetic, `bytes.translate`, `int.bit_count`, and
  `int.from_bytes`/`to_bytes`.
- **Naming**: `snake_case` for everything; no camelCase parameters (`other`, not
  `otherBitVec`). The remaining `N8xx` ruff ignores are temporary.

## 7. Version Control & Commit Messages

- **Feature branches only.** `git checkout -b <type>/<short-name>`; never commit
  directly to `main`.
- **Code review before commit.** Review the diff for correctness and style,
  propose 1–3 improvements, and check whether `AGENTS.md`, `PLAN.md`, or
  `TASKS.md` need updating.
- **Conventional Commits.** `<type>(<scope>): <subject>` — `feat`, `fix`,
  `perf`, `refactor`, `test`, `docs`, `build`, `ci`, `chore`, `style`. Use `!`
  or a `BREAKING CHANGE:` footer for behaviour breaks (allowed while `0.x`;
  always documented in the CHANGELOG once it exists).
- **No `TAG=` / `CONV=` lines** in commit messages, ever.
- **Legacy policy.** A PR may not add a compatibility shim, alias, or
  special-case for BitVector 3.5.0 behaviour. If a legacy behaviour is
  discovered, remove it (or file it under `PLAN.md` §3.3) rather than preserving
  it.

## 8. Roadmap Pointer

The roadmap lives in `PLAN.md` §5 (phases 0–7) and `TASKS.md`. Summary:

| Phase | Theme                                 | Release |
| ----- | ------------------------------------- | ------- |
| 1     | Fix P0 bugs on the current API        | 0.1.0   |
| 2     | Remove all 3.5.0 remnants             | 0.2.0   |
| 3     | Pythonic `Sequence[int]` API, renames | 0.3.0   |
| 4     | Packaging, tooling, CI/CD, releases   | 0.4.0   |
| 5     | Word-level performance everywhere     | 0.5.0   |
| 6     | API freeze                            | 1.0.0   |
| 7     | Backends, ecosystem, frozen variant   | 1.x     |

GitHub issues are mapped to plan items in `PLAN.md` §8. Issues #7, #10, #13,
#16, #30, #64, and #69 are complete or superseded.
