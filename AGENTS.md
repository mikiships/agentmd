# AGENTS.md

Agent context for OpenAI Codex. This file is read automatically by the Codex sandbox at session start.

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

## Sandbox Awareness
The Codex sandbox has network access disabled by default during code execution.
- Do not make HTTP requests in tests — mock all external calls.
- Do not rely on system-installed tools; prefer project-local binaries (`./node_modules/.bin/`, virtualenv, etc.).
- The sandbox resets between sessions — do not rely on persistent state outside the repo.
- Python dependencies: install into a virtualenv. The sandbox may not have all packages pre-installed.

## Conventions Inferred from Codebase
**Commit prefix style:** `feat`, `fix`, `chore`, `docs`, `feat(d3)` (follow this pattern)
**Common file extensions:** `.pyc`, `.py`, `.md`, `.toml`, `.yml`
- Python: use type hints on all public functions
- Python: snake_case for functions/variables, PascalCase for classes
- Tests: files named `test_*.py`, functions named `test_*`

## apply_patch Usage
When modifying files, prefer `apply_patch` over full-file writes for surgical changes:
- Keep patches small and focused on the minimal diff.
- After applying a patch, run the test command to verify correctness.
- Use `apply_patch` with `create` action for new files, `modify` for existing ones.
- For large structural refactors, consider writing the full new file instead of a complex patch.

## Approval Gates
Before marking a task complete, verify ALL of the following:
- [ ] Tests pass: `python3 -m pytest tests/ -x`
- [ ] Linting clean: `ruff check . && ruff format --check .`
- [ ] No unintended files modified (check `git diff --stat`)
- [ ] New code has corresponding tests (if behavior change)
- [ ] Commit message follows the project prefix convention

## Anti-Patterns to Avoid
- **Do not** make network calls in the sandbox — all external calls must be mocked.
- **Do not** commit secrets, API keys, or credentials.
- **Do not** modify test fixtures or golden files to make tests pass without understanding why.
- **Do not** introduce new dependencies without updating the lock file.
- **Do not** skip linting or type-check steps — they are part of the approval gate.
