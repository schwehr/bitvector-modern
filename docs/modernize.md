# Modernizing Pure-Python Projects: A Step-by-Step Guide

This guide provides a systematic, repeatable roadmap for modernizing legacy
pure-Python codebases. Based on real-world modernization experiences, these
steps transform older Python libraries into idiomatic, well-tested, high-
performance packages that leverage modern Python (>=3.13) features, tooling, and
packaging standards.

______________________________________________________________________

## Overview of Modernization Phases

When modernizing a library, executing steps in the right order minimizes
breakage, ensures continuous verification, and avoids redundant refactoring. The
recommended modernization phases are:

1. **Phase 1: Spec-Driven Setup, Governance, & Dependency Management**
1. **Phase 2: Test Infrastructure, Coverage, & Benchmarking (`pytest`)**
1. **Phase 3: Style, Formatting, & Static Analysis Guardrails**
1. **Phase 4: Python Syntax & Language Modernization**
1. **Phase 5: Strict Static Typing & Protocols**
1. **Phase 6: Idiomatic API & Architectural Refactoring**
1. **Phase 7: Performance & Memory Optimization**
1. **Phase 8: Documentation, CI/CD Automation, & Governance**

______________________________________________________________________

## Phase 1: Spec-Driven Setup, Governance, & Dependency Management

Modern Python projects establish clear planning and AI/developer governance
before replacing legacy packaging (`setup.py`, `setup.cfg`, `requirements.txt`,
and `MANIFEST.in`) with unified declarative configuration.

- **Create Spec-Driven Development (SDD) Documents**:
  - Create a `PRD.md` (Product Requirements Document), `SPEC.md` (Technical
    Specification), and `TASKS.md` (actionable task checklist) in Spec-Driven
    Development style to plan and track the modernization initiative.
- **Create a Minimal `AGENTS.md` Guide**:
  - Create an initial `AGENTS.md` file at the repository root to guide AI
    assistants and developers.
  - Start with strict version control rules: enforce **Conventional Commits**
    and explicitly mandate **NO Tag or Conversation ID Entries** in commits.
  - Evaluate the project as it stands and fill out all sections (overview,
    layout, commands, standards) as they currently are.
  - Include explicit instructions to continuously update all sections of
    `AGENTS.md` as the codebase evolves throughout the SDD modernization
    process.
- **Configure Initial Pre-Commit Hooks (`conventional-pre-commit` &
  `mdformat`)**:
  - Configure an initial `.pre-commit-config.yaml` to run
    `conventional-pre-commit` (enforcing Conventional Commits) and `mdformat`
- **Adopt `pyproject.toml` (PEP 517 / PEP 621)**:
  - Remove legacy packaging files and `setuptools` build dependencies.
  - Define all package metadata, a modern build backend (such as `hatchling`),
    and dependency specifications in a single standard `pyproject.toml`
    configuration file.
- **Use Modern Dependency & Environment Management (`uv`)**: Manage virtual
  environments, dependencies, and lockfiles (`uv.lock`) for deterministic builds
  across environments.
- **Standardize Package Directory Layout**: Ensure code resides cleanly in a
  package directory or `src/` layout, with dedicated `tests/`, `docs/`, and
  `examples/` directories at the project root.
- **Set Minimum Python Target**: Drop obsolete Python versions and declare an
  explicit minimum Python version requirement (e.g., `>=3.13`) in metadata and
  classifiers.

______________________________________________________________________

## Phase 2: Test Infrastructure, Coverage, & Benchmarking

Before changing internal logic or APIs, establish an automated safety net.

- **Migrate to Idiomatic `pytest`**:
  - Replace legacy `unittest.TestCase` hierarchies and assertions
    (`self.assertEqual`, `self.assertTrue`) with standard Python `assert`
    statements.
  - Use `@pytest.mark.parametrize` to cleanly cover edge cases without
    boilerplate.
  - Use standard pytest fixtures (`tmp_path`, etc.) instead of manual file
    cleanup.
  - Verify expected errors using `pytest.raises(...)` with specific exception
    types.
