# All-Day Build Contract: agentmd v0.1.0

Status: In Progress
Date: 2026-03-01
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentmd` — a Python CLI tool that analyzes a codebase and generates high-quality context files (CLAUDE.md, AGENTS.md, .cursorrules, copilot-instructions.md) for AI coding agents. The tool scans project structure, detects language/framework/test/lint configuration, and produces agent-specific context files optimized for each platform. Unlike Claude Code's `/init` (which only generates basic CLAUDE.md), agentmd is universal (works for all major agents) and deep (captures conventions, patterns, and anti-patterns from the actual codebase).

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. Project Analyzer (core)

Build the core analysis engine that scans a codebase and extracts structured metadata.

Required:
- `agentmd/analyzer.py` — main analyzer
- `agentmd/detectors/` — language, framework, test, lint, CI detectors
- `agentmd/types.py` — data models for analysis results

Detection targets:
- Language: Python, TypeScript/JavaScript, Rust, Go, Ruby, Java, C#, Swift
- Package manager: pip/uv/poetry, npm/pnpm/yarn, cargo, go mod, bundler, maven/gradle
- Framework: FastAPI, Flask, Django, Express, Next.js, React, Vue, actix-web, gin, Rails
- Test runner: pytest, jest, vitest, cargo test, go test, rspec, JUnit
- Linter: ruff, eslint, prettier, clippy, golangci-lint, rubocop
- CI: GitHub Actions, GitLab CI
- Project structure: monorepo detection, directory layout
- Git history: recent commit patterns, common file types changed
- Existing context files: detect and parse CLAUDE.md, AGENTS.md, .cursorrules, copilot-instructions.md

Output: `ProjectAnalysis` dataclass with all detected metadata.

- [ ] Language detection (at least 8 languages)
- [ ] Package manager detection
- [ ] Framework detection
- [ ] Test runner detection
- [ ] Lint/format detection
- [ ] CI detection
- [ ] Directory structure analysis
- [ ] Existing context file detection
- [ ] Tests for D1

### D2. Context File Generator (core + CLI)

Generate agent-specific context files from ProjectAnalysis.

Required:
- `agentmd/generators/base.py` — base generator
- `agentmd/generators/claude.py` — CLAUDE.md generator
- `agentmd/generators/codex.py` — AGENTS.md generator (Codex format)
- `agentmd/generators/cursor.py` — .cursorrules generator
- `agentmd/generators/copilot.py` — copilot-instructions.md generator
- `agentmd/templates/` — Jinja2 or string templates for each format

Each generator produces a complete, high-quality context file that includes:
- Project overview (language, framework, structure)
- Build/test/lint commands
- Key conventions detected from the codebase
- Directory structure explanation
- Common patterns and anti-patterns
- Agent-specific instructions (e.g., Claude Code slash commands, Codex sandboxing notes)

- [ ] Base generator with common sections
- [ ] Claude generator (CLAUDE.md)
- [ ] Codex generator (AGENTS.md)
- [ ] Cursor generator (.cursorrules)
- [ ] Copilot generator (copilot-instructions.md)
- [ ] `--target all` generates all four
- [ ] Output quality: generated files should be immediately usable (not scaffolds)
- [ ] Tests for D2

### D3. Context Scorer (analysis)

Score existing context files on completeness and quality.

Required:
- `agentmd/scorer.py` — scoring engine

Scoring dimensions (0-100 each, weighted composite):
- **Completeness** (30%): Does it cover build commands, test commands, lint, structure, conventions?
- **Specificity** (25%): Does it reference actual file paths, actual commands, actual patterns (vs generic advice)?
- **Clarity** (20%): Is it scannable? Proper markdown structure? Not a wall of text?
- **Agent-awareness** (15%): Does it use agent-specific features (Claude slash commands, Codex sandbox notes)?
- **Freshness** (10%): Is it consistent with the current codebase? (e.g., mentions files that exist)

Output: score per dimension + composite + specific improvement suggestions.

- [ ] Completeness scorer
- [ ] Specificity scorer
- [ ] Clarity scorer
- [ ] Agent-awareness scorer
- [ ] Freshness scorer (cross-reference with actual codebase)
- [ ] Composite score with improvement suggestions
- [ ] Tests for D3

### D4. CLI Interface

Required:
- `agentmd/cli.py` — Typer-based CLI

Commands:
- `agentmd scan [path]` — Show analysis results (what was detected)
- `agentmd generate [path] --target claude|codex|cursor|copilot|all` — Generate context files
- `agentmd score [file]` — Score an existing context file
- `agentmd diff [path]` — Show what would change if regenerated (for existing context files)

Flags:
- `--output-dir DIR` — Where to write generated files (default: project root)
- `--dry-run` — Show what would be generated without writing
- `--format json|text` — Output format for scan/score
- `--verbose` — Include detection reasoning

- [ ] `scan` command
- [ ] `generate` command with all targets
- [ ] `score` command
- [ ] `diff` command
- [ ] Dry-run support
- [ ] JSON output support
- [ ] Tests for D4

### D5. Project Setup & Packaging

Required:
- `pyproject.toml` — proper Python packaging (uv/pip compatible)
- `README.md` — comprehensive, with examples and usage
- `.github/workflows/ci.yml` — GitHub Actions CI
- `LICENSE` — MIT

- [ ] pyproject.toml with proper metadata, entry points
- [ ] README with install, quick start, all commands, examples
- [ ] CI workflow (lint + test)
- [ ] LICENSE file
- [ ] Tests for D5 (meta: package installs and CLI entry point works)

## 4. Test Requirements

- [ ] Unit tests for each detector in D1
- [ ] Unit tests for each generator in D2
- [ ] Unit tests for each scorer dimension in D3
- [ ] Integration test: scan a sample project -> generate all targets -> score them
- [ ] Edge cases: empty project, monorepo, project with existing context files
- [ ] All tests runnable with `pytest tests/ -x`
- [ ] Minimum 80% code coverage

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected (new requirements discovered) -> STOP, report what's new
- All tests passing but deliverables remain -> continue to next deliverable
