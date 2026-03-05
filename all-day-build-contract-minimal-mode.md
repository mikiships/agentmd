# All-Day Build Contract: Minimal Mode

Status: In Progress
Date: 2026-03-05
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add a `--minimal` flag to `agentmd generate` that produces lean, essential-only context files. Research (arXiv 2602.11988 "Evaluating AGENTS.md") found that verbose context files can reduce task success rates and increase costs by ~20%. Minimal mode generates only what agents can't infer themselves: build/test/lint commands, source/test directory roots, and project-specific conventions that deviate from language defaults. Everything else (tips, style guides, anti-patterns, verbose overviews) is omitted.

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

### D1. `--minimal` flag on `generate` command (CLI + plumbing)

Add `--minimal` / `-m` boolean option to the `generate` command in `agentmd/cli.py`. When set, pass `minimal=True` to each generator's `generate()` method (or constructor).

In `agentmd/generators/base.py`:
- Add `minimal: bool = False` parameter to `BaseGenerator.__init__`
- Add `_build_sections_minimal()` method that returns ONLY:
  1. A one-line header (no preamble paragraph)
  2. `_section_commands()` (build/test/lint commands — this is the highest-value section)
  3. A trimmed `_section_directory_structure()` showing ONLY source_directories and test_directories (no top_level_directories, no most-changed directories)
- Modify `generate()` to call `_build_sections_minimal()` when `self.minimal` is True

Each generator subclass (claude.py, codex.py, cursor.py, copilot.py) should:
- Accept and pass through the `minimal` flag
- In minimal mode, skip agent-specific tips/style/anti-pattern sections
- Include ONLY the minimal sections from base + any agent-critical one-liners (e.g., Claude's "use /compact" tip — but as a single line appended, not a full section)

Required files:
- `agentmd/cli.py`
- `agentmd/generators/base.py`
- `agentmd/generators/claude.py`
- `agentmd/generators/codex.py`
- `agentmd/generators/cursor.py`
- `agentmd/generators/copilot.py`

- [ ] `--minimal` flag added to CLI `generate` command
- [ ] `BaseGenerator` accepts `minimal` parameter
- [ ] `_build_sections_minimal()` implemented in base
- [ ] All 4 generators support minimal mode
- [ ] Tests for D1

### D2. Minimal mode in `diff` and `drift` commands

The `diff` and `drift` commands also generate context to compare against existing files. They need to respect `--minimal` too so users can check drift against minimal output.

- Add `--minimal` flag to `diff` command
- Add `--minimal` flag to `drift` command
- Pass through to generator constructors

Required files:
- `agentmd/cli.py`
- `agentmd/drift.py` (if generators are instantiated there)

- [ ] `--minimal` on `diff` command
- [ ] `--minimal` on `drift` command
- [ ] Tests for D2

### D3. JSON output includes minimal metadata

When `--json` is used with `--minimal`, the JSON output should include `"mode": "minimal"` in the result so consumers can distinguish.

- [ ] JSON output includes mode field
- [ ] Test for JSON + minimal combination

### D4. Score adjustments for minimal files

The scorer should not penalize minimal files for missing sections that were intentionally omitted. Add a `minimal` flag to the scorer that adjusts expectations:
- `completeness` dimension should expect fewer sections
- `agent_awareness` dimension should give full marks for minimal files (agent tips are omitted by design)

Required files:
- `agentmd/scorer.py`
- `agentmd/detectors/context_completeness.py`

- [ ] Scorer accepts `minimal` mode
- [ ] Completeness scoring adjusted for minimal
- [ ] Agent awareness scoring adjusted for minimal
- [ ] Tests for scoring minimal files

### D5. Documentation and version bump

- Update README.md with `--minimal` mode documentation and the research rationale (cite arXiv 2602.11988)
- Update CHANGELOG.md
- Bump version to 0.4.0 in pyproject.toml
- Update `--help` text if needed

- [ ] README updated with --minimal docs
- [ ] CHANGELOG entry
- [ ] Version bumped to 0.4.0
- [ ] All tests pass (target: 400+)

## 4. Test Requirements

- [ ] Unit tests for each generator in minimal mode (verify output has NO tips/style/anti-patterns sections)
- [ ] Unit test for minimal directory structure (only source + test dirs, no top-level)
- [ ] Integration test: `generate --minimal --json` round-trip
- [ ] Integration test: `diff --minimal` against existing full file
- [ ] Integration test: `drift --minimal`
- [ ] Edge case: minimal mode on empty project (no detected languages)
- [ ] Edge case: minimal mode on multi-language project
- [ ] Scorer tests for minimal files
- [ ] All existing tests (384) must still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected (new requirements discovered) -> STOP, report what's new
- All tests passing but deliverables remain -> continue to next deliverable

## 7. Research Context (for the agent)

The arXiv paper 2602.11988 ("Evaluating AGENTS.md") found:
- Context files can REDUCE task success rates when verbose
- Cost increases ~20% with verbose context
- Minimal > verbose for agent performance
- The most valuable information: exact commands to run (build, test, lint)
- Least valuable: generic tips, style guides, anti-patterns (agents already know these)

The `--minimal` mode codifies this finding: generate only what the agent can't infer.
