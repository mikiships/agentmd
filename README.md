# agentmd

[![PyPI](https://img.shields.io/pypi/v/agentmd-gen)](https://pypi.org/project/agentmd-gen/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#install)
[![Tests](https://img.shields.io/badge/tests-483%20passing-brightgreen)](#)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](#license)

agentmd analyzes your codebase and generates optimized context files for AI coding agents. Point it at any Python, Swift/Xcode, Rust, Go, TypeScript, or multi-language project and it produces ready-to-use `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, or Copilot instruction files — scored and ranked so your agent starts with the best possible picture of your project.

## What's New in 0.5.0

- **`--tiered` mode** — generate a directory of context files instead of a single file. Based on the Codified Context paper ([arXiv 2602.20478](https://arxiv.org/abs/2602.20478)) which showed single-file manifests don't scale past ~1000 lines. Tiered mode automatically detects subsystem boundaries and generates a Tier 1 `CLAUDE.md` (always loaded) plus per-subsystem Tier 2 files in `.agents/`.
- **Subsystem detection** — automatically identifies subsystem boundaries from directory structure, package manifests, and source file distribution
- **Trigger table** — Tier 1 `CLAUDE.md` includes a table mapping directories to their context files so agents know which subsystem context to load

## Install

```bash
pip install agentmd-gen
```

## Usage

### scan — inspect a project

```bash
agentmd scan                   # scan current directory
agentmd scan ~/repos/myapp     # scan a specific path
agentmd scan --json            # output as JSON
```

Prints detected languages, frameworks, package managers, test runners, linters, CI systems, and existing context files.

### generate — create agent context files

```bash
agentmd generate                          # generate for all supported agents
agentmd generate --agent claude           # Claude Code (CLAUDE.md)
agentmd generate --agent codex            # OpenAI Codex (AGENTS.md)
agentmd generate --agent cursor           # Cursor (.cursorrules)
agentmd generate --agent copilot          # GitHub Copilot (.github/copilot-instructions.md)
agentmd generate --minimal                # lean, essential-only output (recommended)
agentmd generate -m --agent claude        # minimal mode for a single agent
agentmd generate --json                   # output generated content as JSON
agentmd generate --json --minimal         # JSON with "mode": "minimal" metadata
agentmd generate --tiered                 # tiered context (CLAUDE.md + .agents/)
agentmd generate --tiered --force         # overwrite existing tiered files
```

### score — evaluate existing context files

```bash
agentmd score                             # score all context files in cwd
agentmd score CLAUDE.md                   # score a specific file
agentmd score --json                      # output scores as JSON
```

Outputs a score (0–100) broken down by dimension.

**Example JSON output:**

```json
{
  "file": "CLAUDE.md",
  "total": 84,
  "dimensions": {
    "completeness": 18,
    "specificity": 17,
    "clarity": 16,
    "agent_awareness": 18,
    "freshness": 15
  }
}
```

### diff — compare context files

```bash
agentmd diff --agent claude               # diff current file vs freshly generated output
agentmd diff --minimal --agent claude     # diff against minimal-mode output
agentmd diff --json                       # output diff as JSON
```

### drift — detect context drift

```bash
agentmd drift                             # check all agent context files in cwd
agentmd drift --agent claude             # check only CLAUDE.md
agentmd drift --minimal --agent claude   # check drift against minimal-mode output
agentmd drift --json                     # machine-readable drift report
agentmd drift --format github            # GitHub workflow command annotations
agentmd drift --format markdown          # PR comment markdown report
```

Exit codes:

- `0` = context files are fresh
- `1` = drift detected (or missing context file)

## GitHub Action

Use the published action in your PR workflow:

```yaml
name: agentmd-drift

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  drift:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: mikiships/agentmd@v0.4.0
        with:
          agent: claude
          fail-on-drift: "true"
          comment: "true"
          python-version: "3.11"
```

For reusable workflow usage, see `.github/workflows/agentmd-drift.yml`.

## Minimal Mode

Research ([arXiv 2602.11988](https://arxiv.org/abs/2602.11988) "Evaluating AGENTS.md") found that verbose context files can **reduce** task success rates and increase costs by ~20%. The most valuable information is exact commands to run (build, test, lint). The least valuable: generic tips, style guides, and anti-patterns that agents already know.

`--minimal` generates only what the agent can't infer itself:

1. A one-line header
2. Build, test, and lint commands (highest-value section)
3. Source and test directory roots

Everything else is omitted. For Claude, a single `/compact` tip is appended.

```bash
agentmd generate --minimal               # recommended for most projects
agentmd generate --minimal --agent claude
agentmd diff --minimal                   # compare existing files against minimal output
agentmd drift --minimal                  # check drift against minimal baseline
```

## Tiered Mode

The Codified Context paper ([arXiv 2602.20478](https://arxiv.org/abs/2602.20478)) showed that single-file context manifests don't scale past ~1000 lines of context. They built a three-tier architecture manually for a 108k-line C# project across 283 sessions. `--tiered` automates that pattern.

`--tiered` detects subsystem boundaries in your project and generates:

```
project/
├── CLAUDE.md              # Tier 1: conventions, build/test/lint, trigger table (~30 lines)
└── .agents/
    ├── api.md             # Tier 2: per-subsystem context
    ├── database.md
    └── web.md
```

The Tier 1 `CLAUDE.md` includes a trigger table that maps directories to their context files:

```markdown
## Context Files (load when working in these areas)
| Directory | Context File |
|-----------|-------------|
| api/      | .agents/api.md |
| db/       | .agents/database.md |
| web/      | .agents/web.md |
```

Projects with fewer than 20 source files or 2000 lines are too small for tiered mode — use `generate` without `--tiered` instead.

```bash
agentmd generate --tiered                # detect subsystems and generate tiered context
agentmd generate --tiered --force        # overwrite existing files
agentmd generate --tiered --dry-run      # preview without writing
```

## Supported Agents

| Agent | Output file |
|-------|-------------|
| Claude Code | `CLAUDE.md` |
| OpenAI Codex | `AGENTS.md` |
| Cursor | `.cursorrules` |
| GitHub Copilot | `.github/copilot-instructions.md` |

## Supported Languages

| Language | Detection | Generators | What's detected |
|----------|-----------|------------|-----------------|
| **Python** | `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile` | All agents | Frameworks (Django, Flask, FastAPI, Starlette, Litestar), pytest, ruff/flake8/mypy, GitHub Actions |
| **Swift/Xcode** | `.xcodeproj`, `Package.swift` | All agents | SwiftUI/UIKit/AppKit targets, SwiftLint, xcodebuild CI, Swift Package Manager |
| **Rust** | `Cargo.toml` | All agents | tokio, actix-web, serde, axum, clap, and other common crates; clippy/rustfmt, cargo-based CI |
| **Go** | `go.mod` | All agents | gin, echo, fiber, cobra, and other common modules; golangci-lint, go test CI |

## How Scoring Works

Each context file is evaluated on five dimensions (total: 100 points):

| Dimension | Points | What it measures |
|-----------|--------|------------------|
| **Completeness** | 20 | All key project facts present (languages, stack, test commands) |
| **Specificity** | 20 | Concrete details vs. generic boilerplate |
| **Clarity** | 20 | Readable structure, scannable headings, no walls of text |
| **Agent-awareness** | 20 | Instructions tailored to the target agent's strengths and quirks |
| **Freshness** | 20 | Content reflects the current state of the codebase (no stale info) |

**Note on freshness scoring (v0.2.0):** Earlier versions could false-positive on freshness — penalizing files that referenced current stable versions or recent stable APIs. This has been corrected. The freshness dimension now only flags genuinely stale references (deprecated packages, EOL runtime versions, removed APIs).

Run `agentmd score` after generating to see where your files land and what to improve.

## Part of the Agent Toolkit

agentmd is one of three tools for AI coding agent quality:

- **[coderace](https://github.com/mikiships/coderace)** — Race coding agents against each other on real tasks. Automated, reproducible, scored comparisons.
- **[agentmd](https://github.com/mikiships/agentmd)** — Generate and score context files for AI coding agents.
- **[agentlint](https://github.com/mikiships/agentlint)** — Lint AI agent git diffs for risky patterns. Static analysis, no LLM required.

Measure (coderace) → Optimize (agentmd) → Guard (agentlint).

## Contributing

1. Fork the repo and create a branch
2. `pip install -e ".[dev]"` to get dev dependencies
3. Write tests in `tests/unit/`
4. `pytest tests/unit -q` must pass
5. Open a PR — CI runs on Python 3.10–3.13

## License

MIT © 2026 mikiships
