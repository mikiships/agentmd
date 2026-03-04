"""Integration tests for end-to-end drift detection."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentmd.cli import app

runner = CliRunner()


def _make_project(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "main.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "tests" / "test_main.py").write_text(
        "from src.main import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\nversion='0.1.0'\n",
        encoding="utf-8",
    )
    return tmp_path


def test_drift_pipeline_flags_single_stale_file(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    generated = runner.invoke(app, ["generate", str(project)])
    assert generated.exit_code == 0

    (project / "CLAUDE.md").write_text(
        "# CLAUDE.md\n\n## Project Overview\nThis file is stale.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["drift", "--json", str(project)])
    assert result.exit_code == 1
    payload = json.loads(result.output)

    assert payload["has_drift"] is True
    assert payload["summary"]["files"] == 4
    assert payload["summary"]["files_with_drift"] >= 1

    files = {item["file"]: item for item in payload["files"]}
    assert files["CLAUDE.md"]["status"] == "stale"
    assert files["CLAUDE.md"]["sections_changed"] or files["CLAUDE.md"]["sections_removed"]
