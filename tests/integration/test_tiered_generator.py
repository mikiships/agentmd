"""Integration tests for D2: tiered context generation end-to-end."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentmd.cli import app
from agentmd.detectors.subsystem import SubsystemInfo, detect_subsystems, is_project_too_small
from agentmd.generators.tiered import TieredGenerator, TieredOutput
from agentmd.types import DirectoryStructure, GitHistorySummary, ProjectAnalysis


runner = CliRunner()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _create_large_project(tmp_path: Path) -> None:
    """Create a multi-module project large enough for tiered generation."""
    # api module
    for i in range(6):
        p = tmp_path / f"api/handler{i}.py"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# handler {i}\n" * 200, encoding="utf-8")

    # db module
    for i in range(5):
        p = tmp_path / f"db/model{i}.py"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# model {i}\n" * 200, encoding="utf-8")

    # web module
    for i in range(4):
        p = tmp_path / f"web/page{i}.ts"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"// page {i}\n" * 200, encoding="utf-8")

    # utils module to push past the 20-file threshold
    for i in range(6):
        p = tmp_path / f"utils/helper{i}.py"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# helper {i}\n" * 200, encoding="utf-8")

    # Extra top-level files for analyzer
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n', encoding="utf-8")
    (tmp_path / "README.md").write_text("# Test\n", encoding="utf-8")


def _make_analysis() -> ProjectAnalysis:
    return ProjectAnalysis(
        root_path="/tmp/proj",
        languages=["Python", "TypeScript"],
        package_managers=["pip", "npm"],
        frameworks=["FastAPI"],
        test_runners=["pytest"],
        linters=["ruff"],
        ci_systems=["GitHub Actions"],
        directory_structure=DirectoryStructure(
            top_level_directories=["api", "db", "web", "tests"],
            source_directories=["api", "db", "web"],
            test_directories=["tests"],
        ),
        git_history=GitHistorySummary(commit_count=50),
    )


def _make_subsystems() -> list[SubsystemInfo]:
    return [
        SubsystemInfo(name="api", path="api", file_count=6, languages=["Python"],
                       frameworks=["FastAPI"]),
        SubsystemInfo(name="db", path="db", file_count=5, languages=["Python"]),
        SubsystemInfo(name="web", path="web", file_count=4, languages=["TypeScript"]),
    ]


# ------------------------------------------------------------------
# TieredGenerator unit tests
# ------------------------------------------------------------------

class TestTieredGenerator:
    def test_generates_tier1_and_tier2(self) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        output = gen.generate()
        assert isinstance(output, TieredOutput)
        assert output.tier1_path == "CLAUDE.md"
        assert len(output.tier2_files) == 3
        assert ".agents/api.md" in output.tier2_files
        assert ".agents/db.md" in output.tier2_files
        assert ".agents/web.md" in output.tier2_files

    def test_file_count(self) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        output = gen.generate()
        assert output.file_count == 4  # 1 tier1 + 3 tier2

    def test_all_files_includes_everything(self) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        output = gen.generate()
        all_files = output.all_files
        assert "CLAUDE.md" in all_files
        assert ".agents/api.md" in all_files

    def test_tier1_has_header(self) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        output = gen.generate()
        assert "# CLAUDE.md" in output.tier1_content

    def test_tier1_has_trigger_table(self) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        output = gen.generate()
        assert "## Context Files" in output.tier1_content
        assert "| Directory | Context File |" in output.tier1_content
        assert "| api/ | .agents/api.md |" in output.tier1_content
        assert "| db/ | .agents/db.md |" in output.tier1_content
        assert "| web/ | .agents/web.md |" in output.tier1_content

    def test_tier1_has_commands(self) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        output = gen.generate()
        assert "## Build, Test, and Lint Commands" in output.tier1_content

    def test_tier1_has_directory_structure(self) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        output = gen.generate()
        assert "## Directory Structure" in output.tier1_content

    def test_tier2_has_header(self) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        output = gen.generate()
        content = output.tier2_files[".agents/api.md"]
        assert "# api" in content
        assert "api/" in content

    def test_tier2_has_detected_stack(self) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        output = gen.generate()
        content = output.tier2_files[".agents/api.md"]
        assert "## Detected Stack" in content
        assert "Python" in content
        assert "FastAPI" in content
        assert "6" in content  # file_count

    def test_tier2_has_structured_sections(self) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        output = gen.generate()
        content = output.tier2_files[".agents/db.md"]
        assert "## Key Files" in content
        assert "## Test Conventions" in content
        assert "## Common Failure Modes" in content

    def test_tier2_no_frameworks_when_none(self) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        output = gen.generate()
        content = output.tier2_files[".agents/db.md"]
        assert "**Frameworks:**" not in content

    def test_write_creates_files(self, tmp_path: Path) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        written = gen.write(tmp_path)
        assert "CLAUDE.md" in written
        assert ".agents/api.md" in written
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / ".agents" / "api.md").exists()
        assert (tmp_path / ".agents" / "db.md").exists()
        assert (tmp_path / ".agents" / "web.md").exists()

    def test_write_respects_force(self, tmp_path: Path) -> None:
        gen = TieredGenerator(_make_analysis(), _make_subsystems())
        gen.write(tmp_path)
        # Without force, existing files should be skipped
        written = gen.write(tmp_path)
        assert written == []
        # With force, files should be rewritten
        written = gen.write(tmp_path, force=True)
        assert len(written) == 4


# ------------------------------------------------------------------
# CLI integration tests
# ------------------------------------------------------------------

class TestTieredCLI:
    def test_tiered_small_project_message(self, tmp_path: Path) -> None:
        """Small project should get a message to use regular generate."""
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")
        result = runner.invoke(app, ["generate", str(tmp_path), "--tiered"])
        assert result.exit_code == 0
        assert "small enough for single-file context" in result.output

    def test_tiered_large_project(self, tmp_path: Path) -> None:
        """Large project should generate tiered output."""
        _create_large_project(tmp_path)
        result = runner.invoke(app, ["generate", str(tmp_path), "--tiered", "--force"])
        assert result.exit_code == 0
        assert "Generated tiered context" in result.output
        assert "CLAUDE.md (Tier 1" in result.output
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / ".agents").is_dir()

    def test_tiered_dry_run(self, tmp_path: Path) -> None:
        """Dry run should show content without writing."""
        _create_large_project(tmp_path)
        result = runner.invoke(app, ["generate", str(tmp_path), "--tiered", "--dry-run"])
        assert result.exit_code == 0
        assert "[dry-run]" in result.output
        assert not (tmp_path / ".agents").exists()

    def test_tiered_no_overwrite_without_force(self, tmp_path: Path) -> None:
        """Existing files should not be overwritten without --force."""
        _create_large_project(tmp_path)
        (tmp_path / "CLAUDE.md").write_text("existing", encoding="utf-8")
        result = runner.invoke(app, ["generate", str(tmp_path), "--tiered"])
        assert "skip" in result.output

    def test_tiered_force_overwrites(self, tmp_path: Path) -> None:
        """Existing files should be overwritten with --force."""
        _create_large_project(tmp_path)
        (tmp_path / "CLAUDE.md").write_text("existing", encoding="utf-8")
        result = runner.invoke(app, ["generate", str(tmp_path), "--tiered", "--force"])
        assert result.exit_code == 0
        assert "Generated tiered context" in result.output
        content = (tmp_path / "CLAUDE.md").read_text()
        assert content != "existing"

    def test_tiered_summary_file_count(self, tmp_path: Path) -> None:
        """Summary should show total file count."""
        _create_large_project(tmp_path)
        result = runner.invoke(app, ["generate", str(tmp_path), "--tiered", "--force"])
        assert "context files total" in result.output


# ------------------------------------------------------------------
# End-to-end: full pipeline on mock project
# ------------------------------------------------------------------

class TestTieredEndToEnd:
    def test_full_pipeline(self, tmp_path: Path) -> None:
        """Full pipeline: detect subsystems → generate → verify files."""
        _create_large_project(tmp_path)

        # Step 1: detect
        assert not is_project_too_small(tmp_path)
        subsystems = detect_subsystems(tmp_path)
        assert len(subsystems) >= 2

        # Step 2: generate
        from agentmd.analyzer import ProjectAnalyzer
        analysis = ProjectAnalyzer().analyze(tmp_path)
        gen = TieredGenerator(analysis, subsystems)
        output = gen.generate()

        # Step 3: verify structure
        assert "CLAUDE.md" in output.all_files
        for s in subsystems:
            assert f".agents/{s.name}.md" in output.tier2_files

        # Step 4: verify tier1 content
        assert "## Context Files" in output.tier1_content
        for s in subsystems:
            assert s.path in output.tier1_content

        # Step 5: write and verify on disk
        gen.write(tmp_path, force=True)
        assert (tmp_path / "CLAUDE.md").exists()
        for s in subsystems:
            assert (tmp_path / ".agents" / f"{s.name}.md").exists()
