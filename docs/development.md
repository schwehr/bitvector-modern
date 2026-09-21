# Development

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management
and [`pre-commit`](https://pre-commit.com/) to enforce code quality and
conventional commit messages.

`pyupgrade` is part of the pre-commit suite, which means modern syntax cleanup
runs locally for developers and is enforced again by CI on every pull request
and push.

## Setup

After cloning the repository, set up the development environment and register
both pre-commit and commit-msg git hooks:

```bash
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

To run only the syntax modernization hook on demand:

```bash
uv run pre-commit run pyupgrade --all-files
```

## Testing

To execute the automated test suite and check code coverage:

```bash
uv run pytest
```

To continuously run adaptive, coverage-guided property-based fuzzing on the
hypothesis test suite (`tests/test_properties.py`):

```bash
uv run hypothesis fuzz tests/test_properties.py
```

## Building Documentation

To build and view the documentation locally:

```bash
uv run mkdocs serve
```
