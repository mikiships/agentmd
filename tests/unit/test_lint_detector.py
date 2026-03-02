import json
from pathlib import Path

from agentmd.detectors.common import collect_project_files
from agentmd.detectors.lint import detect_linters


def test_detect_linters(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\nline-length = 100\n", encoding="utf-8")

    package_json = {"devDependencies": {"eslint": "^9", "prettier": "^3"}}
    (tmp_path / "package.json").write_text(json.dumps(package_json), encoding="utf-8")

    (tmp_path / "Cargo.toml").write_text("[package]\nname='x'\n", encoding="utf-8")
    (tmp_path / ".golangci.yml").write_text("run:\n  timeout: 5m\n", encoding="utf-8")
    (tmp_path / ".rubocop.yml").write_text("AllCops:\n  NewCops: enable\n", encoding="utf-8")

    files = collect_project_files(tmp_path)
    result = detect_linters(tmp_path, files)

    assert "ruff" in result.values
    assert "eslint" in result.values
    assert "prettier" in result.values
    assert "clippy" in result.values
    assert "golangci-lint" in result.values
    assert "rubocop" in result.values
