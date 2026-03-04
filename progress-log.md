# Progress Log

## D1 - Project Analyzer (core)
- Status: Complete
- What was built:
  - Added `ProjectAnalysis` and related dataclasses in `agentmd/types.py`.
  - Implemented detector modules for language, package manager, framework, test runner, lint tools, and CI in `agentmd/detectors/`.
  - Implemented `ProjectAnalyzer` in `agentmd/analyzer.py` with:
    - Directory structure analysis and monorepo heuristics.
    - Git history summary (commit count, common extensions/directories/message prefixes).
    - Existing context file detection/parsing for `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, and `copilot-instructions.md`.
- Tests passing:
  - `python3 -m pytest tests/unit -q` (7 passed).
  - Coverage for each D1 detector plus analyzer-level behavior.
- Next:
  - D2 context file generators and tests.
- Blockers:
  - `uv run` currently panics in this sandbox (`system-configuration` NULL object panic). Using `python3 -m pytest` as execution fallback while keeping uv-compatible packaging.

## Blocker Report - 2026-03-01
- Status: STOPPED (contract stop condition triggered)
- Blocking issue:
  - Cannot write to `.git/` in this environment, so required deliverable commits are impossible.
  - Error: `Operation not permitted` when creating `.git/index.lock` and writing under `.git/objects`.
- Attempts made (3 consecutive):
  1. `git add ... && git commit ...` -> failed: cannot create `.git/index.lock`.
  2. `touch .git/index.lock` -> failed: operation not permitted.
  3. `touch .git/objects/.write_test` -> failed: operation not permitted.
- Impact:
  - Contract rule \"Commit after each completed deliverable\" cannot be satisfied.
  - Work cannot proceed to D2 while staying contract-compliant.
- Unblock needed:
  - Enable write access to `.git/` for this workspace, then resume from current D1 state.

## D1-v0.2 Complete — Swift/Xcode Detection — 2026-03-02

Built `agentmd/detectors/swift.py` for Swift/Xcode project detection:

**Detects:**
- Project files: `.xcodeproj`, `Package.swift` (SPM), `Podfile` (CocoaPods), `.xcworkspace`
- Frameworks (by scanning `.swift` source files): SwiftUI, UIKit, AppKit, Combine
- Linters: SwiftLint (`swiftlint.yml`, `.swiftlint.yml`), swift-format (`.swift-format`)
- CI: `xcodebuild` usage in any `.github/workflows/` YAML file

**Files changed:**
- `agentmd/detectors/swift.py` — new detector, `detect_swift_project(root, files) -> DetectorFindings`
- `agentmd/detectors/__init__.py` — registered `detect_swift_project`
- `agentmd/analyzer.py` — wired in `swift_findings`, passes `swift_components` to `ProjectAnalysis`, adds `"swift"` key to `detection_reasons`
- `agentmd/types.py` — added `swift_components: list[str]` field to `ProjectAnalysis` + `to_dict()`
- `tests/unit/test_swift_detector.py` — 15 tests: all project types, all frameworks, both linters, CI positive/negative, empty project, ordering guarantee

**Test results:** 114 passed (99 pre-existing + 15 new), 0 failures, 0.30s

**Commit:** 22795f9

---

## D2 Complete — 2026-03-02

Built the Context File Generator (D2):

**Files created:**
- `agentmd/generators/base.py` — BaseGenerator ABC with shared sections: project overview, commands, directory structure, conventions. Plus internal helpers for test/lint/install command inference.
- `agentmd/generators/claude.py` — ClaudeGenerator → CLAUDE.md with /compact, /review, /init hints; style guide; anti-patterns; agent-specific tips
- `agentmd/generators/codex.py` — CodexGenerator → AGENTS.md with sandbox awareness, apply_patch notes, approval gates checklist
- `agentmd/generators/cursor.py` — CursorGenerator → .cursorrules with Always/Never rule blocks, file patterns, context preferences
- `agentmd/generators/copilot.py` — CopilotGenerator → copilot-instructions.md with coding standards, test patterns, PR review checklist
- `agentmd/generators/__init__.py` — Updated with exports and GENERATOR_MAP
- `tests/unit/test_generators.py` — 41 tests covering all generators, edge cases, empty analysis

**Test results:** 51 passed (10 D1 + 41 D2), 0 failures, 0.21s

**Commit:** d752757

---

## D1-v0.3 Complete — 2026-03-03

- Status: Complete
- What was built:
  - Added [`agentmd/drift.py`] with deterministic drift detection against freshly generated context files.
  - Added section-level comparison reporting: `sections_added`, `sections_removed`, `sections_changed`, `sections_stale`, plus per-section stale details with diffs.
  - Added schema-backed JSON report payload (`agentmd.drift.report` v1.0.0).
  - Added GitHub Actions annotation formatter output (`--format github`).
  - Added `drift` subcommand to [`agentmd/cli.py`] with exit code behavior:
    - `0` when no drift is detected
    - `1` when drift is detected
- Tests passing:
  - `python3 -m pytest -q` (340 passed)
  - Added coverage:
    - `tests/unit/test_drift.py`
    - `tests/integration/test_drift_cli_integration.py`
    - `tests/unit/test_cli.py` (drift command behavior)
    - `tests/unit/test_cli_json.py` (drift JSON schema/behavior)
- Next:
  - D2 GitHub composite action + reusable workflow + D2 tests.
- Blockers:
  - None.

## Blocker Report - 2026-03-03 (v0.3 pass)
- Status: STOPPED (contract stop condition triggered)
- Blocking issue:
  - Cannot write to `.git/` in this environment, so required commit after D1 cannot be created.
  - Error: `Operation not permitted` while creating `.git/index.lock`.
- Attempts made (3 consecutive):
  1. `git add ... && git commit ...` -> failed: unable to create `.git/index.lock`.
  2. `git add agentmd/drift.py` -> failed: unable to create `.git/index.lock`.
  3. `touch .git/index.lock` -> failed: operation not permitted.
- Impact:
  - Contract rule "Commit after each completed deliverable" cannot be satisfied.
  - Per stop condition, work must pause before D2.
- Unblock needed:
  - Enable write access to `.git/` for this workspace, then resume from current D1 state.

## D2 Complete — 2026-03-04

- Status: Complete
- What was built:
  - Added root [`action.yml`] as a composite GitHub Action for drift checks.
  - Added configurable action inputs: `agent`, `fail-on-drift`, `comment`, and `python-version`.
  - Action installs from PyPI (`pip install agentmd-gen`), runs `agentmd drift --format markdown`, captures outputs, and supports optional PR commenting.
  - Integrated PR comment upsert flow using `peter-evans/find-comment@v3` + `peter-evans/create-or-update-comment@v4`.
  - Added reusable workflow example at `.github/workflows/agentmd-drift.yml` (`workflow_call`).
- Validation:
  - Parsed both YAML files with `python3 -c "import yaml; yaml.safe_load(...)"` successfully.
- Next:
  - D3 markdown formatter (`--format markdown`) and CLI integration.
- Blockers:
  - None.

## D3 Complete — 2026-03-04

- Status: Complete
- What was built:
  - Added new markdown formatter module at `agentmd/formatters.py` with PR-comment oriented drift output.
  - Added required markdown report structure:
    - Header: `## 🔍 agentmd Context Drift Report`
    - Summary line with fresh/drift state
    - Table: `Section | Status | Detail` with statuses `fresh`, `stale`, `missing`, `new`
    - Collapsible `<details>` blocks with full `diff` fences per drifted section
    - Footer: `Generated by [agentmd](https://github.com/mikiships/agentmd)`
  - Extended drift comparison metadata in `agentmd/drift.py`:
    - Added `sections_fresh`
    - Added `added` support in per-section detail status + diff generation
  - Wired CLI support for `agentmd drift --format markdown` in `agentmd/cli.py`.