- **Enforce Automated Code Coverage (`pytest-cov`)**:
  - Track branch and line coverage continuously.
  - Enforce a strict minimum coverage threshold in CI (e.g., `--fail-under=95`),
    striving for 100% coverage on new features and refactored modules.
- **Implement Property-Based & Fuzz Testing (`hypothesis`)**:
  - Add invariant and property-based test suites to uncover edge cases that
    manual unit tests might miss.
  - Use tools like `hypofuzz` for continuous coverage-guided fuzzing.
- **Establish Performance Benchmarks (`pytest-benchmark`)**:
  - Create regression benchmarks for critical algorithms and data structures
    early in the process. This ensures subsequent refactorings and optimizations
    can be quantitatively verified against baseline performance.

______________________________________________________________________

## Phase 3: Style, Formatting, & Static Analysis Guardrails

Implement automated linting and formatting so team members and AI assistants
share consistent style guardrails.

- **Unify Linting & Formatting (`ruff`, `pylint`)**:
  - Use `ruff` for fast, comprehensive formatting and linting (import sorting,
    style checks, bug detection).
  - Enable explicit linter checkers (e.g., checking for unnecessary dunders,
    pointless statements, and unused arguments).
- **Standardize Markdown & Documentation Formatting**:
  - Enforce consistent line wrapping (e.g., 80-column width) and GFM style
    across markdown documentation using `mdformat`.
  - Enforce automated spell-checking across documentation and docstrings using
    `codespell`.
- **Expand Pre-Commit Hook Guardrails**:
  - Expand `.pre-commit-config.yaml` to run code formatters (`ruff-format`),
    linters (`ruff`), type checkers (`mypy`, `ty`), and spell checkers
    (`codespell`) automatically before commits alongside the initial hooks.
- **Adopt Static Security & Vulnerability Scanning**:
  - Integrate static analysis tools (`semgrep`, `bandit`, and workflow scanners
    like `zizmor` for GitHub Actions) to catch security antipatterns early.
- **Standardize Version Control Workflows**:
  - Require feature branches for all changes.
  - Enforce **Conventional Commits** (`<type>(<scope>): <subject>`) to ensure a
    readable, automated git history.

______________________________________________________________________

## Phase 4: Python Syntax & Language Modernization

Modernize syntax to take full advantage of recent Python language evolutions.

- **Automated Syntax Upgrades (`pyupgrade`)**:
  - Automatically strip Python 2 and older Python 3 compatibility artifacts
    (such as inheriting from `object`, redundant `super()` arguments, and old
    exception syntax).
- **Convert to Modern Formatted Strings (f-strings)**:
  - Replace legacy `%`-formatting and `.format()` calls with readable, highly
    performant f-strings (`f"Value: {val}"`).
- **Standardize Docstrings**:
  - Adhere strictly to a structured convention (e.g., standard **Google Python
    Docstring Style**) across all modules, classes, and methods, including
    `Args:`, `Returns:`, `Raises:`, and `Attributes:` sections.
- **Modernize Libraries & Control Flow**:
  - Replace insecure or legacy standard library patterns (e.g., switching from
    `random` to `secrets` for security-sensitive or modern RNG generation).
  - Use modern control flow idioms: comprehensions, generator expressions,
    context managers (`with` statements) for I/O, and `in` operators for
    membership checks.

______________________________________________________________________

## Phase 5: Strict Static Typing & Protocols

Introduce explicit type systems to prevent runtime type errors and improve IDE
support.

- **Enable `ty` and Fix Existing Type Issues**:
  - Enable `ty` (`astral-sh/ty`) as a fast initial static type checker to
    identify and fix baseline type errors and missing annotations.
- **Add Complete Function & Attribute Annotations**:
  - Annotate all method signatures, return values, and instance attributes.
  - Avoid ambiguous `Any` types; prefer precise types such as `Sequence`,
    `Buffer`, and `Literal`.
- **Use Modern Type Syntax (PEP 585 / PEP 604)**:
  - Use standard collection types directly (`list[int]`, `dict[str, int]`).
  - Use the union operator (`|`) instead of `Union` or `Optional`
    (`int | None`).
  - Use `typing.Self` for fluent interface return types and class constructors.
