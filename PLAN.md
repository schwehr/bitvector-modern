# PLAN.md: bitvector-modern Modernization Plan

This document is the long-range plan for `bitvector-modern`. It records the
audit of the current codebase (bugs, typos, and improvement opportunities), the
target design for a 1.0 release, the phased roadmap to get there, and the open
decisions that need a human call. The concrete, checkable work items live in
[TASKS.md](TASKS.md). Day-to-day conventions live in [AGENTS.md](AGENTS.md).

Status legend used throughout: **P0** = fix before the next release, **P1** =
required for 1.0, **P2** = nice to have / post-1.0.

______________________________________________________________________

## 1. Vision

`bitvector-modern` should be the obvious pure-Python choice for packed bit
sequences on Python 3.14+:

- **Pythonic first.** A `BitVector` behaves like `bytes`/`bytearray`: it is a
  `collections.abc.Sequence[int]` with real slicing (steps, negative indices,
  clamping), `IndexError` on bad indices, `in` for both bits and sub-vectors,
  `find`/`count`/`index`, `__repr__` that round-trips, and binary operators that
  return `NotImplemented` for foreign types.
- **No legacy baggage.** Nothing from Avi Kak's BitVector 3.5.0 survives for
  compatibility's sake. Names, error messages, return conventions, test
  fixtures, and demo scripts are judged purely on whether they are good modern
  Python. A porting guide documents the mapping for people migrating.
- **Fast where pure Python can be fast.** Word-level (`array('Q')`) operations
  everywhere; no bit-at-a-time Python loops on hot paths; a benchmark suite that
  gates regressions in CI.
- **Boringly well-engineered.** 100% coverage, property-based and mutation
  testing, strict typing under four checkers, reproducible builds, trusted
  publishing, signed attestations, and documentation generated from the code.
- **Backend-agnostic by design.** The public API is specified by a protocol so
  that alternative backends (NumPy, mmap, Rust) can be evaluated later without
  changing user code.

### Non-goals

- Supporting Python < 3.14.
- Byte-for-byte compatibility with BitVector 3.5.0 output or exceptions.
- A general-purpose big-integer or number-theory library. Integer `gcd`, modular
  inverse, and primality are handled by `math` and `pow()`; only the GF(2^n)
  polynomial operations stay because they are genuinely bit-vector work.

______________________________________________________________________

## 2. Current State (baseline, 2026-09-30)

Measured on `main` at `1a8c6a0`:

| Check                                       | Result                                                                                                                   |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `uv run pytest --benchmark-skip`            | 464 passed, 80 skipped, 100% cov                                                                                         |
| `uv run ruff check` (project config)        | clean                                                                                                                    |
| `uv run ruff check --isolated --select ALL` | 1196 findings (181 `ANN001`, 83 `D103`, 76 `D401`, 62 `TRY003`, 49 `EM101`, 28 `SLF001`, 25 `PLR2004`, 14 `ANN401`, ...) |
| `uv run ty check` / `mypy .` / `pyright`    | clean                                                                                                                    |
| `uv run mypy --strict BitVector`            | 2 `no-any-return` errors                                                                                                 |
| CI matrix                                   | Linux only (macOS/Windows commented out)                                                                                 |

Shape of the code:

- `BitVector/BitVector.py` — 2,167 lines, one class, 64-bit `array('Q')`
  storage, bit `i` lives at `vector[i // 64]` bit `(i & 63)` (LSB-first within a
  word), with `_BIT_REV_8` byte-translation used to convert to/from big-endian
  integers and bytes.
- `BitVector/protocol.py` — a `BitVectorProtocol` that `BitVector` does **not**
  actually satisfy (see B17).
- `tests/` — 13 pytest modules, hypothesis properties, pytest-benchmark suite.
- `examples/demo.py` — a 778-line linear port of the 3.5.0 demo script, with
  several sections that no longer do what their comments say.

______________________________________________________________________

## 3. Audit Findings

Line numbers refer to `main` at `1a8c6a0`. Items marked **(confirmed)** were
reproduced with a probe script; the rest were found by reading.

### 3.1 Bugs

