"""Framework detection heuristics."""

from __future__ import annotations

import json
from pathlib import Path

from agentmd.detectors.common import read_text
from agentmd.types import DetectorFindings

FRAMEWORKS = [
    "FastAPI",
    "Flask",
    "Django",
    "Express",
    "Next.js",
    "React",
    "Vue",
    "actix-web",
    "gin",
    "Rails",
]


def _package_dependencies(root: Path) -> set[str]:
    package_json = root / "package.json"
    if not package_json.exists():
        return set()
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return set()
    dependencies: set[str] = set()
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        values = data.get(section, {})
        if isinstance(values, dict):
            dependencies.update(values.keys())
    return dependencies


def detect_frameworks(root: Path, files: list[Path]) -> DetectorFindings:
    """Detect common backend/frontend frameworks."""
    detected: set[str] = set()
    evidence: dict[str, list[str]] = {}

    deps = _package_dependencies(root)
    file_names = {path.name for path in files}

    if "fastapi" in deps:
        detected.add("FastAPI")
        evidence.setdefault("FastAPI", []).append("package.json: fastapi")
    if "flask" in deps:
        detected.add("Flask")
        evidence.setdefault("Flask", []).append("package.json: flask")
    if "django" in deps:
        detected.add("Django")
        evidence.setdefault("Django", []).append("package.json: django")

    if "express" in deps:
        detected.add("Express")
        evidence.setdefault("Express", []).append("package.json dependency express")
    if "next" in deps or "next.config.js" in file_names or "next.config.mjs" in file_names:
        detected.add("Next.js")
        evidence.setdefault("Next.js", []).append("next dependency or config")
    if "react" in deps or any(path.suffix in {".jsx", ".tsx"} for path in files):
        detected.add("React")
        evidence.setdefault("React", []).append("react dependency or JSX/TSX files")
    if "vue" in deps or any(path.suffix == ".vue" for path in files):
        detected.add("Vue")
        evidence.setdefault("Vue", []).append("vue dependency or .vue files")

    pyproject = root / "pyproject.toml"
    requirements = root / "requirements.txt"
    pyproject_text = read_text(pyproject) if pyproject.exists() else ""
    requirements_text = read_text(requirements) if requirements.exists() else ""

    if "fastapi" in pyproject_text.lower() or "fastapi" in requirements_text.lower():
        detected.add("FastAPI")
        evidence.setdefault("FastAPI", []).append("pyproject.toml/requirements.txt")
    if "flask" in pyproject_text.lower() or "flask" in requirements_text.lower():
        detected.add("Flask")
        evidence.setdefault("Flask", []).append("pyproject.toml/requirements.txt")
    if "django" in pyproject_text.lower() or "django" in requirements_text.lower() or "manage.py" in file_names:
        detected.add("Django")
        evidence.setdefault("Django", []).append("manage.py or Python deps")

    cargo_toml = root / "Cargo.toml"
    if cargo_toml.exists():
        cargo_text = read_text(cargo_toml).lower()
        if "actix-web" in cargo_text:
            detected.add("actix-web")
            evidence.setdefault("actix-web", []).append("Cargo.toml dependency")

    go_files = [root / file_path for file_path in files if file_path.suffix == ".go"]
    for go_file in go_files[:20]:
        text = read_text(go_file, max_chars=4000)
        if "github.com/gin-gonic/gin" in text:
            detected.add("gin")
            evidence.setdefault("gin", []).append(str(go_file.relative_to(root)))
            break

    gemfile = root / "Gemfile"
    if gemfile.exists():
        gemfile_text = read_text(gemfile).lower()
        if "rails" in gemfile_text:
            detected.add("Rails")
            evidence.setdefault("Rails", []).append("Gemfile dependency rails")

    values = [framework for framework in FRAMEWORKS if framework in detected]
    trimmed_evidence = {k: sorted(set(v))[:5] for k, v in evidence.items() if k in detected}
    return DetectorFindings(values=values, evidence=trimmed_evidence)
