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
