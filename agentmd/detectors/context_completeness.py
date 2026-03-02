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

    # Match file paths: must start with a letter/underscore or contain /
    # Exclude version strings like "1.0.0", "3.10", etc.
    if re.search(r"(?:[a-zA-Z_][\w\-]*/|[a-zA-Z_][\w\-]+\.(?![\d]+(?:\b|$))[a-zA-Z]\w{0,5})", content):
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

# Patterns that look like paths but are NOT real filesystem paths — skip them.
_VERSION_RE = re.compile(
    r"""
    ^
    (?:
        v?\d+\.\d+(?:\.\d+)*(?:[-+][\w.]+)?   # semver: 1.2.3, v1.0.0, 1.0.0-rc1
      | [><=!^~]+\d[\d.]*                       # range: >=3.10, ^2.0, ~1.5
      | \d+\.\d+(?:\.\d+)*                      # bare numeric: 3.10, 12.0.1
    )
    $
    """,
    re.VERBOSE,
)
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_EMAIL_RE = re.compile(r"^[\w.+-]+@[\w.-]+\.\w+$")
_BARE_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)*$")

# Only treat a string as a candidate file path if it has a directory separator
# or an extension that doesn't look purely numeric.
_PLAUSIBLE_PATH_RE = re.compile(
    r"""
    (?:
        [./]          # contains / or starts with ./
      | \.\w{1,6}$   # ends with an extension
    )
    """,
    re.VERBOSE,
)

_NUMERIC_EXT_RE = re.compile(r"\.\d+$")


def _is_path_candidate(s: str) -> bool:
    """Return True only if *s* looks like an actual file/directory path."""
    if _URL_RE.search(s):
        return False
    if _EMAIL_RE.match(s):
        return False
    if _BARE_NUMBER_RE.match(s):
        return False
    if _VERSION_RE.match(s):
        return False
    # Must contain / or have a non-numeric extension
    if "/" not in s and not re.search(r"\.[a-zA-Z]\w{0,5}$", s):
        return False
    # Extension must not be purely digits (e.g., "3.10" has ext "10")
    if _NUMERIC_EXT_RE.search(s):
        return False
    return True


def _strip_urls(content: str) -> str:
    """Remove URLs from content so their path-like sub-strings aren't extracted."""
    return re.sub(r"https?://\S+", "", content, flags=re.IGNORECASE)


def score_freshness(content: str, project_root: str | None = None) -> tuple[float, list[str]]:
    """Return (score 0-100, suggestions).

    Cross-references file paths mentioned in the content against the actual
    project root (if provided). Version strings, URLs, email addresses, and
    other non-path tokens are filtered out before filesystem checks to avoid
    false positives.
    """
    suggestions: list[str] = []

    # Strip URLs first so sub-paths inside them (e.g., "re.html" in a URL) are
    # not mistakenly extracted as local file references.
    stripped = _strip_urls(content)

    raw_paths = re.findall(r"[`'\"]?([\w./\-]+\.\w{1,8})[`'\"]?", stripped)
    # Also catch paths with leading ./ or explicit dir prefix
    raw_paths += re.findall(r"[`'\"]?((?:\./|[\w\-]+/)[\w./\-]+)[`'\"]?", stripped)

    mentioned_paths = [p for p in dict.fromkeys(raw_paths) if _is_path_candidate(p)]

    if not mentioned_paths:
        return 50.0, ["Mention specific project files so freshness can be verified"]

    if not project_root:
        return 50.0, []

    root = Path(project_root)
    missing: list[str] = []
    checked = 0
    for p in mentioned_paths:
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