| ID  | Pri | Where                                                                                    | Finding                                                                                                                                                                                                                                                                    |
| --- | --- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B1  | P0  | `BitVector.py` L356–448 (`__getitem__`, `_get_slice`, `_resolve_slice_range`)            | **(confirmed)** Slice `step` is silently ignored. `bv[::2]`, `bv[::-1]`, and `bv[1:4:2]` all return the wrong bits with no error.                                                                                                                                          |
| B2  | P0  | `BitVector.py` L1260–1261 (`__setitem__`)                                                | **(confirmed)** `bv[:] = other` is a silent no-op. `tests/test_dunder.py::test_setitem_full_slice` (L420–424) asserts the buggy behaviour. Slice assignment also ignores `step`.                                                                                           |
| B3  | P0  | `BitVector.py` L1533 (`__deepcopy__`, no `__copy__`)                                     | **(confirmed)** `copy.copy(bv)` shares the underlying `array`; mutating the copy mutates the original.                                                                                                                                                                     |
| B4  | P0  | `BitVector.py` L196–208 (`from_bitstring`)                                               | **(confirmed)** Accepts `_`, leading `+`, and whitespace via `int(s, 2)`, producing the wrong width/value (`"1_0"` → `"010"`, `"+1"` → `"01"`).                                                                                                                            |
| B5  | P0  | `BitVector.py` L234 (`from_hex`)                                                         | **(confirmed)** Invalid characters raise `KeyError` instead of `ValueError`.                                                                                                                                                                                               |
| B6  | P0  | `BitVector.py` L248 (`from_string`), L944 (`get_bitvector_in_ascii`)                     | **(confirmed)** No `encoding` parameter. Characters > U+00FF silently produce more than 8 bits; U+0080–U+00FF round-trip to a `UnicodeDecodeError`.                                                                                                                        |
| B7  | P0  | `BitVector.py` L1854–1870 (`rank_of_bit_set_at_index`)                                   | **(confirmed)** Negative `position` is accepted by `self[position]` but the follow-up slice `self[0:position+1]` is wrong → bogus `ValueError`.                                                                                                                            |
| B8  | P0  | `BitVector.py` L827–871 (`permute`, `unpermute`)                                         | **(confirmed)** Negative indices accepted silently; `permute([])` raises `max() iterable argument is empty`; `unpermute` never checks that the list is a bijection (duplicates accepted).                                                                                  |
| B9  | P0  | `BitVector.py` L490–584, L1638 (`__xor__`, `__and__`, `__or__`, `__contains__`, metrics) | **(confirmed)** Foreign operands raise `AttributeError: 'int' object has no attribute '_size'` instead of returning `NotImplemented` (→ `TypeError`).                                                                                                                      |
| B10 | P0  | `BitVector.py` L1304 (`__setitem__`)                                                     | **(confirmed)** `bv[0] = BitVector.from_int(0)` is accepted because `item not in (0, 1)` calls `BitVector.__eq__(0)`.                                                                                                                                                      |
| B11 | P0  | `BitVector.py` L1087–1146 (`shift_left_by_one`, `shift_right_by_one`)                    | **(confirmed)** `shift_right_by_one` leaves a set bit in the unused padding region (breaks the all-padding-bits-are-zero invariant). `shift_left_by_one` on an empty vector raises `IndexError` from `left_most_bits[0]`.                                                  |
| B12 | P1  | `BitVector.py` L2137–2154 (`gen_random_bits`)                                            | **(confirmed)** `width < 3` raises `negative shift count`. Also an instance method that ignores `self`.                                                                                                                                                                    |
| B13 | P1  | `BitVector.py` L2156 (`min_canonical`)                                                   | **(confirmed)** Empty vector raises `min() iterable argument is empty`.                                                                                                                                                                                                    |
| B14 | P1  | `BitVector.py` L86–110 (`__init__`)                                                      | **(confirmed)** `BitVector(size=-1)` reports `wrong arg(s) for constructor` instead of saying size must be non-negative.                                                                                                                                                   |
| B15 | P1  | `BitVector.py` L133–134 (`from_int`)                                                     | **(confirmed)** `from_int(1.5)` silently truncates to `"1"` (legacy `intVal` coercion).                                                                                                                                                                                    |
| B16 | P1  | `BitVector.py` L1769–1774 (`jaccard_similarity`)                                         | **(confirmed)** Zero-vector check runs before the size check, so mismatched sizes report the wrong error.                                                                                                                                                                  |
| B17 | P0  | `protocol.py` L19, `test_protocol.py` L13                                                | **(confirmed)** `BitVectorProtocol` declares `size: int`; `BitVector` has only `_size` and `__slots__`, so it does not satisfy its own protocol. The test hides this with `typing.cast`. Protocol is also not `@runtime_checkable`.                                        |
| B18 | P1  | `BitVector.py` L341, L909, L937–942, L967–972                                            | `get_bitvector_in_ascii`/`get_bitvector_in_hex` byteswap on big-endian hosts but `__int__`, `from_file_path`, and `__add__` do not → inconsistent results on big-endian. Pick one (see D5).                                                                                |
| B19 | P1  | `tests/test_properties.py::test_reverse_involution`                                      | Vacuous: `reverse()` returns a new vector, the test discards it and asserts the untouched original.                                                                                                                                                                        |
| B20 | P1  | `BitVector.py` L2041–2070 (`gf_MI`)                                                      | Returns a `str` on failure (\`Self                                                                                                                                                                                                                                         |
| B21 | P1  | `BitVector.py` L375–376, L382–429                                                        | Out-of-range index raises `ValueError` not `IndexError`; out-of-range slices raise instead of clamping like every other Python sequence (see D2).                                                                                                                          |
| B22 | P1  | `.gitignore`, `examples/`                                                                | `.gitignore` ignores `testinput*.txt` yet `examples/testinput{1,4,5}.txt` are tracked and unused; `demo.py` writes `test.txt` and `testinput5.txt` into the CWD.                                                                                                           |
| B23 | P1  | `.github/workflows/release.yml`, `README.md`                                             | Publishes with a long-lived `PYPI_API_TOKEN` (zizmor `use-trusted-publishing` suppressed). README says to put `1.0.0-rc.1` in `pyproject.toml`; PEP 440 normalizes that to `1.0.0rc1`, so tag, `__version__`, and the PyPI version disagree.                               |
| B24 | P1  | `pyproject.toml`, `BitVector.py` L6                                                      | Version string duplicated.                                                                                                                                                                                                                                                 |
| B25 | P0  | `docs/index.md`, `docs/porting.md`, `examples/README.md`, `README.md`                    | Quick Start uses removed `BitVector(intVal=42, size=8)`; porting guide maps `intValue()` → nonexistent `int_val()`; examples README references a `BitVector.py` that is not in `examples/`; README says running `BitVector.py` executes examples (there is no `__main__`). |
| B26 | P1  | `examples/demo.py` L66–70, L201–254, L409–414, L695–704, L720                            | Sections claim to construct from a file-like object / `testinput1.txt` but print stale variables; `bv3 << 7` statements are no-ops whose comments claim mutation; "UNCOMMENT THE FOLLOWING" precedes live code.                                                            |
| B27 | P2  | `tests/test_benchmarks.py` L370–375, L1–6                                                | `test_bench_len` and `test_bench_length` are identical; module docstring references nonexistent `_not_yet_ready__add__`.                                                                                                                                                   |
| B28 | P1  | `tests/test_constructors.py`                                                             | 108 lines of unused 3.5.0 byte blobs and **zero tests**. The codespell `ignore-words-list` (`astroid,bu,mis,whet,wit`) exists only to tolerate this data.                                                                                                                  |
| B29 | P0  | `AGENTS.md`                                                                              | Wrong about storage (`'H'`/16-bit → actually `'Q'`/64-bit), attributes (`self.size`, `self.more_to_read`), removed methods (`read_bits_from_file*`), CI matrix (Linux only), and roadmap (#7 closed; #10/#13/#16/#64/#69 effectively done). Fixed in this change.          |

### 3.2 Typos and wording

| ID  | Where                                     | Finding                                                                                                                                                                                                             |
| --- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T1  | `examples/demo.py` L401                   | "Unpurmute" → "Unpermute".                                                                                                                                                                                          |
| T2  | `examples/demo.py` L648                   | "multiplicati_inverses" → "multiplicative_inverses".                                                                                                                                                                |
| T3  | `examples/demo.py` L627                   | Says GF(2^3) with x^3 + x + 1 but uses the AES GF(2^8) modulus.                                                                                                                                                     |
| T4  | `examples/demo.py` L54–57                 | Duplicated "Int value ... as computed by int()" block.                                                                                                                                                              |
| T5  | `examples/demo.py` L444                   | "initialized with the intVal method" — legacy name.                                                                                                                                                                 |
| T6  | `BitVector.py` L144                       | Error message refers to `intVal`.                                                                                                                                                                                   |
| T7  | `BitVector.py` L1320                      | Orphaned comment `# Allow int() to work:` sits above `__iter__`.                                                                                                                                                    |
| T8  | `tests/test_properties.py` (slicing test) | Docstring says "16-bit word boundaries"; words are 64-bit.                                                                                                                                                          |
| T9  | `tests/test_constructors.py` L1           | Docstring "intVal, fp, and file" describes removed constructor kwargs.                                                                                                                                              |
| T10 | `tests/test_init.py` L11–20, L157–171     | `test_intVal_zero_hex_helper` (camelCase) and `ZeroHex` exist only to cover the legacy `int(val)` coercion branch.                                                                                                  |
| T11 | `BitVector.py` L1638, `protocol.py`       | `__contains__(self, otherBitVec)` camelCase parameter (why `N803` is suppressed).                                                                                                                                   |
| T12 | `BitVector.py` various                    | Legacy-style messages: "Jaccard called on two zero vectors --- NOT ALLOWED", "NO MI. However, ...", "wrong arg(s) for constructor", "First arg bitvec has no bits", "the arg bit not set", "Bad permutation index". |
| T13 | `BitVector.py` L116–118 (`from_int`)      | Docstring describes the implementation ("bypassing intermediate string formatting and dictionary lookups") rather than behaviour.                                                                                   |
| T14 | `BitVector.py` L367–369 (`__getitem__`)   | `Raises:` lists `ValueError` for out-of-bounds (should become `IndexError`) and omits `TypeError`.                                                                                                                  |
| T15 | `pyproject.toml` `maintainers`            | Lists Avinash Kak; he does not maintain this fork.                                                                                                                                                                  |
| T16 | `mkdocs.yml` `site_url`                   | Points at the repository, not a documentation site.                                                                                                                                                                 |
| T17 | `BitVector.py` L254, L796, L873           | \`BinaryIO                                                                                                                                                                                                          |
| T18 | `README.md`                               | No install command, no usage example, no PyPI/license badges.                                                                                                                                                       |

### 3.3 Legacy 3.5.0 remnants to remove

These are not bugs per se; they exist only because the original library did it
that way. All are slated for removal (no deprecation shims — see D8).

| ID  | Where                                                                  | Remnant                                                                                                                                                                                                         |
| --- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| L1  | `BitVector.py` L716–723, L1548–1551, `test_dunder.py` L76–83, L173–176 | `isinstance(self.vector, array.array)` fallbacks in `__add__`/`__deepcopy__` for a `vector` that could once be a `list`/`tuple` (issue #80), plus the tests that monkeypatch `vector` to a tuple to cover them. |
| L2  | `BitVector.py` L1306–1307, `test_get_set.py` L66                       | `isinstance(pos, tuple)` branch in `__setitem__` and the test that passes `(0,)` as an index.                                                                                                                   |
| L3  | `BitVector.py` L133–134, `test_init.py` `ZeroHex`                      | `if not isinstance(val, int): val = int(val)` in `from_int`.                                                                                                                                                    |
| L4  | `BitVector.py` L20–37, L192, L234                                      | `_hexdict` nibble table and the hex-string → bitlist → per-bit constructor path (`from_bytes`, `from_hex`, `from_string`).                                                                                      |
| L5  | `BitVector.py` L1087–1146                                              | `shift_left_by_one` / `shift_right_by_one` (subsumed by `shift_left(1)` / `shift_right(1)`).                                                                                                                    |
| L6  | `BitVector.py` L1736–1754, L1886–1895                                  | `bit_count_sparse` / `is_power_of_2_sparse` — identical algorithms to the non-sparse versions now that both use `int.bit_count()`.                                                                              |
| L7  | `BitVector.py` L1910–1955, L2101–2135                                  | `gcd`, `multiplicative_inverse`, `test_for_primality` — integer number theory better served by `math.gcd`, `pow(a, -1, m)`, and a dedicated library.                                                            |
| L8  | `BitVector.py` L2137–2154                                              | `gen_random_bits` forcing odd + top two bits (a prime-candidate heuristic, not a bit-vector concern).                                                                                                           |
| L9  | `BitVector.py` L1710–1734                                              | `set_value(...)` re-running `__init__` on an existing instance.                                                                                                                                                 |
| L10 | `BitVector.py` L811–825, L1665–1689                                    | `divide_into_two` (trivial slice pair) and `reset(val)` (→ `fill`/`clear`).                                                                                                                                     |
| L11 | `BitVector.py` L796–809, L873–898, L916–987                            | Names `write_bits_to_stream_object`, `write_to_file`, `get_bitvector_in_ascii`, `get_bitvector_in_hex` (→ `to_bitstring`/`write_to`, `to_bytes`, `decode`, `hex`).                                              |
| L12 | `BitVector.py` L2041                                                   | `gf_MI` naming and string return.                                                                                                                                                                               |
| L13 | `BitVector.py` L1385–1419                                              | `bv == 5` / `bv == 5.0` cross-type equality inherited from 3.5.0 (see D3).                                                                                                                                      |
| L14 | `examples/demo.py`, `examples/testinput*.txt`, `examples/README.md`    | The linear demo script and its fixture files.                                                                                                                                                                   |
| L15 | `tests/test_constructors.py`                                           | Byte blobs from the 3.5.0 test inputs.                                                                                                                                                                          |
| L16 | `pyproject.toml` `[tool.codespell]`                                    | `ignore-words-list` entries that only exist for L15.                                                                                                                                                            |
| L17 | `BitVector/BitVector.py` module path, `N999` suppression               | `BitVector/BitVector.py` with class `BitVector` (three identical names) — see D1.                                                                                                                               |
| L18 | `BitVector.py` L60–62                                                  | Public, mutable `vector` attribute as the storage API.                                                                                                                                                          |

### 3.4 Improvements

| ID  | Pri | Area        | Improvement                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| --- | --- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| I1  | P1  | API         | Model the public API after `bytes`/`bytearray`: register as `collections.abc.Sequence[int]`; full slice semantics (B1/B2/B21); `find`, `rfind`, `index`, `count`, `startswith`, `endswith`; `in` accepts an `int` bit or a sub-vector; `hex()`/`fromhex()`; `to_bytes()`/`from_bytes()` with a `bit_order` argument.                                                                                                                                                                                                                                               |
| I2  | P1  | API         | `__repr__` that round-trips (`BitVector.from_bitstring('10110')`), explicit `__bool__`, `__copy__`, `__reduce__`, `__buffer__` (PEP 688) for zero-copy export to `memoryview`/NumPy, `__bytes__`.                                                                                                                                                                                                                                                                                                                                                                  |
| I3  | P1  | API         | Binary dunders return `NotImplemented` for foreign types (B9). `@overload` `__getitem__` (`int → int`, `slice → Self`) replacing `Any`.                                                                                                                                                                                                                                                                                                                                                                                                                            |
| I4  | P1  | API         | Consistent exceptions: `IndexError` for positions, `ValueError` for values, `TypeError` for types; messages that include the offending value and the vector length.                                                                                                                                                                                                                                                                                                                                                                                                |
| I5  | P1  | API         | `random(n, *, rng=secrets)` classmethod replacing `gen_random_bits`; `fill(bit)`/`clear()` replacing `reset`; GF(2^n) helpers renamed (`gf_multiply`, `gf_divmod`, `gf_multiply_modular`, `gf_inverse`) and raising on failure.                                                                                                                                                                                                                                                                                                                                    |
| I6  | P1  | Typing      | Remove all `Any`: `Sequence[int]` for permutations/bitlists, `collections.abc.Buffer` for byte input, `SupportsRead[bytes]`/`SupportsWrite[bytes]`/`SupportsWrite[str]` for streams, `dict[int, object]` for memo. `mypy --strict`, `pyright strict`, `ty`, `pyrefly` all clean on package **and** tests.                                                                                                                                                                                                                                                          |
| I7  | P1  | Internals   | Single `_WORD_BITS = 64` / `_WORD_MASK` constant set; remove hard-coded `63`, `64`, `0xFFFF…`, `0x8000…`, and the parallel `itemsize * 8` computations. Private `_words` storage. One documented invariant: padding bits are always zero, checked by a hypothesis test after every mutator.                                                                                                                                                                                                                                                                        |
| I8  | P1  | Performance | Replace per-bit Python loops with word-level or C-level operations in: `from_bytes`/`from_hex`/`from_string` (use `translate(_BIT_REV_8)` + `frombytes` like `from_file_path`), `write_to_file`, `__str__` (`format(int(self), f"0{n}b")`), `reverse`, `permute`, slice `__setitem__`, `__contains__` (currently O(n·m) with an allocation per position), `min_canonical` (O(n²) → Booth's algorithm or integer rotation), `gf_multiply` (a deepcopy per set bit), `is_power_of_2`, `__ilshift__`/`__irshift__` (two deepcopies each), `rank_of_bit_set_at_index`. |
| I9  | P1  | Tests       | Shared `conftest.py` with a `bitstrings()` hypothesis strategy; model-based property tests comparing every operation against a reference built on Python `int`/`str`; tests for step slices, copy semantics, repr round-trip, `NotImplemented`; stop reading `_size` and `vector` from tests (use `len` and public API); de-duplicate (empty-rotation error, `__str__`, permute tests appear twice); typed `BenchmarkFixture`; drop `# type: ignore[import-not-found]` for hypothesis.                                                                             |
| I10 | P1  | Tests       | Mutation testing (`mutmut`) with a baseline score and a CI gate (issue #211). Coverage `fail_under = 100`.                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| I11 | P1  | Packaging   | `src/` layout; PEP 639 `license = "PSF-2.0"` + `license-files`; classifiers (`Typing :: Typed`, `Development Status`, `Operating System :: OS Independent`, `Intended Audience :: Developers`); correct `maintainers`; `Documentation`/`Changelog` URLs; single-sourced version (VCS tags via `uv-dynamic-versioning` or `hatch-vcs`; `importlib.metadata` at runtime); evaluate `uv_build` backend.                                                                                                                                                               |
| I12 | P1  | Tooling     | Ruff: `per-file-ignores` for `tests/` instead of global ignores; enable `ANN001`, `ANN401`, `B905`, `D401`, `EM`, `TRY003`, `PLR2004`; `preview = true`; `isort` `required-imports`. Pytest: `--strict-markers --strict-config -ra`, `filterwarnings = ["error"]`, `xfail_strict = true`, hypothesis CI profile. Consolidate pylint to local disables or drop it (issue #142). `validate-pyproject`, `pyproject-fmt`, `actionlint`/`check-jsonschema` for workflows, `uv-lock` hook.                                                                               |
| I13 | P1  | CI/CD       | Re-enable macOS/Windows; add `3.14t` (free-threaded) and `3.15-dev` (`continue-on-error`) jobs; `concurrency` with `cancel-in-progress`; `uv lock --check`; `uv build` + `twine check`/`uv publish --check` on every PR; docs build on PR and deploy to GitHub Pages on `main`; benchmark regression tracking (e.g. CodSpeed or `github-action-benchmark`); `pip-audit`/`uv audit` and OSV scanning (issues #210, #53); Dependabot `uv` ecosystem (the `pip` ecosystem does not update `uv.lock`).                                                                 |
| I14 | P1  | Release     | Trusted Publishing (OIDC, `id-token: write`), `actions/attest-build-provenance` (SLSA), a job that fails if the tag does not match the built version, a CHANGELOG generated by `git-cliff` or `release-please` from Conventional Commits, test on the built wheel (not the source tree) before publishing.                                                                                                                                                                                                                                                         |
| I15 | P1  | Docs        | Fix `docs/index.md`; add `docs/design.md` (bit order, word layout, invariants, complexity table per method); complete and verify `docs/porting.md` against the real 3.5.0 API (issue #123); `CONTRIBUTING.md`; `CHANGELOG.md`; examples as doctested `docs/examples.md` or small `examples/*.py` with `main()` guards, run in CI; README with install/quick-start/badges; `mkdocs` `site_url` → GitHub Pages.                                                                                                                                                      |
| I16 | P2  | Backends    | After the API freeze, evaluate alternative storage behind `BitVectorProtocol`: Python `int` (bulk ops are C-speed; `__setitem__` is O(n)), `bytearray`/`memoryview`, NumPy `uint64` (issue #79), mmap (issues #74/#76), Rust/pyo3 (issue #77). Each must pass the shared conformance test-suite and the benchmark gate.                                                                                                                                                                                                                                            |
| I17 | P2  | Python 3.14 | Use `warnings.deprecated` (PEP 702) only if a shim is ever needed; rely on PEP 649 lazy annotations (no quoted forward refs); `collections.abc.Buffer`; document thread-safety under free-threading (instances are not thread-safe; module has no mutable globals).                                                                                                                                                                                                                                                                                                |
| I18 | P2  | Ecosystem   | Comparison benchmarks and a feature matrix against `bitarray`, `bitstring`, and `numpy.packbits` (issue #37); a `FrozenBitVector` (hashable) variant; optional Textual TUI (issue #21) as a separate package.                                                                                                                                                                                                                                                                                                                                                      |

______________________________________________________________________

## 4. Target Design (1.0)

### 4.1 Package layout

```
src/
  BitVector/                 # importable name: decision D1 (resolved: keep BitVector)
    __init__.py              # re-exports BitVector, BitVectorProtocol, __version__
    _core.py                 # BitVector implementation
    _gf2.py                  # GF(2^n) polynomial helpers (mixin or functions)
    _io.py                   # stream/file helpers
    protocol.py              # BitVectorProtocol (runtime_checkable)
    py.typed
tests/
  conftest.py                # shared fixtures + hypothesis strategies
  conformance/               # backend-agnostic protocol tests
  test_*.py
  benchmarks/
docs/
  index.md, quickstart.md, design.md, api.md, porting.md, development.md,
  changelog.md (symlink to CHANGELOG.md)
examples/                    # small, focused, CI-executed scripts
```

### 4.2 Public API sketch

```python
class BitVector(Sequence[int]):
    # construction
    def __init__(self, *, size: int = 0, bitlist: Sequence[int] | None = None) -> None: ...  # D9 (resolved: keyword-only size=, bitlist=)
    @classmethod
    def zeros(cls, n: int) -> Self: ...
    @classmethod
    def ones(cls, n: int) -> Self: ...
    @classmethod
    def from_int(cls, value: int, *, length: int | None = None) -> Self: ...
    @classmethod
    def from_bitstring(cls, s: str) -> Self: ...          # strict: only "0"/"1"
    @classmethod
    def from_bytes(cls, data: Buffer, *, bit_order: Literal["big", "little"] = "big") -> Self: ...
    @classmethod
    def fromhex(cls, s: str) -> Self: ...
    @classmethod
    def from_text(cls, s: str, *, encoding: str = "utf-8") -> Self: ...
    @classmethod
    def from_stream(cls, stream: SupportsRead[bytes], *, num_bytes: int | None = None) -> Self: ...
    @classmethod
    def from_file(cls, path: StrPath, *, offset: int = 0, num_bytes: int | None = None) -> Self: ...
    @classmethod
    def random(cls, n: int, *, rng: Callable[[int], int] = secrets.randbits) -> Self: ...

    # sequence protocol
    def __len__(self) -> int: ...
    @overload
    def __getitem__(self, i: int) -> int: ...
    @overload
    def __getitem__(self, s: slice) -> Self: ...
    def __setitem__(self, key: int | slice, value: int | Iterable[int]) -> None: ...
    def __iter__(self) -> Iterator[int]: ...
    def __reversed__(self) -> Iterator[int]: ...
    def __contains__(self, item: object) -> bool: ...     # int bit or BitVector sub-sequence
    def find(self, sub: BitVector, start: int = 0, end: int | None = None) -> int: ...
    def index(...)/count(...)/startswith(...)/endswith(...)

    # conversion
    def __int__(self) -> int: ...
    def __index__(self) -> int: ...                       # D10 (resolved: implemented)
    def __str__(self) -> str: ...                         # "10110"
    def __repr__(self) -> str: ...                        # BitVector('10110')
    def __format__(self, spec: str) -> str: ...
    def __bytes__(self) -> bytes: ...
    def to_bytes(self, *, bit_order=..., pad: Literal["right", "left", "error"] = "error") -> bytes: ...
    def hex(self) -> str: ...
    def decode(self, encoding: str = "utf-8") -> str: ...
    def write_to(self, stream: SupportsWrite[bytes]) -> None: ...
    def __buffer__(self, flags: int) -> memoryview: ...   # read-only view of words

    # bitwise (requires equal lengths; raises ValueError on mismatch — decision D11)
    __and__/__or__/__xor__/__invert__ and in-place variants; return NotImplemented
    __lshift__/__rshift__ = logical shift (new object); rotate_left/rotate_right = circular  # D12 (resolved: logical shift)
    __add__/__iadd__ = concatenation

    # mutation
    def fill(self, bit: int) -> None: ...
    def clear(self) -> None: ...
    def pad_left(self, n: int) -> None: ... / pad_right
    def reverse(self) -> Self: ...                        # returns new vector  # D13 (resolved: new vector)

    # analysis
    def bit_count(self) -> int: ...
    def next_set_bit(self, start: int = 0) -> int: ...
    def rank(self, i: int) -> int: ...
    def runs(self) -> list[tuple[int, int]]: ...          # (bit, length), not strings
    def hamming_distance(self, other) -> int: ...
    def jaccard_similarity(self, other) -> float: ... / jaccard_distance
    def is_power_of_2(self) -> bool: ...
    def min_rotation(self) -> Self: ...                   # Booth's algorithm
    def permute(self, perm: Sequence[int]) -> Self: ... / unpermute

    # GF(2^n)
    def gf_multiply(self, other) -> Self: ...
    def gf_divmod(self, modulus, n: int) -> tuple[Self, Self]: ...
    def gf_multiply_modular(self, other, modulus, n: int) -> Self: ...
    def gf_inverse(self, modulus, n: int) -> Self: ...    # raises ZeroDivisionError
```

### 4.3 Invariants (to be enforced by tests)

1. `len(bv) == bv._size` and `len(bv._words) == ceil(len(bv) / 64)` — never
   over-allocated after a public operation.
1. All bits at positions `>= len(bv)` in the last word are zero after every
   public operation (including in-place ones).
1. `BitVector.from_bitstring(str(bv)) == bv` and `eval(repr(bv)) == bv`.
1. `int(bv) == int(str(bv) or "0", 2)` and
   `BitVector.from_int(int(bv), length=len(bv)) == bv`.
1. For every operation, the result equals the reference implementation on Python
   `str`/`int` (model-based property tests).

______________________________________________________________________

## 5. Roadmap

Each phase ends with a tagged release so users can stop at any point. Breaking
changes are allowed in 0.x and are called out in the CHANGELOG.

| Phase | Theme                                       | Release | Exit criteria                                                                                                                                                                                              |
| ----- | ------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | Planning (this change)                      | —       | `PLAN.md`, `TASKS.md`, corrected `AGENTS.md` merged. Decisions D1–D13 answered and recorded.                                                                                                               |
| 1     | Correctness: fix P0 bugs on the current API | 0.1.0   | All P0 bugs in §3.1 fixed with regression tests; `copy.copy` safe; invariant test added; docs that lie are fixed; dead test data removed.                                                                  |
| 2     | Shed legacy: remove §3.3 remnants           | 0.2.0   | No code path exists only for 3.5.0 compatibility; `demo.py`/fixture files gone; `porting.md` complete and verified; codespell ignore list empty.                                                           |
| 3     | Pythonic API (per §4.2)                     | 0.3.0   | `Sequence[int]` semantics; `NotImplemented`; `IndexError`; step slices; `__repr__`; `__buffer__`; renamed methods; strict typing clean on tests too; model-based property tests cover every public method. |
| 4     | Packaging, tooling, CI/CD, release pipeline | 0.4.0   | `src/` layout; PEP 639 metadata; single-sourced version; trusted publishing + attestations; full OS matrix + `3.14t`; docs on GitHub Pages; mutation-testing gate; audit scanning; Dependabot on `uv`.     |
| 5     | Performance                                 | 0.5.0   | Every method in I8 is word-level or C-level; benchmark CI tracks regressions; complexity table published in `docs/design.md`.                                                                              |
| 6     | API freeze and 1.0                          | 1.0.0   | Two consecutive minor releases without breaking changes; conformance suite passes; `BitVectorProtocol` is the documented extension point.                                                                  |
| 7     | Post-1.0 exploration                        | 1.x     | Backend experiments (I16) behind the protocol; ecosystem comparisons (I18); `FrozenBitVector`.                                                                                                             |

Phases 1 and 2 may proceed in parallel on separate branches; Phase 3 depends on
both. Phase 4 items that are independent of the API (CI matrix, trusted
publishing, Dependabot) can be done at any time.

______________________________________________________________________

## 6. Recorded Decisions

All decisions D1–D13 have been recorded below.

| ID  | Decision                                                                                                               | Options                                                                                                                                                                                                              | Recommendation                                                                                                                            | Resolution                                                                                                                                                                        |
| --- | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | Import name. `BitVector/BitVector.py` triples the name and violates PEP 8 module naming (`N999` is suppressed for it). | (a) keep `BitVector`; (b) `bitvector_modern` (matches the distribution); (c) `bitvector` (short, may collide with the original on PyPI/import).                                                                      | **(b)** `src/bitvector_modern/` with `from bitvector_modern import BitVector`. Do it in Phase 3 together with the other breaking changes. | **(a) Keep `BitVector`** (`BitVector/` or `src/BitVector/`).                                                                                                                      |
| D2  | Sequence semantics for bad indices/slices.                                                                             | (a) keep raising `ValueError`; (b) `IndexError` for indices and clamping for slices like every Python sequence.                                                                                                      | **(b)**.                                                                                                                                  | **(b) Standard sequence semantics**: `IndexError` for invalid indices and clamping for slices.                                                                                    |
| D3  | Cross-type equality (`bv == 5`, `bv == 5.0`).                                                                          | (a) keep; (b) drop — `==` only between `BitVector`s; ordering between `BitVector`s stays by integer value.                                                                                                           | **(b)**. A sequence equal to a number is surprising and breaks `Sequence` expectations; users can write `int(bv) == 5`.                   | **(b) Drop cross-type equality**: `==` only between `BitVector` instances (`int(bv) == 5` for numeric comparisons); ordering between `BitVector`s stays by integer value.         |
| D4  | Integer number theory (`gcd`, `multiplicative_inverse`, `test_for_primality`, `gen_random_bits`).                      | (a) keep; (b) remove, document `math.gcd(int(a), int(b))`, `pow(int(a), -1, int(m))`, and a primality library in the porting guide; keep GF(2^n).                                                                    | **(b)**.                                                                                                                                  | **(b) Remove integer number theory**: remove `gcd`, `multiplicative_inverse`, `test_for_primality`, `gen_random_bits` (document alternatives in `docs/porting.md`); keep GF(2^n). |
| D5  | Big-endian hosts.                                                                                                      | (a) support consistently everywhere (byteswap paths + a big-endian CI job via QEMU); (b) drop the two byteswap branches and document little-endian word layout as an implementation detail hidden behind `to_bytes`. | **(b)**; the layout is internal once `vector` is private.                                                                                 | **(b) Internal little-endian layout**: drop byteswap branches and document little-endian word layout as an internal implementation detail hidden behind `to_bytes`.               |
| D6  | Storage backend.                                                                                                       | (a) keep `array('Q')` LSB-first; (b) `array('Q')` MSB-first (cheaper int/bytes conversion, costlier indexing); (c) Python `int`; (d) `bytearray`.                                                                    | Keep **(a)** through 1.0; evaluate (b)–(d) in Phase 7 behind the protocol with the benchmark suite as the judge.                          | **(a) Keep `array('Q')` LSB-first** through 1.0; evaluate alternative backends in Phase 7 behind `BitVectorProtocol`.                                                             |
| D7  | Keep `docs/porting.md`?                                                                                                | (a) delete with the rest of the legacy; (b) keep as the one place the 3.5.0 names are allowed to appear.                                                                                                             | **(b)** — it serves migrating users and costs nothing in code.                                                                            | **(b) Keep `docs/porting.md`** as the designated reference mapping 3.5.0 legacy names to modern equivalents.                                                                      |
| D8  | Deprecation shims for renamed methods.                                                                                 | (a) `warnings.deprecated` aliases for one minor release; (b) hard rename, CHANGELOG + porting guide only.                                                                                                            | **(b)** while 0.x; adopt (a) only after 1.0.                                                                                              | **(b) Hard rename in 0.x**: document in CHANGELOG and porting guide; adopt deprecation shims only after 1.0.                                                                      |
| D9  | Constructor shape.                                                                                                     | (a) keep keyword-only `size=`/`bitlist=`; (b) `BitVector(iterable_of_bits)` + `BitVector.zeros(n)` like `bytes(n)`/`bytes(iterable)`; (c) `BitVector(n)` zeros like `bytes(n)` and `BitVector([...])`.               | **(c)** — mirrors `bytes`/`bytearray` exactly and makes `BitVector()` the empty vector.                                                   | **(a) Keep keyword-only `size=` and `bitlist=`**: retain keyword-only `BitVector(size=..., bitlist=...)`.                                                                         |
| D10 | Provide `__index__`?                                                                                                   | (a) yes (`hex(bv)`, `range(bv)`, `bytes(bv)` work — but `bytes(bv)` would then mean a zero-filled buffer of length `int(bv)`); (b) only `__int__` + `__bytes__`.                                                     | **(b)**. The `bytes(bv)` ambiguity is a trap.                                                                                             | **(a) Implement `__index__`**: provide `__index__` to allow `hex(bv)`, `range(bv)`, `bin(bv)`, bitwise indexing directly.                                                         |
| D11 | Mixed-length bitwise operators.                                                                                        | (a) keep auto left-padding the shorter operand; (b) require equal lengths and raise `ValueError`.                                                                                                                    | **(a)** — it matches integer semantics and existing tests rely on it; document it prominently.                                            | **(b) Require equal lengths**: operands of `&`, `\|`, `^` must have matching lengths; raise `ValueError` on mismatch.                                                             |
| D12 | Meaning of `<<` / `>>`.                                                                                                | (a) keep as circular rotation (3.5.0); (b) logical shift like `int`, with `rotate_left/right` methods for rotation.                                                                                                  | **(b)** — every other Python type treats `<<` as a shift; rotation-by-operator surprises readers.                                         | **(b) Logical shift**: `<<` and `>>` perform logical bit shift (returning new instances); add dedicated `rotate_left` and `rotate_right` methods for circular rotation.           |
| D13 | `reverse()` semantics.                                                                                                 | (a) keep returning a new vector; (b) in-place like `list.reverse`, plus `reversed(bv)`/a copy helper.                                                                                                                | **(b)** for consistency with `list`/`bytearray`.                                                                                          | **(a) Return new vector**: keep `reverse()` returning a new `BitVector` instance.                                                                                                 |

______________________________________________________________________

## 7. Versioning and Release Policy

- Semantic Versioning. While `0.x`, minor bumps may break; patch bumps never do.
- Every merge to `main` must leave `uv run pytest`, pre-commit, and all type
  checkers green. Releases are cut by tagging `vX.Y.Z` (PEP 440 pre-releases are
  spelled `vX.Y.ZrcN`, not `-rc.N`).
- The CHANGELOG is generated from Conventional Commits; a commit that changes
  behaviour must have a `feat`/`fix`/`perf` type and a `!`/`BREAKING CHANGE:`
  footer when applicable.
- Supported Python: the two most recent minor versions once 3.15 ships;
  free-threaded builds are tested but not yet "supported".

______________________________________________________________________

## 8. Related GitHub Issues

| Issue           | Covered by                                                                |
| --------------- | ------------------------------------------------------------------------- |
| #8              | I6                                                                        |
| #10             | Done (`secrets`); I5 `random`                                             |
| #11             | T-series; I15                                                             |
| #13             | Done; I15                                                                 |
| #16             | Done; I14                                                                 |
| #21             | I18                                                                       |
| #22             | I13                                                                       |
| #23             | B5, L4                                                                    |
| #30             | Done; I9/I10                                                              |
| #37             | I18                                                                       |
| #53             | I13                                                                       |
| #64             | Done                                                                      |
| #69             | Done                                                                      |
| #74/#76/#77/#79 | I16                                                                       |
| #80             | L1                                                                        |
| #84             | I8                                                                        |
| #89             | I1–I3                                                                     |
| #90/#91         | I2 (`__buffer__`), I16                                                    |
| #92             | I8 (evaluate caching `__int__`; probably not worth the invalidation cost) |
| #93             | §4.1 `_io.py`                                                             |
| #94             | D9                                                                        |
| #123            | D7, I15                                                                   |
| #142            | I12                                                                       |
| #210            | I13                                                                       |
| #211            | I10                                                                       |
| #249            | I12 (`B905` / `strict=True`)                                              |
