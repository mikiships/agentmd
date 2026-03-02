"""Shared helpers for detectors."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "target",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
}


def collect_project_files(root: Path) -> list[Path]:
    """Collect project files while skipping common generated directories."""
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir() and path.name in IGNORED_DIR_NAMES:
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_DIR_NAMES for part in relative.parts):
            continue
        files.append(relative)
    return sorted(files)


def read_text(path: Path, max_chars: int = 5000) -> str:
    """Read text from file safely."""
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    return content[:max_chars]


def top_ranked(counter: Counter[str], limit: int = 5) -> list[str]:
    """Sort by count desc, then value asc for deterministic output."""
    ordered = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return [value for value, _ in ordered[:limit]]


def normalize_item_values(values: set[str]) -> list[str]:
    """Return stable sorted detector values."""
    return sorted(values)