- Tests added/updated:
  - Added `tests/unit/test_formatters.py` for markdown output behavior.
  - Updated drift/CLI unit tests for markdown format and JSON-format guardrails.
- Next:
  - D4 integration validation.
- Blockers:
  - None.

## D4 Complete — 2026-03-04

- Status: Complete
- What was built:
  - Expanded `tests/integration/test_drift_cli_integration.py` with explicit end-to-end coverage for:
    - stale context file -> drift exit code `1` + text output checks
    - fresh generated context -> drift exit code `0`
    - missing context file detection
    - drift JSON schema shape validation
    - markdown output structural validation
- Validation:
  - Ran targeted suite:
    - `python3 -m pytest -q tests/unit/test_drift.py tests/unit/test_formatters.py tests/unit/test_cli.py tests/unit/test_cli_json.py tests/integration/test_drift_cli_integration.py`
  - Result: passing.
- Next:
  - D5 docs + packaging/version updates + full test run.
- Blockers:
  - None.

## D5 Complete — 2026-03-04

- Status: Complete
- What was built:
  - Updated `README.md` with v0.3.0 highlights, drift command docs, and GitHub Action usage (copy-paste workflow YAML).
  - Added `CHANGELOG.md` with `0.3.0` release notes.
  - Bumped version to `0.3.0` in:
    - `pyproject.toml`
    - `agentmd/__init__.py`
- Packaging validation:
  - `python3 -m pip install -e .` failed due system-managed Python environment (PEP 668).
  - Verified editable install in an isolated local venv:
    - `python3 -m venv .tmp-venv && .tmp-venv/bin/python -m ensurepip --upgrade && .tmp-venv/bin/python -m pip install -e .`
    - Result: success (`agentmd-gen==0.3.0` installed editable).
- Full test run:
  - `python3 -m pytest -q` -> pass.
- Blockers:
  - None.

## Test Target Update — 2026-03-04

- Added additional formatter matrix coverage in `tests/unit/test_formatters_matrix.py`.
- `python3 -m pytest --collect-only` now reports **384 tests collected** (target 380+ met).
- `python3 -m pytest -q` remains passing.
