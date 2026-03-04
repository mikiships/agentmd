# All-Day Build Contract: agentmd v0.3.0 — GitHub Action + CI Integration

Status: In Progress
Date: 2026-03-03
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build a GitHub Action that runs agentmd on pull requests, compares the generated context files against what's already in the repo, and posts a PR comment showing drift. This is the "context freshness" CI integration: every PR gets a comment showing whether CLAUDE.md (or equivalent) is still accurate.

Secondary: add a `watch` command to the CLI that can detect drift between existing context files and current codebase state, outputting a machine-readable report for CI.

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

### D1. `agentmd drift` CLI command (core)

Add a `drift` command that:
- Runs a fresh `generate` against the codebase
- Compares the generated output against existing context file(s) in the repo
- Outputs a structured drift report: sections added, removed, changed, stale
- Supports `--json` output for machine consumption
- Supports `--format github` that outputs GitHub Actions annotation format
- Exit code: 0 = no drift, 1 = drift detected (for CI fail gates)

Required files:
- `agentmd/drift.py` (new)
- `agentmd/cli.py` (add drift subcommand)

- [ ] `drift` command implementation
- [ ] JSON output schema
- [ ] GitHub annotations format output
- [ ] Exit code behavior (0 = clean, 1 = drift)
- [ ] Tests for D1 (unit + integration)

### D2. GitHub Action definition

Create `.github/actions/agentmd-drift/action.yml` (composite action) that:
- Installs agentmd from PyPI
- Runs `agentmd drift` against the repo
- Posts a PR comment with the drift report (create or update, don't spam)
- Configurable inputs: `agent` (which context file format), `fail-on-drift` (boolean), `comment` (boolean)
- Uses `peter-evans/create-or-update-comment` or equivalent for PR comments
- The action.yml should be publishable to GitHub Marketplace

Also create a reusable workflow example at `.github/workflows/agentmd-drift.yml`.

Required files:
- `action.yml` (root level, for Marketplace)
- `.github/workflows/agentmd-drift.yml` (example workflow)

- [ ] action.yml with inputs/outputs
- [ ] Composite action steps (install, run drift, comment)
- [ ] PR comment formatting (markdown table with drift summary)
- [ ] Example workflow file
- [ ] Tests for D2 (action.yml validation, dry-run test)

### D3. PR Comment Formatter

Build a formatter that turns drift output into a clean PR comment:
- Header with agentmd logo/badge
- Summary line: "✅ Context files are fresh" or "⚠️ 3 sections drifted"
- Table: section name, status (fresh/stale/missing/new), details
- Collapsible details section with full diff for each drifted section
- Footer with link to agentmd repo

Required files:
- `agentmd/formatters.py` (new)

- [ ] PR comment markdown formatter
- [ ] Collapsible diff sections
- [ ] Summary line generation
- [ ] Tests for D3

### D4. Integration test suite

- [ ] End-to-end test: create a temp repo with a stale CLAUDE.md, run `agentmd drift`, verify output
- [ ] Test: fresh context file produces exit 0
- [ ] Test: missing context file detected
- [ ] Test: JSON output validates against schema
- [ ] Test: GitHub annotations format is valid

### D5. Docs + Packaging

- [ ] Update README.md with `drift` command docs
- [ ] Add GitHub Action usage section to README
- [ ] Update CHANGELOG.md
- [ ] Bump version to 0.3.0 in pyproject.toml
- [ ] Update pyproject.toml keywords/classifiers if needed

## 4. Test Requirements

- [ ] Unit tests for drift detection logic
- [ ] Unit tests for PR comment formatter
- [ ] Integration test for full drift pipeline
- [ ] All existing tests (323) must still pass
- [ ] New test count target: 360+

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected (new requirements discovered) -> STOP, report what's new
- All tests passing but deliverables remain -> continue to next deliverable
