"""Language detection heuristics."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from agentmd.types import DetectorFindings

LANGUAGE_EXTENSIONS: dict[str, set[str]] = {
    "Python": {".py"},
    "TypeScript/JavaScript": {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"},
    "Rust": {".rs"},
    "Go": {".go"},
    "Ruby": {".rb"},
    "Java": {".java"},
    "C#": {".cs"},
    "Swift": {".swift"},
}

SPECIAL_FILES: dict[str, set[str]] = {
    "Ruby": {"Gemfile"},
    "Go": {"go.mod"},
    "Rust": {"Cargo.toml"},
}


def detect_languages(root: Path, files: list[Path]) -> DetectorFindings:
    """Detect primary languages from file extensions and known manifest files."""
    extension_counts: Counter[str] = Counter()
    evidence: dict[str, list[str]] = {}

    for relative in files:
        extension = relative.suffix.lower()
        for language, extensions in LANGUAGE_EXTENSIONS.items():
            if extension in extensions:
                extension_counts[language] += 1
                evidence.setdefault(language, []).append(str(relative))

        for language, manifest_files in SPECIAL_FILES.items():
            if relative.name in manifest_files or str(relative) in manifest_files:
                extension_counts[language] += 1
                evidence.setdefault(language, []).append(str(relative))

    languages = sorted(extension_counts, key=lambda item: (-extension_counts[item], item))
    # Keep only evidence snippets used for reasoning output.
    trimmed_evidence = {k: sorted(set(v))[:5] for k, v in evidence.items() if k in languages}
    return DetectorFindings(values=languages, evidence=trimmed_evidence)
