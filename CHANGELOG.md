# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2026-03-05

### Added

- Added `--minimal` / `-m` flag to `generate` command for lean, essential-only context files.
  - Produces only: one-line header, build/test/lint commands, source + test directory roots.
  - Skips: tips, style guides, anti-patterns, verbose overviews, conventions.
  - Claude generator appends a single `/compact` tip in minimal mode.
  - Research rationale: arXiv 2602.11988 "Evaluating AGENTS.md" found verbose context reduces agent performance.
- Added `--minimal` flag to `diff` command for comparing against minimal-mode output.
- Added `--minimal` flag to `drift` command for checking drift against minimal baseline.
- Added `"mode": "minimal"` field in JSON output when `--json --minimal` are combined on `generate`.
- Added `minimal` parameter to scorer — completeness expects fewer sections, agent awareness gives full marks.
- Added 58 new tests for minimal mode across generators, CLI, JSON, diff, drift, and scorer.

### Changed

- Bumped package version to `0.4.0`.
- Updated README with minimal mode documentation, research rationale, and usage examples.

## [0.3.0] - 2026-03-04

### Added

- Added `drift` markdown formatter (`agentmd drift --format markdown`) with:
  - `## 🔍 agentmd Context Drift Report` header
  - Summary line for fresh vs drifted state
  - Section-level status table (`fresh`, `stale`, `missing`, `new`)
  - Collapsible `<details>` blocks containing full section diffs
  - Footer linking back to the project repository
- Added root `action.yml` composite GitHub Action to:
  - Install `agentmd-gen` from PyPI
  - Run `agentmd drift`
  - Optionally post/update PR comments via `peter-evans/create-or-update-comment@v4`
  - Optionally fail CI when drift is detected
- Added reusable workflow example at `.github/workflows/agentmd-drift.yml`.
- Added integration tests for stale, fresh, missing-file, JSON schema, and markdown structure drift flows.
- Added unit coverage for markdown formatter rendering behavior.

### Changed

- Extended drift section comparison metadata to include `sections_fresh` and per-section `added` detail diffs.
- Updated `drift --format` options to support `text`, `github`, and `markdown`.
- Updated README with drift command docs and GitHub Action usage.
- Bumped package version metadata to `0.3.0`.

## [0.2.0] - 2026-03-02

### Added

- Multi-language detection and generation for Python, Swift/Xcode, Rust, and Go projects.
- `--json` output support across CLI commands for structured automation.

### Fixed

- Reduced false positives in context freshness scoring.
