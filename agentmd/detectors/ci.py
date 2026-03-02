"""CI system detection heuristics."""

from __future__ import annotations

from pathlib import Path

from agentmd.types import DetectorFindings

CI_ORDER = ["GitHub Actions", "GitLab CI"]


def detect_ci_systems(root: Path, files: list[Path]) -> DetectorFindings:
    """Detect CI providers from canonical config paths."""
    detected: set[str] = set()
    evidence: dict[str, list[str]] = {}

    file_paths = {str(path) for path in files}
    if any(path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")) for path in file_paths):
        detected.add("GitHub Actions")
        evidence.setdefault("GitHub Actions", []).append(".github/workflows/*.yml")

    if ".gitlab-ci.yml" in file_paths:
        detected.add("GitLab CI")
        evidence.setdefault("GitLab CI", []).append(".gitlab-ci.yml")

    values = [provider for provider in CI_ORDER if provider in detected]
    trimmed_evidence = {k: sorted(set(v))[:5] for k, v in evidence.items() if k in detected}
    return DetectorFindings(values=values, evidence=trimmed_evidence)
