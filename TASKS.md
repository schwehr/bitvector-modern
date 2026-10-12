# TASKS.md: bitvector-modern Work Items

Checkable tasks derived from [PLAN.md](PLAN.md). IDs in brackets refer to the
audit findings (`B` bug, `T` typo, `L` legacy remnant, `I` improvement) and
decisions (`D`) in that document.

Conventions:

- One task ≈ one PR on a feature branch with a Conventional Commit title.
- Tick the box in the same PR that completes the task; add a line to the
  CHANGELOG when behaviour changes.
- Tasks marked **⚠ decision** must not start until the referenced `D` item in
  `PLAN.md` §6 has an answer.
- Every bug fix lands with a regression test first (red → green).

______________________________________________________________________

## Phase 0 — Planning

- [x] P0-1 Write `PLAN.md` with audit, target design, roadmap, decisions.
- [x] P0-2 Write `TASKS.md` (this file).
- [x] P0-3 Correct `AGENTS.md` (storage type, attributes, layout, CI reality,
  roadmap) and point it at `PLAN.md`/`TASKS.md`. [B29]
- [x] P0-4 Get answers for decisions D1–D13 and record them in `PLAN.md` §6.
- [ ] P0-5 File/triage GitHub issues so each open task below has one; close
  issues that are already done (#7, #10, #13, #16, #30, #64, #69).

______________________________________________________________________

## Phase 1 — Correctness (release 0.1.0)

Fix P0 bugs on the *current* API so a safe release exists before any renames.

### Slicing and indexing

- [x] P1-1 `__getitem__`: honour `slice.step` (including negative) or raise
  `ValueError("step is not supported")` as an interim measure; add tests for
  `[::2]`, `[::-1]`, `[1:4:2]`, `[::64]`, `[::-64]`. [B1]
- [x] P1-2 `__setitem__`: make `bv[:] = other` replace all bits; honour or
  reject `step`; fix `test_setitem_full_slice` which asserts the bug. [B2]
- [x] P1-3 `__setitem__`: reject non-`int` values for index assignment before
  the `in (0, 1)` check (`bool` stays allowed). [B10]
- [x] P1-4 `rank_of_bit_set_at_index`: normalise negative positions once, then
  count words directly instead of slicing. [B7]

### Copy semantics

- [ ] P1-5 Add `__copy__` that duplicates the storage; add tests that
  `copy.copy`, `copy.deepcopy`, `bv[:]`, and `pickle` round-trips never alias
  the array. [B3]

### Constructors and conversions

- [ ] P1-6 `from_bitstring`: validate `set(s) <= {"0", "1"}`; test `_`, `+`,
  `-`, whitespace, and non-ASCII digits. [B4]
- [ ] P1-7 `from_hex`: raise `ValueError` (not `KeyError`) for bad characters;
  accept odd-length input explicitly or document rejection. [B5]
- [ ] P1-8 `from_string`/`get_bitvector_in_ascii`: add `encoding="utf-8"` to
  both; make the round-trip a hypothesis property over `st.text()`. [B6]
- [ ] P1-9 `from_int`: reject non-`int` (`isinstance(val, int)`; `bool` ok);
  delete the `ZeroHex` test. [B15, L3, T10]
- [ ] P1-10 `__init__`: `size < 0` must raise
  `ValueError("size must be non-negative, got -1")`. [B14]

### Operators and errors

- [ ] P1-11 `__and__`/`__or__`/`__xor__`/`__contains__`/metrics: return
  `NotImplemented` (or raise `TypeError`) for non-`BitVector` operands; test
  with `int`, `str`, `bytes`, `None`. [B9]
- [ ] P1-12 `permute`/`unpermute`: reject negative indices, empty lists with a
  clear message, and non-bijective lists in `unpermute`. [B8]
- [ ] P1-13 `jaccard_similarity`: check sizes before the zero-vector check.
  [B16]
- [ ] P1-14 `gen_random_bits`: validate `width >= 3` (interim until I5 replaces
  it). [B12]
- [ ] P1-15 `min_canonical`: define behaviour on the empty vector (return empty)
  and test it. [B13]
- [ ] P1-16 `shift_left_by_one`/`shift_right_by_one`: route through
  `shift_left(1)`/`shift_right(1)` so the padding invariant holds and the empty
  case works (full removal happens in Phase 2). [B11]

### Invariant enforcement

- [ ] P1-17 Add `tests/test_invariants.py`: a hypothesis test that applies a
  random sequence of public mutators and asserts (a) padding bits are zero, (b)
  `len(vector) == ceil(size/64)`, (c) `int(bv) == int(str(bv) or "0", 2)`. [I7]
- [ ] P1-18 Fix `test_reverse_involution` so it actually tests something. [B19]

### Protocol

- [ ] P1-19 Make `BitVector` satisfy `BitVectorProtocol` (add a read-only `size`
  property or drop `size` from the protocol in favour of `__len__`); mark the
  protocol `@runtime_checkable`; replace the `cast` in `test_protocol.py` with
  an `isinstance` check and a plain annotated assignment that the type checkers
  verify. [B17]

### Docs that are currently wrong

- [ ] P1-20 `docs/index.md`: replace `BitVector(intVal=42, size=8)` with
  `BitVector.from_int(42, size=8)`; remove "execute `BitVector.py` directly".
  [B25]
- [ ] P1-21 `docs/porting.md`: fix `int_val()` → `int(bv)`; audit the table
  against the real 3.5.0 method list (`intValue`, `getbit`, `setbit`,
  `circular_rotate_left_by_one`, `read_bits_from_file`, `close_file_object`,
  `more_to_read`, `fp=`, `filename=`, `rawbytes=`, `hexstring=`, `textstring=`,
  `bitstring=`, `intVal=`). [B25, #123]
- [ ] P1-22 `examples/README.md` and `README.md`: remove references to a
  `BitVector.py` in `examples/` and to running the module directly; add install
  \+ quick-start. [B25, T18]
- [ ] P1-23 `AGENTS.md`/`README.md`: stop claiming macOS/Windows CI until P4-12
  lands. [B29]

### Dead data and duplicates

- [ ] P1-24 Delete `tests/test_constructors.py` (no tests) and the codespell
  `ignore-words-list` entries that only existed for it. [B28, L15, L16]
- [ ] P1-25 Delete `examples/testinput{1,4,5}.txt`; remove the `testinput*.txt`
  / `test.txt` entries from `.gitignore`; stop `demo.py` writing to CWD (or
  delete `demo.py` now — see P2-11). [B22]
- [ ] P1-26 Remove the duplicate `test_bench_length`; fix the benchmark module
  docstring. [B27]
- [ ] P1-27 Typos: T1–T9, T11–T14, T17 in one `docs:`/`style:` PR.
- [ ] P1-28 Tag `v0.1.0`.

______________________________________________________________________

## Phase 2 — Shed Legacy (release 0.2.0)

Remove every code path, test, and file that exists only because 3.5.0 did it. No
deprecation shims (D8).

- [ ] P2-1 Remove the `list`/`tuple` `vector` fallbacks in `__add__` and
  `__deepcopy__` and the two tests that monkeypatch `vector` to a tuple. [L1]
- [ ] P2-2 Remove the `isinstance(pos, tuple)` branch in `__setitem__` and the
  `(0,)` test case. [L2]
- [ ] P2-3 Remove `_hexdict`; implement `from_bytes`, `from_hex`, `from_string`
  via `bytes.fromhex`/`str.encode` + `translate(_BIT_REV_8)` + `array.frombytes`
  (same path as `from_file_path`). [L4, I8]
- [ ] P2-4 Remove `shift_left_by_one`/`shift_right_by_one`. [L5]
- [ ] P2-5 Remove `bit_count_sparse` and `is_power_of_2_sparse`; keep the
  benchmarks pointed at the surviving methods. [L6]
- [ ] P2-6 **decision D4 (resolved: remove)** Remove `gcd`,
  `multiplicative_inverse`, `test_for_primality`, `gen_random_bits`; document
  stdlib replacements in `porting.md`; add
  `BitVector.random(n, *, rng=secrets.randbits)`. [L7, L8, I5]
- [ ] P2-7 Remove `set_value`. [L9]
- [ ] P2-8 Replace `reset(val)` with `fill(bit)` and `clear()`; remove
  `divide_into_two` (document `bv[:n], bv[n:]`). [L10]
- [ ] P2-9 Rewrite legacy error messages (T12) with the
  `f"<what> <value> <constraint>"` pattern and the right exception types.
- [ ] P2-10 `gf_MI` → `gf_inverse`, raising `ZeroDivisionError` (or
  `ValueError`) with the GCD in the message instead of returning a string;
  `gf_divide_by_modulus` → `gf_divmod`; `while 1` → proper loop. [L12, B20]
- [ ] P2-11 Delete `examples/demo.py`; replace with 3–5 focused scripts
  (`examples/basics.py`, `examples/io.py`, `examples/gf2.py`, …) each with a
  `main()` and executed by a CI step; or move them into doctested
  `docs/examples.md`. [L14, B26]
- [ ] P2-12 Rename `__contains__(self, otherBitVec)` → `other`; drop the
  `N802`/`N803`/`N806` ruff ignores and fix the `MOD`/`MI`/`NUM` names. [T11]
- [ ] P2-13 Make storage private (`_words`) with a read-only `memoryview`
  accessor if anything outside the class still needs it; update tests to use the
  public API instead of `_size`/`vector`. [L18, I9]
- [ ] P2-14 Tag `v0.2.0`.

______________________________________________________________________

## Phase 3 — Pythonic API (release 0.3.0)

Breaking changes land together here so users migrate once.

### Package and naming

- [ ] P3-1 **decision D1 (resolved: keep BitVector)** Move to `src/BitVector/`
  (or keep `BitVector/`) (`_core.py`, `_gf2.py`, `_io.py`, `protocol.py`);
  update `pyproject.toml`, imports, docs, `mkdocs.yml`; drop the `N999`/`INP001`
  ignores. [L17, I11]
- [ ] P3-2 Single-source the version: `importlib.metadata.version(...)` in
  `__init__.py`; remove `__version__` from the module body. [B24]

### Constructors

- [ ] P3-3 **decision D9 (resolved: keep size=/bitlist=)** Retain keyword-only
  constructor parameters `size=` and `bitlist=`; add `zeros(n)`/`ones(n)`
  classmethods; `from_int(value, *, length=None)`;
  `from_bytes(data: Buffer, *, bit_order="big")`; `fromhex`;
  `from_text(s, *, encoding="utf-8")`; `from_stream`; `from_file`. [I1, I6]

### Sequence protocol

- [ ] P3-4 **decision D2 (resolved: IndexError and clamping)** Subclass/register
  `collections.abc.Sequence[int]`; `IndexError` for out-of-range indices;
  clamping slices; full `step` support in `__getitem__` and `__setitem__` (value
  may be an `int` broadcast or any iterable of bits of matching length). \[B21,
  I1\]
- [ ] P3-5 `__contains__` accepts an `int` bit or a sub-vector; add `find`,
  `rfind`, `index`, `count`, `startswith`, `endswith` with `bytes` semantics.
  [I1]
- [ ] P3-6 `@overload`s for `__getitem__`; remove every remaining `Any`
  (`permute_list`, `bitlist`, `fp`, `file_out`, `stream`, `memo`). \[I3, I6,
  T17\]

### Representation and conversion

- [ ] P3-7 Implement `__index__` [D10 (resolved: implement)]; `__repr__` →
  `BitVector('10110')` (round-trips via `eval` in a test); explicit `__bool__`;
  `__bytes__`; `to_bytes(*, bit_order, pad)`; `hex()`; `decode(encoding)`;
  `write_to(stream)`; `__buffer__` (PEP 688) exposing the words read-only. [I2]
- [ ] P3-8 **decision D5 (resolved: drop byteswap branches)** Remove the
  big-endian byteswap branches and document the internal layout in
  `docs/design.md`; or add a big-endian CI job and make every path consistent.
  [B18]
- [ ] P3-9 `__str__` via `format(int(self), f"0{len(self)}b")` (empty → "").
  [I8]

### Operators

- [ ] P3-10 **decision D3 (resolved: drop cross-type ==)** Drop cross-type
  `==`/`!=` with `int`/`float`; keep ordering between `BitVector`s. [L13]
- [ ] P3-11 **decision D12 (resolved: logical shifts)** `<<`/`>>` become logical
  shifts returning new objects; add `rotate_left(n)`/`rotate_right(n)` (+
  in-place variants) for the old behaviour; keep `shift_left`/`shift_right` as
  the in-place forms or fold them into `<<=`/`>>=`. [I1]
- [ ] P3-12 **decision D11 (resolved: require equal lengths)** Require equal
  lengths and raise `ValueError` for `&`, `|`, `^`. [I1]
- [ ] P3-13 **decision D13 (resolved: return new vector)** `reverse()` returns a
  new vector (pure function/copy). [I1]
- [ ] P3-14 `runs()` returns `list[tuple[int, int]]` (bit, run length) instead
  of strings; `min_canonical` → `min_rotation`. [I1]
- [ ] P3-15 `pad_from_left/right` → `pad_left/pad_right` (in place) and
  `ljust/rjust`-style copies if useful.

### Tests and typing

- [ ] P3-16 `tests/conftest.py`: `bitstrings()`, `bitvectors()`, and
  `aligned_sizes()` hypothesis strategies; a hypothesis CI profile
  (`max_examples` higher on `main`). [I9]
- [ ] P3-17 `tests/test_model.py`: model-based property tests comparing every
  public method against a reference built on `str`/`int` (slicing, shifts,
  rotations, concatenation, bitwise ops, find/count, conversions). [I9]
- [ ] P3-18 De-duplicate tests (empty-rotation error, `__str__`, permute cases);
  stop touching `_size`/`_words` from tests; type the `benchmark` fixture as
  `BenchmarkFixture`; drop the hypothesis `type: ignore`s. [I9]
- [ ] P3-19 Enable `mypy --strict` and pyright `strict` for `src/` **and**
  `tests/`; make `ty` and `pyrefly` run on tests too. [I6]
- [ ] P3-20 `tests/conformance/`: protocol-level tests parameterised over the
  implementation class so future backends reuse them. [I16]
- [ ] P3-21 Rewrite `docs/porting.md` for the final names; write
  `docs/design.md` (bit order, word layout, invariants, complexity table). [I15]
- [ ] P3-22 Tag `v0.3.0`.

______________________________________________________________________

## Phase 4 — Packaging, Tooling, CI/CD (release 0.4.0)

Independent of the API; can start any time.

### Packaging

- [ ] P4-1 PEP 639: `license = "PSF-2.0"`, `license-files = ["LICENSE"]`; drop
  the `License ::` classifier if present; add `Typing :: Typed`,
  `Development Status :: 4 - Beta`, `Operating System :: OS Independent`,
  `Intended Audience :: Developers`,
  `Topic :: Software Development :: Libraries`. [I11]
- [ ] P4-2 Fix `maintainers` (schwehr); add `Documentation` and `Changelog`
  URLs. [T15]
- [ ] P4-3 Dynamic version from git tags (`uv-dynamic-versioning` or
  `hatch-vcs`); verify `uv build` from a clean clone. [B24]
- [ ] P4-4 Evaluate `uv_build` as the build backend; keep `hatchling` if
  anything is missing.
- [ ] P4-5 `[tool.uv] required-version`; `uv lock --check` in CI.

### Lint/format/type configuration

- [ ] P4-6 Ruff: move test-only ignores (`S101`, `ANN001`, `D103`, `PLR2004`,
  `SLF001`, `PT012`) to `per-file-ignores`; enable `ANN001`, `ANN401`, `B905`,
  `D401`, `EM101/102`, `TRY003`, `FBT001`, `TC003`; set `preview = true`; review
  the rest of the ignore list rule by rule. [I12, #249]
- [ ] P4-7 Pytest: `--strict-markers --strict-config -ra`,
  `filterwarnings = ["error"]`, `xfail_strict = true`; move `--cov` out of
  `addopts` into the CI command so local runs and benchmarks are fast.
- [ ] P4-8 Coverage `fail_under = 100`.
- [ ] P4-9 Pylint: convert every global `disable` to a local one or remove
  pylint if ruff covers everything that still fires (issue #142).
- [ ] P4-10 Pre-commit additions: `validate-pyproject`, `pyproject-fmt`,
  `check-github-workflows` (check-jsonschema) or `actionlint`, `uv-pre-commit`
  (`uv-lock`), `taplo` (TOML), `markdownlint` or keep `mdformat` only. Remove
  hooks that duplicate ruff.
- [ ] P4-11 Mutation testing: add `mutmut` (or `cosmic-ray`) with a recorded
  baseline score and a non-regressing CI gate (issue #211). [I10]

### CI

- [ ] P4-12 Re-enable macOS and Windows in `test.yml`; add `3.14t`
  (free-threaded) and `3.15-dev` with `continue-on-error: true`;
  `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }`.
  [I13]
- [ ] P4-13 Build job on every PR: `uv build`, `twine check dist/*` (or
  `uv publish --check`), install the wheel into a fresh venv and run the test
  suite against the installed package.
- [ ] P4-14 Docs job: `mkdocs build --strict` on PRs; deploy to GitHub Pages on
  `main`; set `site_url` accordingly. [T16, I15]
- [ ] P4-15 Benchmark regression tracking (CodSpeed or
  `benchmark-action/github-action-benchmark`) with alerts on >20% slowdowns.
- [ ] P4-16 Security: `pip-audit`/`uv audit` job; OSV scanner (issue #53); keep
  zizmor and bandit. (issue #210)
- [ ] P4-17 Dependabot: switch `pip` → `uv` ecosystem so `uv.lock` is updated;
  group minor/patch updates.
- [ ] P4-18 Lychee: also check `docs/` output links; add a `.lycheeignore`
  review.

### Release pipeline

- [ ] P4-19 Trusted Publishing: `permissions: id-token: write`, remove
  `PYPI_API_TOKEN`, remove the zizmor suppression; configure the PyPI publisher
  for the `pypi` environment. [B23, I14]
- [ ] P4-20 `actions/attest-build-provenance` for `dist/*`; upload attestations
  to the GitHub Release. [I14]
- [ ] P4-21 Guard job: fail if `git tag` (`v1.2.3` / `v1.2.3rc1`) ≠ built
  version; fix README release instructions to PEP 440 spelling. [B23]
- [ ] P4-22 CHANGELOG automation from Conventional Commits (`git-cliff` or
  `release-please`); publish it in the GitHub Release notes and `docs/`.
- [ ] P4-23 `CONTRIBUTING.md` (branching, commits, review checklist, how to run
  the full tool chain) and a `SECURITY.md` refresh once releases are real.
- [ ] P4-24 Tag `v0.4.0`.

______________________________________________________________________

## Phase 5 — Performance (release 0.5.0)

Each item: benchmark before, change, benchmark after, record in
`docs/design.md`.

- [ ] P5-1 `write_to`/`to_bytes`: `translate(_BIT_REV_8)` on `tobytes()` instead
  of a per-bit loop. [I8]
- [ ] P5-2 `reverse`: byte-wise reversal via `_BIT_REV_8` + word reversal +
  shift, instead of per-bit set. [I8]
- [ ] P5-3 Slice assignment: word-level copy with shift/mask. [I8]
- [ ] P5-4 `__contains__`/`find`: integer-based or string-based search
  (`str(self).find(str(sub))`) with no per-position slice allocation; consider
  two-way/`bytes.find` on byte-aligned cases. [I8]
- [ ] P5-5 `min_rotation`: Booth's O(n) algorithm, or integer rotation without
  deep copies. [I8]
- [ ] P5-6 `gf_multiply`/`gf_divmod`/`gf_inverse`: carry-less multiply on Python
  `int`s with a single conversion at the boundary. [I8]
- [ ] P5-7 `rotate_*` in-place: single pass, no `deepcopy`. [I8]
- [ ] P5-8 `permute`/`unpermute`: build an `int` then one `from_int`, or a
  word-level gather. [I8]
- [ ] P5-9 `is_power_of_2`: `(v & (v - 1)) == 0` on `int(self)` without
  allocating a vector. [I8]
- [ ] P5-10 `rank`: word-level popcount prefix; no slice allocation. [I8]
- [ ] P5-11 Decide on `__int__` caching (issue #92): measure; implement only
  with a cheap invalidation strategy or reject.
- [ ] P5-12 Publish a complexity table (method → O(words) / O(bits) / O(1)) in
  `docs/design.md` and keep it in sync via a docs test.
- [ ] P5-13 Tag `v0.5.0`.

______________________________________________________________________

## Phase 6 — API Freeze and 1.0

- [ ] P6-1 Two consecutive minor releases with no breaking changes.
- [ ] P6-2 Conformance suite (`tests/conformance/`) green; protocol documented
  as the extension point.
- [ ] P6-3 README feature matrix vs `bitarray`/`bitstring`/`numpy.packbits` with
  benchmark numbers (issue #37).
- [ ] P6-4 `Development Status :: 5 - Production/Stable`; tag `v1.0.0`.

______________________________________________________________________

## Phase 7 — Post-1.0 Exploration

- [ ] P7-1 Backend experiments behind `BitVectorProtocol`: Python `int`,
  `bytearray`, NumPy `uint64` (#79), mmap (#74/#76), Rust/pyo3 (#77); each must
  pass the conformance suite and be judged by the benchmark suite. [I16]
- [ ] P7-2 `FrozenBitVector` (hashable, usable as dict keys / set members).
  [I18]
- [ ] P7-3 Free-threading: run the suite under `3.14t` with `PYTHON_GIL=0`;
  document thread-safety guarantees. [I17]
- [ ] P7-4 Optional Textual TUI as a separate distribution (issue #21). [I18]
- [ ] P7-5 Writing-style checks for docs (issue #239): `vale` or similar.
