"""Tests for D2 context file generators."""

from __future__ import annotations

import pytest

from agentmd.generators import (
    ClaudeGenerator,
    CodexGenerator,
    CopilotGenerator,
    CursorGenerator,
    GENERATOR_MAP,
)
from agentmd.types import DirectoryStructure, GitHistorySummary, ProjectAnalysis


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

def _make_python_analysis(root: str = "/tmp/proj") -> ProjectAnalysis:
    return ProjectAnalysis(
        root_path=root,
        languages=["Python"],
        package_managers=["pip"],
        frameworks=["FastAPI"],
        test_runners=["pytest"],
        linters=["ruff", "mypy"],
        ci_systems=["GitHub Actions"],
        directory_structure=DirectoryStructure(
            top_level_directories=["src", "tests"],
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


def _make_ts_analysis(root: str = "/tmp/tsproject") -> ProjectAnalysis:
    return ProjectAnalysis(
        root_path=root,
        languages=["TypeScript"],
        package_managers=["npm"],
        frameworks=["React"],
        test_runners=["jest"],
        linters=["eslint", "prettier"],
        ci_systems=["GitHub Actions"],
        directory_structure=DirectoryStructure(
            top_level_directories=["src", "tests"],
            source_directories=["src"],
            test_directories=["tests"],
        ),
        git_history=GitHistorySummary(
            commit_count=5,
            common_file_extensions=[".ts", ".tsx"],
            common_directories=["src"],
            common_message_prefixes=["feat"],
        ),
    )


def _make_empty_analysis(root: str = "/tmp/empty") -> ProjectAnalysis:
    return ProjectAnalysis(root_path=root)


# ------------------------------------------------------------------
# ClaudeGenerator tests
# ------------------------------------------------------------------

class TestClaudeGenerator:
    def test_generates_markdown(self):
        gen = ClaudeGenerator(_make_python_analysis())
        output = gen.generate()
        assert "# CLAUDE.md" in output
        assert output.endswith("\n")

    def test_output_filename(self):
        assert ClaudeGenerator.output_filename == "CLAUDE.md"

    def test_contains_slash_commands(self):
        output = ClaudeGenerator(_make_python_analysis()).generate()
        assert "/compact" in output
        assert "/review" in output
        assert "/init" in output

    def test_contains_detected_language(self):
        output = ClaudeGenerator(_make_python_analysis()).generate()
        assert "Python" in output

    def test_contains_test_command(self):
        output = ClaudeGenerator(_make_python_analysis()).generate()
        assert "pytest" in output

    def test_contains_lint_command(self):
        output = ClaudeGenerator(_make_python_analysis()).generate()
        assert "ruff" in output

    def test_contains_framework(self):
        output = ClaudeGenerator(_make_python_analysis()).generate()
        assert "FastAPI" in output

    def test_antipatterns_section(self):
        output = ClaudeGenerator(_make_python_analysis()).generate()
        assert "Anti-Patterns" in output

    def test_style_guide_section(self):
        output = ClaudeGenerator(_make_python_analysis()).generate()
        assert "Style Guide" in output

    def test_empty_analysis_still_valid(self):
        output = ClaudeGenerator(_make_empty_analysis()).generate()
        assert "# CLAUDE.md" in output
        assert output.endswith("\n")

    def test_typescript_antipatterns(self):
        output = ClaudeGenerator(_make_ts_analysis()).generate()
        assert "var" in output  # "Never use var" advice

    def test_mypy_appears_in_style_guide(self):
        output = ClaudeGenerator(_make_python_analysis()).generate()
        assert "mypy" in output


# ------------------------------------------------------------------
# CodexGenerator tests
# ------------------------------------------------------------------

class TestCodexGenerator:
    def test_generates_markdown(self):
        gen = CodexGenerator(_make_python_analysis())
        output = gen.generate()
        assert "# AGENTS.md" in output
        assert output.endswith("\n")

    def test_output_filename(self):
        assert CodexGenerator.output_filename == "AGENTS.md"

    def test_sandbox_section_present(self):
        output = CodexGenerator(_make_python_analysis()).generate()
        assert "Sandbox" in output
        assert "network" in output.lower()

    def test_apply_patch_section_present(self):
        output = CodexGenerator(_make_python_analysis()).generate()
        assert "apply_patch" in output

    def test_approval_gates_section_present(self):
        output = CodexGenerator(_make_python_analysis()).generate()
        assert "Approval Gates" in output
        assert "pytest" in output  # test command appears in checklist

    def test_contains_test_command(self):
        output = CodexGenerator(_make_python_analysis()).generate()
        assert "pytest tests/" in output

    def test_empty_analysis_still_valid(self):
        output = CodexGenerator(_make_empty_analysis()).generate()
        assert "# AGENTS.md" in output
        assert output.endswith("\n")

    def test_antipatterns_section(self):
        output = CodexGenerator(_make_python_analysis()).generate()
        assert "Anti-Patterns" in output


# ------------------------------------------------------------------
# CursorGenerator tests
# ------------------------------------------------------------------

class TestCursorGenerator:
    def test_generates_content(self):
        gen = CursorGenerator(_make_python_analysis())
        output = gen.generate()
        assert ".cursorrules" in output
        assert output.endswith("\n")

    def test_output_filename(self):
        assert CursorGenerator.output_filename == ".cursorrules"

    def test_always_section_present(self):
        output = CursorGenerator(_make_python_analysis()).generate()
        assert "## Always" in output

    def test_never_section_present(self):
        output = CursorGenerator(_make_python_analysis()).generate()
        assert "## Never" in output

    def test_always_contains_test_command(self):
        output = CursorGenerator(_make_python_analysis()).generate()
        assert "pytest" in output

    def test_file_patterns_section_present(self):
        output = CursorGenerator(_make_python_analysis()).generate()
        assert "File Patterns" in output
        assert ".py" in output

    def test_context_preferences_section_present(self):
        output = CursorGenerator(_make_python_analysis()).generate()
        assert "Context Preferences" in output

    def test_typescript_never_rules(self):
        output = CursorGenerator(_make_ts_analysis()).generate()
        assert "any" in output.lower()

    def test_empty_analysis_still_valid(self):
        output = CursorGenerator(_make_empty_analysis()).generate()
        assert ".cursorrules" in output
        assert output.endswith("\n")

    def test_framework_in_context_preferences(self):
        output = CursorGenerator(_make_python_analysis()).generate()
        assert "FastAPI" in output


# ------------------------------------------------------------------
# CopilotGenerator tests
# ------------------------------------------------------------------

class TestCopilotGenerator:
    def test_generates_markdown(self):
        gen = CopilotGenerator(_make_python_analysis())
        output = gen.generate()
        assert "Copilot" in output
        assert output.endswith("\n")

    def test_output_filename(self):
        assert CopilotGenerator.output_filename == "copilot-instructions.md"

    def test_coding_standards_section(self):
        output = CopilotGenerator(_make_python_analysis()).generate()
        assert "Coding Standards" in output

    def test_test_patterns_section(self):
        output = CopilotGenerator(_make_python_analysis()).generate()
        assert "Test Patterns" in output
        assert "pytest" in output

    def test_review_checklist_section(self):
        output = CopilotGenerator(_make_python_analysis()).generate()
        assert "PR Review Checklist" in output
        assert "- [ ]" in output

    def test_typescript_standards(self):
        output = CopilotGenerator(_make_ts_analysis()).generate()
        assert "TypeScript" in output
        assert "strict" in output.lower()

    def test_jest_test_patterns(self):
        output = CopilotGenerator(_make_ts_analysis()).generate()
        assert "jest" in output.lower() or "test.ts" in output

    def test_ruff_appears_in_standards(self):
        output = CopilotGenerator(_make_python_analysis()).generate()
        assert "ruff" in output

    def test_empty_analysis_still_valid(self):
        output = CopilotGenerator(_make_empty_analysis()).generate()
        assert "Copilot" in output
        assert output.endswith("\n")

    def test_lint_command_in_checklist(self):
        output = CopilotGenerator(_make_python_analysis()).generate()
        # ruff lint command should appear in review checklist
        assert "ruff check" in output


# ------------------------------------------------------------------
# GENERATOR_MAP / --target all path
# ------------------------------------------------------------------

class TestGeneratorMap:
    def test_all_four_generators_in_map(self):
        assert set(GENERATOR_MAP.keys()) == {"claude", "codex", "cursor", "copilot"}

    def test_all_generators_produce_output(self):
        analysis = _make_python_analysis()
        for name, GenClass in GENERATOR_MAP.items():
            gen = GenClass(analysis)
            output = gen.generate()
            assert isinstance(output, str), f"{name} generator returned non-string"
            assert len(output) > 100, f"{name} generator output too short"
            assert output.endswith("\n"), f"{name} generator output missing trailing newline"

    def test_all_generators_handle_empty_analysis(self):
        analysis = _make_empty_analysis()
        for name, GenClass in GENERATOR_MAP.items():
            gen = GenClass(analysis)
            output = gen.generate()
            assert isinstance(output, str), f"{name} generator returned non-string"
            assert output.endswith("\n"), f"{name} generator missing trailing newline on empty analysis"

    def test_output_filenames_are_set(self):
        for name, GenClass in GENERATOR_MAP.items():
            assert GenClass.output_filename, f"{name} generator missing output_filename"
