"""Test runner detection heuristics."""

from __future__ import annotations

import json
from pathlib import Path

from agentmd.detectors.common import read_text
from agentmd.types import DetectorFindings

RUNNER_ORDER = ["pytest", "jest", "vitest", "cargo test", "go test", "rspec", "JUnit"]


def _package_dependencies(root: Path) -> set[str]:
    package_json = root / "package.json"
    if not package_json.exists():
        return set()
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return set()
    dependencies: set[str] = set()
    for section in ("dependencies", "devDependencies"):
        values = data.get(section, {})
        if isinstance(values, dict):
            dependencies.update(values.keys())
    return dependencies


def detect_test_runners(root: Path, files: list[Path]) -> DetectorFindings:
    """Detect test tools from config files and source patterns."""
    detected: set[str] = set()
    evidence: dict[str, list[str]] = {}

    file_names = {path.name for path in files}
    file_paths = {str(path) for path in files}
    deps = _package_dependencies(root)

    if "pytest.ini" in file_names or ".pytest.ini" in file_names:
        detected.add("pytest")
        evidence.setdefault("pytest", []).append("pytest.ini")

    pyproject = root / "pyproject.toml"
    if pyproject.exists() and "pytest" in read_text(pyproject).lower():
        detected.add("pytest")
        evidence.setdefault("pytest", []).append("pyproject.toml")

    if any(path.endswith("_test.py") or path.startswith("tests/") for path in file_paths):
        detected.add("pytest")
        evidence.setdefault("pytest", []).append("tests/ or *_test.py")

    if "jest" in deps or "jest.config.js" in file_names or "jest.config.ts" in file_names:
        detected.add("jest")
        evidence.setdefault("jest", []).append("package.json/jest config")

    if "vitest" in deps or "vitest.config.ts" in file_names or "vitest.config.js" in file_names:
        detected.add("vitest")
        evidence.setdefault("vitest", []).append("package.json/vitest config")

    if "Cargo.toml" in file_names:
        detected.add("cargo test")
        evidence.setdefault("cargo test", []).append("Cargo.toml")

    if any(path.name.endswith("_test.go") for path in files) or "go.mod" in file_names:
        detected.add("go test")
        evidence.setdefault("go test", []).append("go.mod or *_test.go")

    if "spec" in {path.parts[0] for path in files if path.parts} or ".rspec" in file_names:
        detected.add("rspec")
        evidence.setdefault("rspec", []).append("spec/ or .rspec")

    if "pom.xml" in file_names or "build.gradle" in file_names or "build.gradle.kts" in file_names:
        java_test_file = next((path for path in files if path.suffix == ".java" and "test" in str(path).lower()), None)
        if java_test_file is not None:
            detected.add("JUnit")
            evidence.setdefault("JUnit", []).append(str(java_test_file))

    values = [runner for runner in RUNNER_ORDER if runner in detected]
    trimmed_evidence = {k: sorted(set(v))[:5] for k, v in evidence.items() if k in detected}
    return DetectorFindings(values=values, evidence=trimmed_evidence)