- **Define Structural Interfaces via Protocols**:
  - Define `typing.Protocol` classes for public APIs and data exchange to enable
    clean duck-typing and static verification.
- **Export Package Type Metadata (PEP 561)**:
  - Include a `py.typed` marker file inside the package directory so downstream
    consumers recognize type annotations.
- **Enforce Multi-Checker Static Verification**:
  - Enforce type soundness across additional static type checkers (`mypy`,
    `pyright`, and `pyrefly`) as the final step of the typing phase to guarantee
    cross-checker compatibility.

______________________________________________________________________

## Phase 6: Idiomatic API & Architectural Refactoring

Refactor the public API so that it feels natural to experienced Python
developers while decoupling orthogonal concerns.

- **Adopt Python Dunder Methods (Data Model Protocols)**:
  - Replace ad-hoc accessors, mutators, and sizing methods with standard dunders
    (`__getitem__`, `__setitem__`, `__len__`, `__iter__`, `__reversed__`,
    `__eq__`, `__int__`, and `__format__`).
  - Support arithmetic and bitwise operator overloading (`+`, `+=`, `&`, `|`,
    `^`, `~`) with clean immutability or in-place semantics as appropriate.
- **Clean Constructor & Factory Patterns**:
  - Require explicit keyword arguments for complex initialization.
  - Provide descriptive `classmethod` factory constructors (e.g., `from_bytes`,
    `from_hex`, `from_stream`) instead of overloaded, multi-modal `__init__`
    signatures.
- **Decouple Orthogonal Architecture**:
  - Separate data structures from file/stream I/O operations. Core data classes
    should operate on memory buffers, sequences, or streams rather than managing
    file paths directly.
- **Make Internal State Explicit**:
  - Prefix internal implementation attributes with an underscore (`_size`,
    `_vector`) to clarify the public API boundary.
- **Standardize Exception Types**:
  - Replace generic assertions with descriptive built-in exceptions
    (`ValueError`, `TypeError`, `IndexError`, or `KeyError`).

______________________________________________________________________

## Phase 7: Performance & Memory Optimization

Once tests, benchmarks, and APIs are stable, apply systematic optimizations. All
optimization work falls into four general categories:

### 1. Algorithmic & Built-in Acceleration

- Replace custom loops with high-performance Python built-ins and standard
  library C-implementations.
- Utilize specialized built-in methods (e.g., `int.bit_count()` for population
  counts, `int.from_bytes()`, and standard `copy.deepcopy()`).

### 2. Memory Layout & Packed Data Structures

- Transition from Python lists of objects to compact, contiguous storage types
  such as `array.array`, `bytearray`, or fixed-width integer words.
- Define `__slots__` on classes with high instance counts to eliminate per-
  instance `__dict__` overhead and reduce memory footprint.

### 3. Word-Level & Vectorized Processing

- Replace element-by-element or bit-by-bit Python iteration with block-level or
  word-level processing.
- Perform bitwise masking, bulk slice assignments, and shifts across entire data
  blocks or words simultaneously.

### 4. Allocation & Conversion Minimization

- Eliminate unnecessary intermediate object allocations.
- Pre-allocate correctly sized output containers before populating them.
- Avoid expensive conversions (such as hex/string representations) in critical
  hot paths.
- Replace eager list conversions (`list(map(...))`) with generator expressions
  or targeted comprehensions.

______________________________________________________________________

## Phase 8: Documentation, CI/CD Automation, & Governance

Ensure the modernized codebase is maintainable, well-documented, and accessible.

- **Modern Documentation Generation**:
  - Maintain a structured `docs/` directory using modern documentation engines
    (such as `mkdocs` with `mkdocstrings`) to generate API references directly
    from Google-style docstrings.
  - Provide a migration/porting guide for existing users upgrading from legacy
    versions.
- **Automated CI/CD Pipelines**:
  - Execute automated matrix testing across multiple operating systems (Linux,
    macOS, Windows) and Python versions via GitHub Actions.
  - Automate package building and secure release publishing to PyPI using
    Trusted Publishing (OIDC).
