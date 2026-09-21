# BitVector

[![Test](https://github.com/schwehr/bitvector-modern/actions/workflows/test.yml/badge.svg)](https://github.com/schwehr/bitvector-modern/actions/workflows/test.yml)
[![Check Links](https://github.com/schwehr/bitvector-modern/actions/workflows/lychee.yml/badge.svg)](https://github.com/schwehr/bitvector-modern/actions/workflows/lychee.yml)

The `BitVector.py` module is for a memory-efficient packed representation of bit
vectors and for the processing of such vectors.

If you wish, you can execute the code in `BitVector.py` directly in this
directory prior to the installation of the module. This will execute all of the
example code in the module file.

To see a working example of the `BitVector` module, see the file:

- [`examples/demo.py`](examples/demo.py)

This is a fork from Avi Kak's BitVector 3.5.0.

## Development

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management
and [`pre-commit`](https://pre-commit.com/) to enforce code quality and
conventional commit messages.

`pyupgrade` runs as part of the pre-commit checks, so syntax modernization is
applied automatically for developers and enforced in CI on every pull request
and push.

After cloning the repository, set up the development environment and register
both pre-commit and commit-msg git hooks:

```bash
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

You can also run the hook on demand:

```bash
uv run pre-commit run pyupgrade --all-files
```

To execute the automated test suite and check code coverage:

```bash
uv run pytest
```

To run coverage without benchmark tests and generate an HTML report:

```bash
uv run pytest --benchmark-skip --cov-report=html
```

To continuously run adaptive, coverage-guided property-based fuzzing on the
hypothesis test suite (`tests/test_properties.py`):

```bash
uv run hypothesis fuzz tests/test_properties.py
```

## Releasing

Releases are automated via GitHub Actions. We strictly adhere to
[Semantic Versioning 2.0.0](https://semver.org/).

### Release Process

To trigger a new package build and release:

1. **Bump Version**: Update the version string in `pyproject.toml`.
   - For final releases, use `X.Y.Z` (e.g., `1.0.0`).
   - For release candidates, append `-rc.N` (e.g., `1.0.0-rc.1`, `1.0.0-rc.2`).
1. **Commit and Push**: Push the version change to `main` (typically via a pull
   request).
1. **Tag and Push**: Create and push a git tag matching the version, prefixed
   with a `v`:
   ```bash
   # Example for a release candidate
   git tag v1.0.0-rc.1
   git push origin v1.0.0-rc.1

   # Example for a final release
   git tag v1.0.0
   git push origin v1.0.0
   ```

### Release Workflow Execution

The `Release` workflow is triggered by tags matching `v[0-9]*.[0-9]*.[0-9]*`. It
executes the following steps:

- **Verification**: Runs the test suite to ensure the package builds cleanly.
- **Build**: Compiles package wheels and source distributions using `uv build`.
- **Publish to PyPI**: Publishes the package to PyPI (requires PyPI Trusted
  Publishing setup).
  - Prerelease versions (like `v1.0.0-rc.1`) are published as pre-releases on
    PyPI.
- **GitHub Release**: Creates a GitHub Release, uploads the built artifacts
  (`dist/*`), and auto-generates release notes.
  - Prerelease tags (containing `-rc`, `-beta`, `-alpha`, or `-pre`) are
    automatically marked as **Pre-release** on GitHub.
