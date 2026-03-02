"""Tests for Go project detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentmd.detectors.go import detect_go_project


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_files(tmp_path: Path, structure: dict[str, str]) -> list[Path]:
    """Write files under tmp_path and return relative Path list."""
    paths: list[Path] = []
    for rel, content in structure.items():
        full = tmp_path / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        paths.append(Path(rel))
    return paths


_MINIMAL_GO_MOD = "module example.com/myapp\n\ngo 1.21\n"


# ---------------------------------------------------------------------------
# Project file detection
# ---------------------------------------------------------------------------

def test_detects_go_mod(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"go.mod": _MINIMAL_GO_MOD})
    result = detect_go_project(tmp_path, files)
    assert "go-mod" in result.values
    assert "go.mod" in result.evidence.get("go-mod", [])


def test_detects_go_sum(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "go.mod": _MINIMAL_GO_MOD,
        "go.sum": "github.com/some/dep v1.0.0 h1:abc=\n",
    })
    result = detect_go_project(tmp_path, files)
    assert "go-sum" in result.values
    assert "go.sum" in result.evidence.get("go-sum", [])


def test_detects_go_work(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "go.work": "go 1.21\n\nuse (\n\t./service-a\n\t./service-b\n)\n",
    })
    result = detect_go_project(tmp_path, files)
    assert "go-work" in result.values
    assert "go.work" in result.evidence.get("go-work", [])


def test_no_go_mod_no_detections(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"README.md": "# hello\n"})
    result = detect_go_project(tmp_path, files)
    assert result.values == []
    assert result.evidence == {}


# ---------------------------------------------------------------------------
# Build tool detection
# ---------------------------------------------------------------------------

def test_go_implied_by_go_mod(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"go.mod": _MINIMAL_GO_MOD})
    result = detect_go_project(tmp_path, files)
    assert "go" in result.values
    assert "go.mod" in result.evidence.get("go", [])


def test_detects_makefile_with_go_build(tmp_path: Path) -> None:
    makefile = "build:\n\tgo build ./...\n"
    files = _make_files(tmp_path, {"go.mod": _MINIMAL_GO_MOD, "Makefile": makefile})
    result = detect_go_project(tmp_path, files)
    assert "make-go" in result.values
    assert "Makefile" in result.evidence.get("make-go", [])


def test_detects_makefile_with_go_test(tmp_path: Path) -> None:
    makefile = "test:\n\tgo test ./...\n"
    files = _make_files(tmp_path, {"go.mod": _MINIMAL_GO_MOD, "Makefile": makefile})
    result = detect_go_project(tmp_path, files)
    assert "make-go" in result.values


def test_makefile_without_go_targets_not_detected(tmp_path: Path) -> None:
    makefile = "build:\n\tnpm run build\n"
    files = _make_files(tmp_path, {"go.mod": _MINIMAL_GO_MOD, "Makefile": makefile})
    result = detect_go_project(tmp_path, files)
    assert "make-go" not in result.values


def test_no_make_go_without_makefile(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"go.mod": _MINIMAL_GO_MOD})
    result = detect_go_project(tmp_path, files)
    assert "make-go" not in result.values


# ---------------------------------------------------------------------------
# Framework / library detection
# ---------------------------------------------------------------------------

def _go_mod_with_deps(*deps: str) -> str:
    require_lines = "\n".join(f"\t{dep} v1.0.0" for dep in deps)
    return f"{_MINIMAL_GO_MOD}\nrequire (\n{require_lines}\n)\n"


@pytest.mark.parametrize("framework,module_path", [
    ("gin",     "github.com/gin-gonic/gin"),
    ("echo",    "github.com/labstack/echo"),
    ("fiber",   "github.com/gofiber/fiber"),
    ("chi",     "github.com/go-chi/chi"),
    ("cobra",   "github.com/spf13/cobra"),
    ("viper",   "github.com/spf13/viper"),
    ("gorm",    "gorm.io/gorm"),
    ("ent",     "entgo.io/ent"),
    ("fx",      "go.uber.org/fx"),
    ("wire",    "github.com/google/wire"),
    ("zap",     "go.uber.org/zap"),
    ("logrus",  "github.com/sirupsen/logrus"),
    ("testify", "github.com/stretchr/testify"),
    ("gomock",  "github.com/golang/mock"),
])
def test_detects_framework(tmp_path: Path, framework: str, module_path: str) -> None:
    files = _make_files(tmp_path, {"go.mod": _go_mod_with_deps(module_path)})
    result = detect_go_project(tmp_path, files)
    assert framework in result.values
    assert "go.mod" in result.evidence.get(framework, [])


def test_no_framework_without_require(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"go.mod": _MINIMAL_GO_MOD})
    result = detect_go_project(tmp_path, files)
    for fw in ("gin", "echo", "fiber", "chi", "cobra", "viper",
               "gorm", "ent", "fx", "wire", "zap", "logrus", "testify", "gomock"):
        assert fw not in result.values


def test_detects_multiple_frameworks(tmp_path: Path) -> None:
    go_mod = _go_mod_with_deps(
        "github.com/gin-gonic/gin",
        "go.uber.org/zap",
        "github.com/stretchr/testify",
    )
    files = _make_files(tmp_path, {"go.mod": go_mod})
    result = detect_go_project(tmp_path, files)
    assert "gin" in result.values
    assert "zap" in result.values
    assert "testify" in result.values


def test_single_line_require_detected(tmp_path: Path) -> None:
    go_mod = f"{_MINIMAL_GO_MOD}\nrequire github.com/spf13/cobra v1.8.0\n"
    files = _make_files(tmp_path, {"go.mod": go_mod})
    result = detect_go_project(tmp_path, files)
    assert "cobra" in result.values


# ---------------------------------------------------------------------------
# Linter detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cfg_file", [".golangci.yml", ".golangci.yaml", ".golangci.toml"])
def test_detects_golangci_lint(tmp_path: Path, cfg_file: str) -> None:
    files = _make_files(tmp_path, {
        "go.mod": _MINIMAL_GO_MOD,
        cfg_file: "linters:\n  enable:\n    - errcheck\n",
    })
    result = detect_go_project(tmp_path, files)
    assert "golangci-lint" in result.values
    assert cfg_file in result.evidence.get("golangci-lint", [])


def test_no_golangci_lint_without_config(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"go.mod": _MINIMAL_GO_MOD})
    result = detect_go_project(tmp_path, files)
    assert "golangci-lint" not in result.values


def test_go_vet_implied_by_go_mod(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"go.mod": _MINIMAL_GO_MOD})
    result = detect_go_project(tmp_path, files)
    assert "go-vet" in result.values
    assert "go.mod" in result.evidence.get("go-vet", [])


def test_no_go_vet_without_go_mod(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"README.md": "# project\n"})
    result = detect_go_project(tmp_path, files)
    assert "go-vet" not in result.values


# ---------------------------------------------------------------------------
# CI detection
# ---------------------------------------------------------------------------

def test_detects_go_ci_in_github_actions(tmp_path: Path) -> None:
    workflow = (
        "name: CI\non: [push]\njobs:\n  test:\n    steps:\n"
        "      - run: go test ./...\n"
    )
    files = _make_files(tmp_path, {
        "go.mod": _MINIMAL_GO_MOD,
        ".github/workflows/ci.yml": workflow,
    })
    result = detect_go_project(tmp_path, files)
    assert "go-ci" in result.values
    assert ".github/workflows/ci.yml" in result.evidence.get("go-ci", [])


def test_no_go_ci_without_go_commands(tmp_path: Path) -> None:
    workflow = "name: CI\non: [push]\njobs:\n  test:\n    steps:\n      - run: npm test\n"
    files = _make_files(tmp_path, {
        "go.mod": _MINIMAL_GO_MOD,
        ".github/workflows/ci.yml": workflow,
    })
    result = detect_go_project(tmp_path, files)
    assert "go-ci" not in result.values


def test_no_go_ci_without_workflows(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"go.mod": _MINIMAL_GO_MOD})
    result = detect_go_project(tmp_path, files)
    assert "go-ci" not in result.values


# ---------------------------------------------------------------------------
# Output ordering
# ---------------------------------------------------------------------------

def test_values_in_expected_order(tmp_path: Path) -> None:
    go_mod = _go_mod_with_deps("github.com/gin-gonic/gin", "go.uber.org/zap")
    workflow = "name: CI\non: [push]\njobs:\n  test:\n    steps:\n      - run: go test ./...\n"
    makefile = "build:\n\tgo build ./...\n"
    files = _make_files(tmp_path, {
        "go.mod": go_mod,
        "go.sum": "",
        ".golangci.yml": "linters:\n  enable:\n    - errcheck\n",
        "Makefile": makefile,
        ".github/workflows/ci.yml": workflow,
    })
    result = detect_go_project(tmp_path, files)
    # go-mod and go-sum must precede go and make-go
    assert result.values.index("go-mod") < result.values.index("go")
    assert result.values.index("go-mod") < result.values.index("make-go")
    # frameworks must come after build tools
    assert result.values.index("make-go") < result.values.index("gin")
    # linters after frameworks
    assert result.values.index("gin") < result.values.index("golangci-lint")
    # CI last
    assert result.values.index("golangci-lint") < result.values.index("go-ci")


# ---------------------------------------------------------------------------
# Evidence trimming
# ---------------------------------------------------------------------------

def test_evidence_keys_match_detected_values(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"go.mod": _MINIMAL_GO_MOD})
    result = detect_go_project(tmp_path, files)
    for key in result.evidence:
        assert key in result.values
