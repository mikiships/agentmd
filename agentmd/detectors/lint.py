"""Lint/format tool detection heuristics."""

from __future__ import annotations

import json
from pathlib import Path

from agentmd.detectors.common import read_text
from agentmd.types import DetectorFindings

LINTER_ORDER = ["ruff", "eslint", "prettier", "clippy", "golangci-lint", "rubocop"]


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


def detect_linters(root: Path, files: list[Path]) -> DetectorFindings:
    """Detect lint and formatting tools."""
    detected: set[str] = set()
    evidence: dict[str, list[str]] = {}

    file_names = {path.name for path in files}
    deps = _package_dependencies(root)

    pyproject = root / "pyproject.toml"
    if pyproject.exists() and "[tool.ruff" in read_text(pyproject):
        detected.add("ruff")
        evidence.setdefault("ruff", []).append("pyproject.toml")
    if "ruff.toml" in file_names or ".ruff.toml" in file_names:
        detected.add("ruff")
        evidence.setdefault("ruff", []).append("ruff.toml")

    if "eslint" in deps or "eslint.config.js" in file_names or ".eslintrc" in file_names:
        detected.add("eslint")
        evidence.setdefault("eslint", []).append("package.json/eslint config")

    prettier_configs = {".prettierrc", ".prettierrc.json", "prettier.config.js", "prettier.config.cjs"}
    if "prettier" in deps or any(name in file_names for name in prettier_configs):
        detected.add("prettier")
        evidence.setdefault("prettier", []).append("package.json/prettier config")

    if "Cargo.toml" in file_names:
        detected.add("clippy")
        evidence.setdefault("clippy", []).append("Cargo.toml")

    golangci_configs = {".golangci.yml", ".golangci.yaml", ".golangci.toml", ".golangci.json"}
    if any(config_name in file_names for config_name in golangci_configs):
        detected.add("golangci-lint")
        evidence.setdefault("golangci-lint", []).append(".golangci config")

    if ".rubocop.yml" in file_names:
        detected.add("rubocop")
        evidence.setdefault("rubocop", []).append(".rubocop.yml")

    values = [tool for tool in LINTER_ORDER if tool in detected]
    trimmed_evidence = {k: sorted(set(v))[:5] for k, v in evidence.items() if k in detected}
    return DetectorFindings(values=values, evidence=trimmed_evidence)