- **Project Governance & Community Standards**:
  - Add standard community health files (`SECURITY.md`, `CODE_OF_CONDUCT.md`,
    `CODEOWNERS`, pull request templates) and ensure `AGENTS.md` reflects the
    final modernized architecture.

______________________________________________________________________

## Evaluating the Order of Modernization Steps

When planning a modernization initiative, the **order of execution** is critical
to reducing friction and rework. Below is an evaluation of why the recommended
sequence is structured this way, along with trade-offs to consider:

### Why Testing (Phase 2) Comes Before Style (Phase 3) and Syntax (Phase 4)

- **Safety First**: Making any automated or manual syntax changes without a
  trusted, high-coverage test suite risks introducing silent regressions.
- **Alternative Consideration**: In some legacy projects, code formatting is so
  inconsistent that writing tests is difficult. In those cases, running an
  automated formatter (`ruff format`) *first* as a non-functional
  formatting-only commit can be beneficial before building the test suite.

### Why Static Typing (Phase 5) Precedes API Refactoring (Phase 6)

- **Tool-Assisted Refactoring**: Introducing strict type annotations first
  enables static type checkers (`mypy`, `pyright`, etc.) to guide you when
  refactoring constructors and dunder methods.
- **Alternative Consideration**: If an API is going to be completely replaced or
  removed (such as deprecated I/O helpers), typing those legacy methods first is
  wasted effort. In practice, type annotations and API refactoring often occur
  iteratively.

### Why Performance Optimization (Phase 7) Comes Late

- **Avoid Premature Optimization**: Optimizing code before stabilizing the
  public API and establishing a benchmark suite (`pytest-benchmark`) leads to
  wasted effort and unverified performance claims.
- **Regression Guard**: Benchmarks established in Phase 2 provide the baseline
  needed to prove that Phase 7 optimizations deliver real speedups without
  breaking behavior.

______________________________________________________________________

## Glossary

Below are definitions for acronyms and technical terms used throughout this
guide:

- **API (Application Programming Interface)**: A set of defined protocols,
  methods, and data structures that enable software components to communicate.
- **CI/CD (Continuous Integration / Continuous Deployment)**: Automated
  pipelines that build, test, lint, and publish software changes whenever code
  is pushed or merged.
- **GFM (GitHub Flavored Markdown)**: The dialect of Markdown used on GitHub,
  supporting features such as tables, strikethrough, autolinks, and task lists.
- **IDE (Integrated Development Environment)**: A software application (such as
  VS Code or PyCharm) providing comprehensive programming tools, including
  autocomplete, linting, and inline type checking.
- **OIDC (OpenID Connect)**: An identity authentication protocol used in Trusted
  Publishing to securely exchange short-lived tokens between CI/CD runners (like
  GitHub Actions) and package registries without storing static API keys.
- **PEP (Python Enhancement Proposal)**: Official design documents describing
  new language features, standards, or conventions for Python (e.g., PEP 517/621
  for `pyproject.toml`, PEP 561 for `py.typed`, PEP 585/604 for typing syntax).
- **PRD (Product Requirements Document)**: A planning document used in
  Spec-Driven Development that defines the goals, user stories, and high-level
  requirements for an initiative.
- **PyPI (Python Package Index)**: The official third-party software repository
  for Python where open-source packages are published and distributed.
- **RNG (Random Number Generator)**: An algorithm designed to generate a
  sequence of numbers without a predictable pattern. In modern Python,
  cryptographically secure generators (such as the `secrets` module) are
  preferred over legacy pseudo-random generators (`random`) for
  security-sensitive operations.
- **SDD (Spec-Driven Development)**: A methodology where specifications
  (`PRD.md`, `SPEC.md`, `TASKS.md`) are drafted and agreed upon before code
  implementation or refactoring begins.
- **SPDX (Software Package Data Exchange)**: An open standard for software
  license identifiers (e.g., `PSF-2.0`, `MIT`) used in modern package metadata
  and file headers.
- **SPEC (Technical Specification)**: An engineering document in Spec-Driven
  Development outlining the technical design, data structures, and migration
  strategy to fulfill a PRD.
- **VCS (Version Control System)**: Software (such as Git) that tracks changes
  to code over time and enables collaborative branching and revision history.
