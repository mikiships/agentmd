# CLAUDE.md

Agent context for Claude Code. Keep this file up to date as the project evolves.

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

## Conventions Inferred from Codebase
**Commit prefix style:** `feat`, `fix`, `chore`, `docs`, `feat(d3)` (follow this pattern)
**Common file extensions:** `.pyc`, `.py`, `.md`, `.toml`, `.yml`
- Python: use type hints on all public functions
- Python: snake_case for functions/variables, PascalCase for classes
- Tests: files named `test_*.py`, functions named `test_*`

## Claude Code Tips
- Use `/compact` when context grows large mid-session to avoid token limit errors.
- Use `/review` before committing to get a focused code review.
- Use `/init` in a new checkout to re-read this file and orient yourself.
- Open multiple files in a single message when changes span files — reduces round-trips.
- Prefer small, targeted edits over full-file rewrites when touching existing code.
- After every non-trivial change, run `python3 -m pytest tests/ -x` to confirm nothing broke.

## Style Guide
- All public functions and methods must have type annotations.
- Docstrings: use triple-quoted strings on public classes and functions.
- Maximum line length: 100 characters (unless project config says otherwise).
- Imports: standard library first, third-party second, local last (separated by blank lines).
- Linting enforced by `ruff` — run `ruff check .` before committing.

## Anti-Patterns to Avoid
- **Do not** make broad refactors outside the scope of the current task.
- **Do not** delete or skip existing tests to make CI green.
- **Do not** add dependencies without noting them in the commit message.
- **Do not** use bare `except:` — always catch specific exceptions.
- **Do not** use mutable default arguments (e.g., `def f(x=[])`).
