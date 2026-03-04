# Changelog

All notable changes to this project will be documented in this file.

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
