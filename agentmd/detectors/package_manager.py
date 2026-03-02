"""Package manager detection heuristics."""

from __future__ import annotations

from pathlib import Path

from agentmd.detectors.common import read_text
from agentmd.types import DetectorFindings

MANIFEST_FILE_RULES: dict[str, set[str]] = {
    "uv": {"uv.lock"},
    "poetry": {"poetry.lock"},
    "npm": {"package-lock.json"},
    "pnpm": {"pnpm-lock.yaml"},
    "yarn": {"yarn.lock"},
    "cargo": {"Cargo.toml", "Cargo.lock"},
    "go mod": {"go.mod"},
    "bundler": {"Gemfile", "Gemfile.lock"},
    "maven": {"pom.xml"},
    "gradle": {"build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"},
}


def detect_package_managers(root: Path, files: list[Path]) -> DetectorFindings:
    """Detect package managers from lockfiles/manifests and config entries."""
    detected: set[str] = set()
    evidence: dict[str, list[str]] = {}

    file_names = {file_path.name for file_path in files}
    file_paths = {str(file_path) for file_path in files}

    for manager, manifest_files in MANIFEST_FILE_RULES.items():
        for manifest_file in manifest_files:
            if manifest_file in file_names or manifest_file in file_paths:
                detected.add(manager)
                evidence.setdefault(manager, []).append(manifest_file)

    if "pyproject.toml" in file_names:
        pyproject_content = read_text(root / "pyproject.toml")
        if "[tool.uv" in pyproject_content or "uv.lock" in file_names:
            detected.add("uv")
            evidence.setdefault("uv", []).append("pyproject.toml")
        if "[tool.poetry" in pyproject_content or "poetry.lock" in file_names:
            detected.add("poetry")
            evidence.setdefault("poetry", []).append("pyproject.toml")
        if "[project]" in pyproject_content and "poetry" not in detected:
            detected.add("pip")
            evidence.setdefault("pip", []).append("pyproject.toml")

    if "requirements.txt" in file_names or "requirements-dev.txt" in file_names:
        detected.add("pip")
        evidence.setdefault("pip", []).append("requirements.txt")

    if "setup.py" in file_names or "setup.cfg" in file_names:
        detected.add("pip")
        evidence.setdefault("pip", []).append("setup.py/setup.cfg")

    values = sorted(detected)
    trimmed_evidence = {k: sorted(set(v))[:5] for k, v in evidence.items() if k in detected}
    return DetectorFindings(values=values, evidence=trimmed_evidence)
