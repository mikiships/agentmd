"""Dimension checkers for context file scoring."""

from __future__ import annotations

import re
from pathlib import Path


def _lines(content: str) -> list[str]:
    return content.splitlines()


def _headings(content: str) -> list[str]:
    return [ln for ln in _lines(content) if ln.startswith("#")]


def _code_blocks(content: str) -> list[str]:
    return re.findall(r"```[^\n]*\n(.*?)```", content, re.DOTALL)


def _has_pattern(content: str, patterns: list[str]) -> bool:
    lower = content.lower()
    return any(p in lower for p in patterns)


# ---------------------------------------------------------------------------
# Completeness (30%)
# ---------------------------------------------------------------------------

BUILD_PATTERNS = [
    "build", "make ", "cmake", "cargo build", "go build", "npm run build",
    "pnpm build", "yarn build", "mvn ", "gradle",
]
TEST_PATTERNS = [
    "pytest", "jest", "vitest", "go test", "cargo test", "rspec",
    "npm test", "pnpm test", "yarn test", "unittest",
]
LINT_PATTERNS = [
    "ruff", "eslint", "pylint", "flake8", "mypy", "prettier",
    "clippy", "golangci-lint", "rubocop", "lint",
]
STRUCTURE_PATTERNS = [
    "src/", "tests/", "lib/", "cmd/", "pkg/", "app/", "docs/",
    "directory", "structure", "layout",
]
CONVENTIONS_PATTERNS = [
    "convention", "pattern", "style", "naming", "format",
    "import", "module", "package",
]


def score_completeness(content: str) -> tuple[float, list[str]]:
    """Return (score 0-100, suggestions)."""
    suggestions: list[str] = []
    sub_scores: dict[str, float] = {}

    checks = [
        ("build_commands", BUILD_PATTERNS, "Add build commands (e.g., `make`, `cargo build`)"),
        ("test_commands", TEST_PATTERNS, "Add test commands (e.g., `pytest`, `jest`)"),
        ("lint_commands", LINT_PATTERNS, "Add lint/format commands (e.g., `ruff check .`)"),
        ("structure", STRUCTURE_PATTERNS, "Describe project directory structure"),
        ("conventions", CONVENTIONS_PATTERNS, "Document code conventions and patterns"),
    ]

    for key, patterns, suggestion in checks:
        found = _has_pattern(content, patterns)
        sub_scores[key] = 100.0 if found else 0.0
        if not found:
            suggestions.append(suggestion)

    score = sum(sub_scores.values()) / len(sub_scores)
    return score, suggestions


# ---------------------------------------------------------------------------
# Specificity (25%)
# ---------------------------------------------------------------------------

def score_specificity(content: str) -> tuple[float, list[str]]:
    """Return (score 0-100, suggestions)."""
    suggestions: list[str] = []
    points = 0
    total = 4

    if re.search(r"[\w/]+\.\w{1,6}", content):
        points += 1
    else:
        suggestions.append("Reference actual file paths (e.g., `src/main.py`)")

    blocks = _code_blocks(content)
    if blocks:
        points += 1
    else:
        suggestions.append("Include code blocks with actual commands")

    if re.search(r"`[^`]+`", content):
        points += 1
    else:
        suggestions.append("Use inline code formatting for commands and paths")

    concrete = re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b", content)
    cmd_like = re.findall(r"`[a-z][\w\-]+(?: [\w\-\.]+)*`", content)
    if concrete or cmd_like:
        points += 1
    else:
        suggestions.append("Include concrete tool names and commands instead of generic advice")

    score = (points / total) * 100
    return score, suggestions


# ---------------------------------------------------------------------------
# Clarity (20%)
# ---------------------------------------------------------------------------

def score_clarity(content: str) -> tuple[float, list[str]]:
    """Return (score 0-100, suggestions)."""
    suggestions: list[str] = []
    points = 0
    total = 4

    lines = _lines(content)
    headings = _headings(content)

    if headings:
        points += 1
    else:
        suggestions.append("Add markdown headings to structure the document")

    if len(headings) >= 3:
        points += 1
    else:
        suggestions.append("Break content into at least 3 named sections")

    wall = False
    consecutive = 0
    for ln in lines:
        if ln.strip():
            consecutive += 1
            if consecutive > 15:
                wall = True
                break
        else:
            consecutive = 0
    if not wall:
        points += 1
    else:
        suggestions.append("Break up long paragraphs — avoid walls of text")

    if re.search(r"^[ \t]*[-*] ", content, re.MULTILINE) or _code_blocks(content):
        points += 1
    else:
        suggestions.append("Use bullet lists or code blocks to make content scannable")

    score = (points / total) * 100
    return score, suggestions


# ---------------------------------------------------------------------------
# Agent-Awareness (15%)
# ---------------------------------------------------------------------------

AGENT_PATTERNS = [
    "/init", "/review", "/test", "claude code", "claude.md", "claude-code",
    "codex", "agents.md",
    ".cursorrules", "cursor",
    "copilot", "copilot-instructions",
    "agent", "mcp", "tool call", "function call", "system prompt",
    "sandbox", "bash tool", "file edit",
]


def score_agent_awareness(content: str) -> tuple[float, list[str]]:
    """Return (score 0-100, suggestions)."""
    lower = content.lower()
    matches = [p for p in AGENT_PATTERNS if p in lower]

    if not matches:
        return 0.0, [
            "Add agent-specific instructions (e.g., Claude Code slash commands, Codex sandbox notes)"
        ]

    score = min(100.0, len(matches) * 20.0)
    suggestions: list[str] = []
    if score < 60:
        suggestions.append("Expand agent-specific sections (mention relevant slash commands or sandbox behavior)")
    return score, suggestions


# ---------------------------------------------------------------------------
# Freshness (10%)
# ---------------------------------------------------------------------------

def score_freshness(content: str, project_root: str | None = None) -> tuple[float, list[str]]:
    """Return (score 0-100, suggestions).

    Cross-references file paths mentioned in the content against the actual
    project root (if provided).
    """
    suggestions: list[str] = []

    mentioned_paths = re.findall(r"[`'\"]?([\w./\-]+\.\w{1,6})[`'\"]?", content)
    if not mentioned_paths:
        return 50.0, ["Mention specific project files so freshness can be verified"]

    if not project_root:
        return 50.0, []

    root = Path(project_root)
    missing: list[str] = []
    checked = 0
    for p in mentioned_paths:
        if p.startswith("http") or p.count(".") > 3:
            continue
        checked += 1
        if not (root / p).exists():
            missing.append(p)

    if checked == 0:
        return 50.0, []

    stale_ratio = len(missing) / checked
    score = max(0.0, (1 - stale_ratio) * 100)

    if stale_ratio > 0.3:
        suggestions.append(
            f"Update stale file references: {', '.join(missing[:5])}"
        )

    return score, suggestions
