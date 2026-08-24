## Description

Please include a summary of the changes and which issue is addressed (if
applicable).

## Mandatory Code Review Checklist

Before submitting or approving this PR, ensure the following requirements from
`AGENTS.md` are met:

- [ ] **Performed code review**: Reviewed the code changes for bugs, style, and
  correctness.
- [ ] **Proposed 1-3 code improvements**: Suggested or implemented 1–3
  improvements based on the current changes.
- [ ] **Checked if `AGENTS.md` needs updates**: Verified whether project
  instructions, architecture notes, or rules need updating based on these
  changes.

## Type of Change

- [ ] Bug fix (`fix(scope): ...`)
- [ ] New feature (`feat(scope): ...`)
- [ ] Breaking change (`feat!:` or `fix!:`)
- [ ] Documentation update (`docs: ...`)
- [ ] Chore / Refactor (`chore: ...` / `refactor: ...`)

## Checklist

- [ ] My code follows the code style and modern Python (`>=3.14`) standards of
  this project.
- [ ] I have written new/refactored tests in the **best modern `pytest` form**
  (using `assert`, fixtures, `@pytest.mark.parametrize`).
- [ ] My commit messages adhere to the **Conventional Commits** specification
  and do **not** contain `TAG=` or `CONV=` entries.
- [ ] All new and existing tests pass (`uv run pytest`).
- [ ] Pre-commit checks pass locally (`uv run pre-commit run --all-files`).
