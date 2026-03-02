"""Go project detection heuristics."""

from __future__ import annotations

import re
from pathlib import Path

from agentmd.detectors.common import read_text
from agentmd.types import DetectorFindings

# Ordered lists for deterministic output
PROJECT_FILE_ORDER = ["go-mod", "go-sum", "go-work"]
BUILD_TOOL_ORDER = ["go", "make-go"]
FRAMEWORK_ORDER = [
    "gin", "echo", "fiber", "chi", "cobra", "viper",
    "gorm", "ent", "fx", "wire", "zap", "logrus", "testify", "gomock",
]
LINTER_ORDER = ["golangci-lint", "go-vet"]
CI_ORDER = ["go-ci"]

# Map framework short name -> go.mod module path substring
FRAMEWORK_MODULES: dict[str, str] = {
    "gin":      "github.com/gin-gonic/gin",
    "echo":     "github.com/labstack/echo",
    "fiber":    "github.com/gofiber/fiber",
    "chi":      "github.com/go-chi/chi",
    "cobra":    "github.com/spf13/cobra",
    "viper":    "github.com/spf13/viper",
    "gorm":     "gorm.io/gorm",
    "ent":      "entgo.io/ent",
    "fx":       "go.uber.org/fx",
    "wire":     "github.com/google/wire",
    "zap":      "go.uber.org/zap",
    "logrus":   "github.com/sirupsen/logrus",
    "testify":  "github.com/stretchr/testify",
    "gomock":   "github.com/golang/mock",
}


def _parse_require_block(content: str) -> str:
    """Extract text within require(...) blocks and standalone require lines."""
    parts: list[str] = []
    # Multi-line require blocks
    for block in re.findall(r"require\s*\(([^)]*)\)", content, re.DOTALL):
        parts.append(block)
    # Single-line require statements
    for line in re.findall(r"^require\s+(.+)$", content, re.MULTILINE):
        parts.append(line)
    return "\n".join(parts)


def detect_go_project(root: Path, files: list[Path]) -> DetectorFindings:
    """Detect Go project files, build tools, frameworks, linters, and CI usage."""
    detected: set[str] = set()
    evidence: dict[str, list[str]] = {}

    file_names = {path.name for path in files}
    file_paths_str = [str(path) for path in files]

    # --- Project file detection ---
    if "go.mod" in file_names:
        detected.add("go-mod")
        evidence.setdefault("go-mod", []).append("go.mod")

    if "go.sum" in file_names:
        detected.add("go-sum")
        evidence.setdefault("go-sum", []).append("go.sum")

    if "go.work" in file_names:
        detected.add("go-work")
        evidence.setdefault("go-work", []).append("go.work")

    # --- Build tool detection ---
    # `go` is implied whenever go.mod is present
    if "go-mod" in detected:
        detected.add("go")
        evidence.setdefault("go", []).append("go.mod")

    # Makefile with go targets (run/build/test commands invoking go)
    if "Makefile" in file_names:
        makefile = root / "Makefile"
        content = read_text(makefile, max_chars=20000)
        if content and re.search(r"^\s*go\s+(build|run|test|install|generate)\b", content, re.MULTILINE):
            detected.add("make-go")
            evidence.setdefault("make-go", []).append("Makefile")

    # --- Framework / library detection via go.mod require block ---
    go_mod_path = root / "go.mod"
    if go_mod_path.exists():
        go_mod_content = read_text(go_mod_path, max_chars=50000) or ""
        require_text = _parse_require_block(go_mod_content)
        for name, module_path in FRAMEWORK_MODULES.items():
            if module_path in require_text:
                detected.add(name)
                evidence.setdefault(name, []).append("go.mod")

    # --- Linter detection ---
    golangci_configs = {".golangci.yml", ".golangci.yaml", ".golangci.toml"}
    for cfg in golangci_configs:
        if cfg in file_names:
            detected.add("golangci-lint")
            evidence.setdefault("golangci-lint", []).append(cfg)
            break

    # go vet is implicit when go.mod is present
    if "go-mod" in detected:
        detected.add("go-vet")
        evidence.setdefault("go-vet", []).append("go.mod")

    # --- CI: go commands in GitHub Actions workflows ---
    workflow_files = [
        root / path
        for path in files
        if str(path).startswith(".github/workflows/") and path.suffix in {".yml", ".yaml"}
    ]
    for wf in workflow_files:
        content = read_text(wf, max_chars=20000)
        if content and re.search(r"\bgo\s+(build|test|run|install|generate|mod)\b", content):
            detected.add("go-ci")
            evidence.setdefault("go-ci", []).append(str(wf.relative_to(root)))
            break

    # Build ordered values list
    order = PROJECT_FILE_ORDER + BUILD_TOOL_ORDER + FRAMEWORK_ORDER + LINTER_ORDER + CI_ORDER
    values = [item for item in order if item in detected]
    trimmed_evidence = {k: sorted(set(v))[:5] for k, v in evidence.items() if k in detected}
    return DetectorFindings(values=values, evidence=trimmed_evidence)
