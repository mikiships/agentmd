# agentmd

agentmd analyzes your codebase and generates optimized context files for AI coding agents. Point it at any Python, TypeScript, or multi-language project and it produces ready-to-use `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, or Copilot instruction files — scored and ranked so your agent starts with the best possible picture of your project.

## Install

```bash
pip install agentmd
```

## Usage

### scan — inspect a project

```bash
agentmd scan                   # scan current directory
agentmd scan ~/repos/myapp     # scan a specific path
```

Prints detected languages, frameworks, package managers, test runners, linters, CI systems, and existing context files.

### generate — create agent context files

```bash
agentmd generate                          # generate for all supported agents
agentmd generate --agent claude           # Claude Code (CLAUDE.md)
agentmd generate --agent codex            # OpenAI Codex (AGENTS.md)
agentmd generate --agent cursor           # Cursor (.cursorrules)
agentmd generate --agent copilot          # GitHub Copilot (.github/copilot-instructions.md)
agentmd generate --out ./docs/            # write to a custom directory
```

### score — evaluate existing context files

```bash
agentmd score                             # score all context files in cwd
agentmd score CLAUDE.md                   # score a specific file
```

Outputs a score (0–100) broken down by dimension.

### diff — compare context files

```bash
agentmd diff CLAUDE.md AGENTS.md          # side-by-side diff of two context files
agentmd diff --agent claude               # diff current file vs freshly generated output
```

## Supported Agents

| Agent | Output file |
|-------|-------------|
| Claude Code | `CLAUDE.md` |
| OpenAI Codex | `AGENTS.md` |
| Cursor | `.cursorrules` |
| GitHub Copilot | `.github/copilot-instructions.md` |

## How Scoring Works

Each context file is evaluated on five dimensions (total: 100 points):

| Dimension | Points | What it measures |
|-----------|--------|------------------|
| **Completeness** | 20 | All key project facts present (languages, stack, test commands) |
| **Specificity** | 20 | Concrete details vs. generic boilerplate |
| **Clarity** | 20 | Readable structure, scannable headings, no walls of text |
| **Agent-awareness** | 20 | Instructions tailored to the target agent's strengths and quirks |
| **Freshness** | 20 | Content reflects the current state of the codebase (no stale info) |

Run `agentmd score` after generating to see where your files land and what to improve.

## Contributing

1. Fork the repo and create a branch
2. `pip install -e ".[dev]"` to get dev dependencies
3. Write tests in `tests/unit/`
4. `pytest tests/unit -q` must pass
5. Open a PR — CI runs on Python 3.10–3.13

## License

MIT © 2026 mikiships
