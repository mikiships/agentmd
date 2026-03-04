"""Tests for --json flag on all CLI commands."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentmd.cli import app

runner = CliRunner()


def _make_project(tmp_path: Path, *, with_context: bool = False) -> Path:
    """Create a minimal Python project for testing."""
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent("""\
            [build-system]
            requires = ["hatchling"]
            build-backend = "hatchling.build"
            [project]
            name = "demo"
            version = "0.1.0"
        """)
    )
    (tmp_path / "main.py").write_text("print('hello')\n")
    if with_context:
        (tmp_path / "CLAUDE.md").write_text(
            textwrap.dedent("""\
                # CLAUDE.md
                ## Project Overview
                Python demo project.
                ## Build, Test, and Lint Commands
                ```
                python -m pytest
                ```
                ## Code Style
                Follow PEP 8.
            """)
        )
    return tmp_path


# ---------------------------------------------------------------------------
# scan --json
# ---------------------------------------------------------------------------

class TestScanJson:
    def test_produces_valid_json(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["scan", "--json", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)

    def test_json_schema(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["scan", "--json", str(tmp_path)])
        data = json.loads(result.output)
        # ProjectAnalysis.to_dict() should have these keys
        assert "languages" in data
        assert "frameworks" in data
        assert "existing_context_files" in data

    def test_suppresses_human_output(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["scan", "--json", str(tmp_path)])
        assert result.exit_code == 0
        # Should not contain human-readable headers
        assert "Scanning" not in result.output
        assert "Project Analysis" not in result.output
        assert "Context Files" not in result.output

    def test_languages_is_list(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["scan", "--json", str(tmp_path)])
        data = json.loads(result.output)
        assert isinstance(data["languages"], list)


# ---------------------------------------------------------------------------
# generate --json
# ---------------------------------------------------------------------------

class TestGenerateJson:
    def test_produces_valid_json(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", "--json", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)

    def test_json_schema(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", "--json", str(tmp_path)])
        data = json.loads(result.output)
        assert "path" in data
        assert "agents" in data
        assert "contents" in data
        assert "files_written" in data
        assert "files_skipped" in data

    def test_contents_has_agent_keys(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", "--json", str(tmp_path)])
        data = json.loads(result.output)
        # All agents should be present in contents
        for agent_name in data["agents"]:
            assert agent_name in data["contents"]
            assert isinstance(data["contents"][agent_name], str)

    def test_single_agent_json(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", "--json", "--agent", "claude", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["agents"] == ["claude"]
        assert "claude" in data["contents"]

    def test_suppresses_human_output(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", "--json", str(tmp_path)])
        assert result.exit_code == 0
        # Human-readable action words should not appear as standalone output lines
        assert "  wrote  " not in result.output
        assert "  skip  " not in result.output

    def test_path_in_output(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", "--json", str(tmp_path)])
        data = json.loads(result.output)
        assert data["path"] == str(tmp_path.resolve())

    def test_files_written_tracked(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", "--json", "--agent", "claude", str(tmp_path)])
        data = json.loads(result.output)
        assert "CLAUDE.md" in data["files_written"]

    def test_files_skipped_tracked(self, tmp_path):
        _make_project(tmp_path)
        # First write
        runner.invoke(app, ["generate", "--agent", "claude", str(tmp_path)])
        # Second call without --force should skip
        result = runner.invoke(app, ["generate", "--json", "--agent", "claude", str(tmp_path)])
        data = json.loads(result.output)
        assert "CLAUDE.md" in data["files_skipped"]


# ---------------------------------------------------------------------------
# score --json
# ---------------------------------------------------------------------------

class TestScoreJson:
    def test_produces_valid_json(self, tmp_path):
        _make_project(tmp_path, with_context=True)
        result = runner.invoke(app, ["score", "--json", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_json_schema(self, tmp_path):
        _make_project(tmp_path, with_context=True)
        result = runner.invoke(app, ["score", "--json", str(tmp_path)])
        data = json.loads(result.output)
        assert len(data) >= 1
        item = data[0]
        # ScoringResult.to_dict() keys
        assert "composite_score" in item
        assert "dimensions" in item

    def test_suppresses_human_output(self, tmp_path):
        _make_project(tmp_path, with_context=True)
        result = runner.invoke(app, ["score", "--json", str(tmp_path)])
        assert result.exit_code == 0
        assert "Suggestions" not in result.output
        assert "---" not in result.output

    def test_single_file_json(self, tmp_path):
        _make_project(tmp_path, with_context=True)
        claude_md = tmp_path / "CLAUDE.md"
        result = runner.invoke(app, ["score", "--json", str(claude_md)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1

    def test_no_context_files_returns_empty_list(self, tmp_path):
        _make_project(tmp_path, with_context=False)
        result = runner.invoke(app, ["score", "--json", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == []

    def test_dimensions_is_list(self, tmp_path):
        _make_project(tmp_path, with_context=True)
        result = runner.invoke(app, ["score", "--json", str(tmp_path)])
        data = json.loads(result.output)
        assert isinstance(data[0]["dimensions"], list)


# ---------------------------------------------------------------------------
# diff --json
# ---------------------------------------------------------------------------

class TestDiffJson:
    def test_produces_valid_json(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["diff", "--json", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_json_schema(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["diff", "--json", str(tmp_path)])
        data = json.loads(result.output)
        assert len(data) >= 1
        item = data[0]
        assert "file" in item
        assert "agent" in item
        assert "has_changes" in item
        assert "diff" in item

    def test_no_changes_diff_is_null(self, tmp_path):
        _make_project(tmp_path)
        # Generate first so files are up to date
        runner.invoke(app, ["generate", "--force", str(tmp_path)])
        result = runner.invoke(app, ["diff", "--json", str(tmp_path)])
        data = json.loads(result.output)
        for item in data:
            assert item["has_changes"] is False
            assert item["diff"] is None

    def test_has_changes_when_file_missing(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["diff", "--json", "--agent", "claude", str(tmp_path)])
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["has_changes"] is True
        assert data[0]["diff"] is not None

    def test_suppresses_human_output(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["diff", "--json", str(tmp_path)])
        assert result.exit_code == 0
        assert "no changes" not in result.output
        assert "All context files" not in result.output

    def test_single_agent_json(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["diff", "--json", "--agent", "claude", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["agent"] == "claude"

    def test_diff_string_content(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["diff", "--json", "--agent", "claude", str(tmp_path)])
        data = json.loads(result.output)
        # diff should be a non-empty string when has_changes is True
        assert isinstance(data[0]["diff"], str)
        assert len(data[0]["diff"]) > 0


# ---------------------------------------------------------------------------
# drift --json
# ---------------------------------------------------------------------------

class TestDriftJson:
    def test_produces_valid_json(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["drift", "--json", "--agent", "claude", str(tmp_path)])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert isinstance(data, dict)

    def test_json_schema(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["drift", "--json", "--agent", "claude", str(tmp_path)])
        data = json.loads(result.output)
        assert "schema" in data
        assert data["schema"]["name"] == "agentmd.drift.report"
        assert "summary" in data
        assert "files" in data
        assert len(data["files"]) == 1

    def test_no_drift_exit_zero(self, tmp_path):
        _make_project(tmp_path)
        runner.invoke(app, ["generate", "--agent", "claude", str(tmp_path)])
        result = runner.invoke(app, ["drift", "--json", "--agent", "claude", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["has_drift"] is False
        assert data["files"][0]["status"] == "fresh"

    def test_detects_missing_context_file(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["drift", "--json", "--agent", "claude", str(tmp_path)])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["files"][0]["status"] == "missing"
        assert data["summary"]["sections_added"] >= 1

    def test_stale_details_are_present(self, tmp_path):
        _make_project(tmp_path)
        runner.invoke(app, ["generate", "--agent", "claude", str(tmp_path)])
        (tmp_path / "CLAUDE.md").write_text(
            "# CLAUDE.md\n\n## Project Overview\noutdated\n",
            encoding="utf-8",
        )
        result = runner.invoke(app, ["drift", "--json", "--agent", "claude", str(tmp_path)])
        data = json.loads(result.output)
        assert result.exit_code == 1
        assert data["files"][0]["stale_details"]

    def test_rejects_json_with_format_github(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(
            app,
            ["drift", "--json", "--format", "github", "--agent", "claude", str(tmp_path)],
        )
        assert result.exit_code != 0

    def test_rejects_json_with_format_markdown(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(
            app,
            ["drift", "--json", "--format", "markdown", "--agent", "claude", str(tmp_path)],
        )
        assert result.exit_code != 0
