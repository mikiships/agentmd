# Copilot Instructions

GitHub Copilot context for this repository. Copilot uses this file to tailor suggestions to the project's conventions.

## Project Overview
**Primary languages:** Python
**Package managers:** pip
**CI:** GitHub Actions

## Build, Test, and Lint Commands
**Install dependencies:**
```
pip install -e '.[dev]'
```
**Run tests:**
```
python3 -m pytest tests/ -x
```
**Lint / format:**
```
ruff check . && ruff format --check .
```

## Directory Structure
**Top-level directories:** `.github`, `agentmd`, `tests`
**Test roots:** `tests`
**Most-changed directories:** `agentmd`, `tests`, `README.md`, `pyproject.toml`, `progress-log.md`

## Coding Standards
### Python
- Type-annotate all public functions and class attributes.
- Use dataclasses or Pydantic models for structured data — avoid plain dicts for complex payloads.
- Keep functions focused: one responsibility per function, typically under 40 lines.
- Use `pathlib.Path` for file operations, not `os.path`.
- Prefer f-strings over `.format()` or `%` formatting.
- Code style enforced by `ruff`; do not fight the formatter.

## Test Patterns
**Run tests:** `python3 -m pytest tests/ -x`
- Test files live in `tests/`, named `test_*.py`.
- Use `pytest.fixture` for reusable test setup.
- Use `pytest.mark.parametrize` for table-driven tests.
- Mock external services with `unittest.mock` or `pytest-mock`.
- One logical assertion per test where possible; complex state assertions can use multiple asserts.

## Conventions Inferred from Codebase
**Commit prefix style:** `feat`, `fix`, `chore`, `docs`, `feat(d3)` (follow this pattern)
**Common file extensions:** `.pyc`, `.py`, `.md`, `.toml`, `.yml`
- Python: use type hints on all public functions
- Python: snake_case for functions/variables, PascalCase for classes
- Tests: files named `test_*.py`, functions named `test_*`

## PR Review Checklist
Copilot should flag suggestions or changes that violate any of the following:

- [ ] All new public functions have type annotations and docstrings.
- [ ] No hardcoded secrets, credentials, or environment-specific paths.
- [ ] New behavior is covered by at least one test.
- [ ] Existing tests are not deleted or skipped to make CI pass.
- [ ] Dependencies added to the lock file and justification noted in the PR.
- [ ] Commit messages follow the project prefix convention.
- [ ] Test suite passes: `python3 -m pytest tests/ -x`
- [ ] Linting clean: `ruff check . && ruff format --check .`
