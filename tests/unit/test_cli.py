"""Tests for the CLI interface."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentmd.cli import app
from agentmd.generators import GENERATOR_MAP

runner = CliRunner()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

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
# scan
# ---------------------------------------------------------------------------

class TestScan:
    def test_scan_prints_analysis(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["scan", str(tmp_path)])
        assert result.exit_code == 0
        assert "Project Analysis" in result.output
        assert "Context Files" in result.output

    def test_scan_shows_python_language(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["scan", str(tmp_path)])
        assert result.exit_code == 0
        # Python should be detected (main.py + pyproject.toml)
        assert "python" in result.output.lower() or "Languages" in result.output

    def test_scan_shows_context_file_presence(self, tmp_path):
        _make_project(tmp_path, with_context=True)
        result = runner.invoke(app, ["scan", str(tmp_path)])
        assert result.exit_code == 0
        assert "present" in result.output
        assert "CLAUDE.md" in result.output

    def test_scan_defaults_to_cwd(self, tmp_path, monkeypatch):
        _make_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 0
        assert "Project Analysis" in result.output

    def test_scan_invalid_path(self, tmp_path):
        result = runner.invoke(app, ["scan", str(tmp_path / "nonexistent")])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

class TestGenerate:
    def test_generate_all_agents(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", str(tmp_path)])
        assert result.exit_code == 0
        # All generator output files should be created
        for name, cls in GENERATOR_MAP.items():
            gen = cls.__new__(cls)
            assert (tmp_path / gen.output_filename).exists(), f"{gen.output_filename} not created"

    def test_generate_single_agent(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", str(tmp_path), "--agent", "claude"])
        assert result.exit_code == 0
        assert (tmp_path / "CLAUDE.md").exists()

    def test_generate_dry_run_no_files(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", str(tmp_path), "--dry-run"])
        assert result.exit_code == 0
        assert "[dry-run]" in result.output
        # No files written
        for name, cls in GENERATOR_MAP.items():
            gen = cls.__new__(cls)
            assert not (tmp_path / gen.output_filename).exists()

    def test_generate_skip_existing_without_force(self, tmp_path):
        _make_project(tmp_path)
        (tmp_path / "CLAUDE.md").write_text("original\n")
        result = runner.invoke(app, ["generate", str(tmp_path), "--agent", "claude"])
        assert result.exit_code == 0
        assert "skip" in result.output
        assert (tmp_path / "CLAUDE.md").read_text() == "original\n"

    def test_generate_force_overwrites(self, tmp_path):
        _make_project(tmp_path)
        (tmp_path / "CLAUDE.md").write_text("original\n")
        result = runner.invoke(app, ["generate", str(tmp_path), "--agent", "claude", "--force"])
        assert result.exit_code == 0
        assert (tmp_path / "CLAUDE.md").read_text() != "original\n"

    def test_generate_unknown_agent_error(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", str(tmp_path), "--agent", "bogus"])
        assert result.exit_code != 0

    def test_generate_invalid_path(self, tmp_path):
        result = runner.invoke(app, ["generate", str(tmp_path / "nope")])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# score
# ---------------------------------------------------------------------------

class TestScore:
    def test_score_present_context_file(self, tmp_path):
        _make_project(tmp_path, with_context=True)
        result = runner.invoke(app, ["score", str(tmp_path)])
        assert result.exit_code == 0
        assert "CLAUDE.md" in result.output
        assert "composite" in result.output

    def test_score_no_context_files(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["score", str(tmp_path)])
        assert result.exit_code == 0
        assert "No context files found" in result.output

    def test_score_shows_dimensions(self, tmp_path):
        _make_project(tmp_path, with_context=True)
        result = runner.invoke(app, ["score", str(tmp_path)])
        assert result.exit_code == 0
        assert "completeness" in result.output

    def test_score_invalid_path(self, tmp_path):
        result = runner.invoke(app, ["score", str(tmp_path / "nope")])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------

class TestDiff:
    def test_diff_no_existing_files(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["diff", str(tmp_path)])
        assert result.exit_code == 0
        # All files are "new" so diffs should be shown
        # Output should contain diff markers or no-changes messages
        assert result.output  # non-empty

    def test_diff_up_to_date(self, tmp_path):
        _make_project(tmp_path)
        # Generate first
        runner.invoke(app, ["generate", str(tmp_path)])
        # Diff should show no changes
        result = runner.invoke(app, ["diff", str(tmp_path)])
        assert result.exit_code == 0
        assert "up to date" in result.output or "no changes" in result.output

    def test_diff_single_agent(self, tmp_path):
        _make_project(tmp_path)
        runner.invoke(app, ["generate", str(tmp_path), "--agent", "claude"])
        result = runner.invoke(app, ["diff", str(tmp_path), "--agent", "claude"])
        assert result.exit_code == 0
        assert "no changes" in result.output

    def test_diff_shows_changes(self, tmp_path):
        _make_project(tmp_path)
        (tmp_path / "CLAUDE.md").write_text("# Old content\nThis is outdated.\n")
        result = runner.invoke(app, ["diff", str(tmp_path), "--agent", "claude"])
        assert result.exit_code == 0
        # Should show unified diff markers
        assert "---" in result.output or "+++" in result.output

    def test_diff_unknown_agent_error(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["diff", str(tmp_path), "--agent", "bogus"])
        assert result.exit_code != 0

    def test_diff_invalid_path(self, tmp_path):
        result = runner.invoke(app, ["diff", str(tmp_path / "nope")])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# drift
# ---------------------------------------------------------------------------

class TestDrift:
    def test_drift_clean_exit_zero(self, tmp_path):
        _make_project(tmp_path)
        runner.invoke(app, ["generate", str(tmp_path), "--agent", "claude"])
        result = runner.invoke(app, ["drift", str(tmp_path), "--agent", "claude"])
        assert result.exit_code == 0
        assert "fresh" in result.output

    def test_drift_stale_exit_one(self, tmp_path):
        _make_project(tmp_path)
        runner.invoke(app, ["generate", str(tmp_path), "--agent", "claude"])
        (tmp_path / "CLAUDE.md").write_text("# CLAUDE.md\n\n## Project Overview\nold content\n")
        result = runner.invoke(app, ["drift", str(tmp_path), "--agent", "claude"])
        assert result.exit_code == 1
        assert "sections_changed" in result.output
        assert "sections_stale" in result.output

    def test_drift_missing_file_exit_one(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["drift", str(tmp_path), "--agent", "claude"])
        assert result.exit_code == 1
        assert "missing" in result.output

    def test_drift_github_format(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(
            app,
            ["drift", str(tmp_path), "--agent", "claude", "--format", "github"],
        )
        assert result.exit_code == 1
        assert "::warning file=CLAUDE.md,title=agentmd drift::" in result.output

    def test_drift_invalid_format(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(
            app,
            ["drift", str(tmp_path), "--agent", "claude", "--format", "xml"],
        )
        assert result.exit_code != 0
