# .cursorrules

Cursor IDE rules. These rules are applied to every AI interaction in this project.

## Always
- Read the relevant source files before making changes.
- Make minimal, targeted edits — avoid reformatting unrelated code.
- Respect the existing code style (indentation, naming, import order).
- Run `python3 -m pytest tests/ -x` after every non-trivial change.
- Run `ruff check . && ruff format --check .` before finalizing changes.
- Add type annotations to all new public functions.
- Use `pathlib.Path` instead of `os.path` for file operations.

## Never
- Never commit API keys, tokens, or credentials.
- Never delete tests to make the suite pass.
- Never use `TODO` comments without a linked issue or explanation.
- Never make changes outside the scope of the current task without flagging them.
- Never use `except:` without specifying the exception type.
- Never use `eval()` or `exec()` on untrusted input.

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

## File Patterns
**Test files:** `tests/**`
**Python source:** `**/*.py`
**Python tests:** `**/test_*.py`, `**/*_test.py`

## Conventions Inferred from Codebase
**Commit prefix style:** `feat`, `fix`, `chore`, `docs`, `feat(d3)` (follow this pattern)
**Common file extensions:** `.pyc`, `.py`, `.md`, `.toml`, `.yml`
- Python: use type hints on all public functions
- Python: snake_case for functions/variables, PascalCase for classes
- Tests: files named `test_*.py`, functions named `test_*`

## Context Preferences
When writing or reviewing code, prefer to include in context:
- `tests/` (primary code locations)
- The file being edited and its direct imports.
- Relevant test files alongside source files.
- Configuration files when modifying build or tooling behavior.
