"""Tests for --minimal mode (D1-D5)."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentmd.cli import app
from agentmd.generators import (
    ClaudeGenerator,
    CodexGenerator,
    CopilotGenerator,
    CursorGenerator,
    GENERATOR_MAP,
)
from agentmd.types import DirectoryStructure, GitHistorySummary, ProjectAnalysis

runner = CliRunner()


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

def _make_python_analysis() -> ProjectAnalysis:
    return ProjectAnalysis(
        root_path="/tmp/proj",
        languages=["Python"],
        package_managers=["pip"],
        frameworks=["FastAPI"],
        test_runners=["pytest"],
        linters=["ruff", "mypy"],
        ci_systems=["GitHub Actions"],
        directory_structure=DirectoryStructure(
            top_level_directories=["src", "tests", "docs"],
            top_level_files=["pyproject.toml", "README.md"],
            source_directories=["src"],
            test_directories=["tests"],
            is_monorepo=False,
        ),
        git_history=GitHistorySummary(
            commit_count=15,
            common_file_extensions=[".py"],
            common_directories=["src"],
            common_message_prefixes=["feat", "fix", "chore"],
        ),
    )


def _make_empty_analysis() -> ProjectAnalysis:
    return ProjectAnalysis(root_path="/tmp/empty")


def _make_multi_lang_analysis() -> ProjectAnalysis:
    return ProjectAnalysis(
        root_path="/tmp/multi",
        languages=["Python", "TypeScript"],
        package_managers=["pip", "npm"],
        frameworks=["FastAPI", "React"],
        test_runners=["pytest", "jest"],
        linters=["ruff", "eslint"],
        ci_systems=["GitHub Actions"],
        directory_structure=DirectoryStructure(
            top_level_directories=["src", "frontend", "tests"],
            source_directories=["src", "frontend/src"],
            test_directories=["tests", "frontend/tests"],
        ),
        git_history=GitHistorySummary(
            commit_count=30,
            common_file_extensions=[".py", ".ts"],
            common_directories=["src", "frontend"],
            common_message_prefixes=["feat", "fix"],
        ),
    )


def _make_project(tmp_path: Path) -> Path:
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
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')\n")
    (tmp_path / "tests" / "test_main.py").write_text("def test_main(): pass\n")
    return tmp_path


# ------------------------------------------------------------------
# D1: Minimal mode generator tests
# ------------------------------------------------------------------

class TestMinimalModeBase:
    """Test that minimal mode produces lean output from BaseGenerator."""

    def test_minimal_has_no_tips_section(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Claude Code Tips" not in output

    def test_minimal_has_no_style_guide(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Style Guide" not in output

    def test_minimal_has_no_antipatterns(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Anti-Patterns" not in output

    def test_minimal_has_commands_section(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Build, Test, and Lint Commands" in output

    def test_minimal_has_directory_structure(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Directory Structure" in output

    def test_minimal_directory_has_source_roots(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "`src`" in output

    def test_minimal_directory_has_test_roots(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "`tests`" in output

    def test_minimal_directory_no_top_level(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "Top-level directories" not in output

    def test_minimal_directory_no_most_changed(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "Most-changed" not in output

    def test_minimal_has_no_project_overview(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Project Overview" not in output

    def test_minimal_has_no_conventions(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Conventions" not in output

    def test_minimal_has_one_line_header(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        first_line = output.splitlines()[0]
        assert first_line == "# CLAUDE.md"

    def test_minimal_shorter_than_full(self):
        analysis = _make_python_analysis()
        full = ClaudeGenerator(analysis).generate()
        mini = ClaudeGenerator(analysis, minimal=True).generate()
        assert len(mini) < len(full)


class TestMinimalClaudeSpecific:
    """Claude minimal mode includes /compact tip."""

    def test_compact_tip_present(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "/compact" in output

    def test_no_review_tip(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "/review" not in output

    def test_no_init_tip(self):
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "/init" not in output


class TestMinimalCodex:
    """Codex minimal mode skips sandbox/apply-patch/approval/antipatterns."""

    def test_no_sandbox_section(self):
        gen = CodexGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Sandbox" not in output

    def test_no_apply_patch_section(self):
        gen = CodexGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "apply_patch" not in output

    def test_no_approval_gates(self):
        gen = CodexGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "Approval Gates" not in output

    def test_no_antipatterns(self):
        gen = CodexGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "Anti-Patterns" not in output

    def test_has_commands(self):
        gen = CodexGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "pytest" in output


class TestMinimalCursor:
    """Cursor minimal mode skips always/never/file-patterns/context-prefs."""

    def test_no_always_section(self):
        gen = CursorGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Always" not in output

    def test_no_never_section(self):
        gen = CursorGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Never" not in output

    def test_no_file_patterns(self):
        gen = CursorGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## File Patterns" not in output

    def test_no_context_preferences(self):
        gen = CursorGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Context Preferences" not in output


class TestMinimalCopilot:
    """Copilot minimal mode skips coding-standards/test-patterns/review-checklist."""

    def test_no_coding_standards(self):
        gen = CopilotGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Coding Standards" not in output

    def test_no_test_patterns(self):
        gen = CopilotGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## Test Patterns" not in output

    def test_no_review_checklist(self):
        gen = CopilotGenerator(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert "## PR Review Checklist" not in output


class TestMinimalAllGenerators:
    """Tests that apply to all generators in minimal mode."""

    @pytest.mark.parametrize("name,cls", list(GENERATOR_MAP.items()))
    def test_minimal_produces_valid_output(self, name, cls):
        gen = cls(_make_python_analysis(), minimal=True)
        output = gen.generate()
        assert isinstance(output, str)
        assert len(output) > 10
        assert output.endswith("\n")

    @pytest.mark.parametrize("name,cls", list(GENERATOR_MAP.items()))
    def test_minimal_handles_empty_analysis(self, name, cls):
        gen = cls(_make_empty_analysis(), minimal=True)
        output = gen.generate()
        assert isinstance(output, str)
        assert output.endswith("\n")

    @pytest.mark.parametrize("name,cls", list(GENERATOR_MAP.items()))
    def test_minimal_shorter_than_full(self, name, cls):
        analysis = _make_python_analysis()
        full = cls(analysis).generate()
        mini = cls(analysis, minimal=True).generate()
        assert len(mini) < len(full)


class TestMinimalMultiLanguage:
    """Edge case: minimal mode on multi-language project."""

    @pytest.mark.parametrize("name,cls", list(GENERATOR_MAP.items()))
    def test_multi_lang_minimal(self, name, cls):
        gen = cls(_make_multi_lang_analysis(), minimal=True)
        output = gen.generate()
        assert "## Build, Test, and Lint Commands" in output
        assert output.endswith("\n")


# ------------------------------------------------------------------
# D1: CLI tests
# ------------------------------------------------------------------

class TestMinimalCLI:
    def test_generate_minimal_flag(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", "--minimal", "--agent", "claude", str(tmp_path)])
        assert result.exit_code == 0
        content = (tmp_path / "CLAUDE.md").read_text()
        assert "## Build, Test, and Lint Commands" in content
        assert "## Style Guide" not in content

    def test_generate_minimal_short_flag(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", "-m", "--agent", "claude", str(tmp_path)])
        assert result.exit_code == 0

    def test_generate_minimal_all_agents(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["generate", "--minimal", str(tmp_path)])
        assert result.exit_code == 0
        for cls in GENERATOR_MAP.values():
            gen = cls.__new__(cls)
            assert (tmp_path / gen.output_filename).exists()


# ------------------------------------------------------------------
# D2: Minimal on diff and drift
# ------------------------------------------------------------------

class TestMinimalDiff:
    def test_diff_minimal_flag(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(app, ["diff", "--minimal", "--agent", "claude", str(tmp_path)])
        assert result.exit_code == 0

    def test_diff_minimal_against_existing_full(self, tmp_path):
        _make_project(tmp_path)
        # Generate full file first
        runner.invoke(app, ["generate", "--agent", "claude", str(tmp_path)])
        # Diff with minimal should show changes (minimal != full)
        result = runner.invoke(app, ["diff", "--minimal", "--agent", "claude", str(tmp_path)])
        assert result.exit_code == 0
        assert "---" in result.output or "+++" in result.output


class TestMinimalDrift:
    def test_drift_minimal_flag(self, tmp_path):
        _make_project(tmp_path)
        # Generate minimal, then check drift with minimal — should be fresh
        runner.invoke(app, ["generate", "--minimal", "--agent", "claude", str(tmp_path)])
        result = runner.invoke(app, ["drift", "--minimal", "--agent", "claude", str(tmp_path)])
        assert result.exit_code == 0
        assert "fresh" in result.output

    def test_drift_minimal_detects_stale(self, tmp_path):
        _make_project(tmp_path)
        runner.invoke(app, ["generate", "--minimal", "--agent", "claude", str(tmp_path)])
        (tmp_path / "CLAUDE.md").write_text("# CLAUDE.md\nold content\n")
        result = runner.invoke(app, ["drift", "--minimal", "--agent", "claude", str(tmp_path)])
        assert result.exit_code == 1


# ------------------------------------------------------------------
# D3: JSON output includes mode field
# ------------------------------------------------------------------

class TestMinimalJSON:
    def test_generate_json_minimal_has_mode(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(
            app, ["generate", "--json", "--minimal", "--agent", "claude", str(tmp_path)]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["mode"] == "minimal"

    def test_generate_json_no_minimal_no_mode(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(
            app, ["generate", "--json", "--agent", "claude", str(tmp_path)]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "mode" not in data

    def test_generate_json_minimal_roundtrip(self, tmp_path):
        _make_project(tmp_path)
        result = runner.invoke(
            app, ["generate", "--json", "--minimal", str(tmp_path)]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "contents" in data
        assert "mode" in data
        for agent_name, content in data["contents"].items():
            assert isinstance(content, str)
            assert len(content) > 0


# ------------------------------------------------------------------
# D4: Scorer adjustments for minimal files
# ------------------------------------------------------------------

class TestMinimalScorer:
    def test_scorer_minimal_completeness(self):
        from agentmd.scorer import ContextScorer
        gen = ClaudeGenerator(_make_python_analysis(), minimal=True)
        content = gen.generate()
        scorer = ContextScorer()
        result = scorer.score(content, minimal=True)
        completeness = next(d for d in result.dimensions if d.name == "completeness")
        # Minimal files should not be penalized heavily for missing sections
        assert completeness.score >= 60

    def test_scorer_minimal_agent_awareness_full_marks(self):
        from agentmd.scorer import ContextScorer
        gen = CodexGenerator(_make_python_analysis(), minimal=True)
        content = gen.generate()
        scorer = ContextScorer()
        result = scorer.score(content, minimal=True)
        agent_dim = next(d for d in result.dimensions if d.name == "agent_awareness")
        assert agent_dim.score == 100.0

    def test_scorer_non_minimal_unchanged(self):
        from agentmd.scorer import ContextScorer
        gen = ClaudeGenerator(_make_python_analysis())
        content = gen.generate()
        scorer = ContextScorer()
        result_default = scorer.score(content)
        result_explicit = scorer.score(content, minimal=False)
        assert result_default.composite_score == result_explicit.composite_score

    def test_scorer_minimal_all_generators(self):
        from agentmd.scorer import ContextScorer
        scorer = ContextScorer()
        for name, cls in GENERATOR_MAP.items():
            gen = cls(_make_python_analysis(), minimal=True)
            content = gen.generate()
            result = scorer.score(content, minimal=True)
            assert result.composite_score > 0, f"{name} minimal scored 0"
