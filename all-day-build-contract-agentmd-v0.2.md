# All-Day Build Contract: agentmd v0.2.0 — Multi-Language & Quality

Status: Ready to Spawn
Date: 2026-03-02
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Expand agentmd from Python/TypeScript-only to truly universal language support: Swift/Xcode, Rust, Go. Fix false positives in the scorer. Add JSON output for all commands. This positions agentmd as the universal context engineering tool right as Xcode 26.3 brings millions of Apple developers into agentic coding.

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

### D1. Swift/Xcode Project Detection

Detect Swift projects: .xcodeproj, Package.swift (SPM), Podfile (CocoaPods), .xcworkspace. Detect frameworks: SwiftUI, UIKit, AppKit, Combine. Detect Xcode CI (xcodebuild in CI configs). Detect linters: SwiftLint, swift-format.

Required:
- `agentmd/detectors/swift.py` (new)
- Update `agentmd/detectors/__init__.py` to register
- Update `agentmd/analyzer.py` if needed

- [ ] Detect .xcodeproj, Package.swift, Podfile
- [ ] Detect SwiftUI/UIKit/AppKit/Combine frameworks
- [ ] Detect SwiftLint, swift-format
- [ ] Detect Xcode CI (xcodebuild in workflow files)
- [ ] Tests for D1 (at least 8 tests)

### D2. Rust Project Detection

Detect Cargo.toml, workspace members, edition. Detect clippy, rustfmt. Detect common frameworks: tokio, actix, axum, serde.

Required:
- `agentmd/detectors/rust.py` (new)

- [ ] Detect Cargo.toml (single crate + workspace)
- [ ] Detect clippy, rustfmt config
- [ ] Detect tokio/actix/axum/serde
- [ ] Tests for D2 (at least 6 tests)

### D3. Go Project Detection

Detect go.mod, go.sum. Detect golangci-lint, gofmt. Detect common frameworks: gin, echo, fiber, cobra.

Required:
- `agentmd/detectors/go.py` (new)

- [ ] Detect go.mod/go.sum
- [ ] Detect golangci-lint, staticcheck
- [ ] Detect gin/echo/fiber/cobra
- [ ] Tests for D3 (at least 6 tests)

### D4. Generator Updates for New Languages

Update all 4 generators (Claude, Codex, Cursor, Copilot) to produce language-appropriate context for Swift, Rust, Go projects. Include proper build/test/lint commands for each ecosystem.

- [ ] Swift: xcodebuild, swift test, swiftlint commands in generated files
- [ ] Rust: cargo build, cargo test, cargo clippy commands
- [ ] Go: go build, go test, golangci-lint commands
- [ ] Mixed-language projects handled correctly
- [ ] Tests for D4 (at least 8 tests covering each language x each generator)

### D5. Scorer Improvements

Fix false positives: version strings (e.g., "1.1.6") should not be flagged as stale file references. Improve completeness detection to recognize build/test commands in various formats.

- [ ] Version string false positive fixed
- [ ] Build/test command detection improved (recognize pytest, cargo test, go test, xcodebuild test, etc.)
- [ ] Tests for D5 (at least 4 tests)

### D6. JSON Output for All Commands

Add `--json` flag to scan, score, generate (dry-run), and diff commands.

- [ ] `agentmd scan --json` outputs structured project analysis
- [ ] `agentmd score --json` outputs structured scores
- [ ] `agentmd generate --dry-run --json` outputs generated content as JSON
- [ ] Tests for D6 (at least 4 tests)

### D7. README & Version Bump

- [ ] README updated with Swift/Rust/Go examples
- [ ] Version bumped to 0.2.0
- [ ] All existing tests still pass
- [ ] New test count: 130+ total

## 4. Test Requirements

- [ ] Unit tests for each new detector (Swift, Rust, Go)
- [ ] Unit tests for generator updates
- [ ] Unit tests for scorer improvements
- [ ] Unit tests for JSON output
- [ ] All 99 existing tests must still pass
- [ ] Total: 130+ passing

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected -> STOP, report what's new
