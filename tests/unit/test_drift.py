"""Unit tests for drift detection internals."""

from __future__ import annotations

from pathlib import Path

from agentmd.drift import (
    DriftReport,
    build_file_diff,
    compare_sections,
    detect_drift,
    render_github_annotations,
    split_markdown_sections,
    select_generators,
)


def _make_project(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\nversion='0.1.0'\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    return tmp_path


def test_split_markdown_sections_uses_h2_headings() -> None:
    content = (
        "# Title\n\n"
        "## Project Overview\n"
        "One\n\n"
        "## Commands\n"
        "Two\n"
    )
    sections = split_markdown_sections(content)
    assert set(sections) == {"Project Overview", "Commands"}
    assert sections["Project Overview"] == "One"
    assert sections["Commands"] == "Two"


def test_compare_sections_reports_added_removed_changed_and_stale() -> None:
    existing = (
        "## Overview\n"
        "old\n\n"
        "## Removed Section\n"
        "bye\n"
    )
    generated = (
        "## Overview\n"
        "new\n\n"
        "## Added Section\n"
        "hi\n"
    )
    result = compare_sections(existing, generated)

    assert result["sections_added"] == ["Added Section"]
    assert result["sections_removed"] == ["Removed Section"]
    assert result["sections_changed"] == ["Overview"]
    assert sorted(result["sections_stale"]) == ["Overview", "Removed Section"]
    assert len(result["stale_details"]) == 2


def test_detect_drift_reports_missing_context_file(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    report = detect_drift(root, select_generators("claude"))
    assert report.has_drift is True
    assert len(report.files) == 1
    file_report = report.files[0]
    assert file_report.status == "missing"
    assert "Project Overview" in file_report.sections_added


def test_render_github_annotations_contains_workflow_commands() -> None:
    lines = render_github_annotations(DriftReport(root_path="/tmp/demo", has_drift=False, files=[]))
    assert lines.startswith("::notice")


def test_build_file_diff_contains_unified_markers() -> None:
    diff = build_file_diff(
        file_name="CLAUDE.md",
        existing="old\n",
        generated="new\n",
        file_exists=True,
    )
    assert "--- CLAUDE.md" in diff
    assert "+++ CLAUDE.md (generated)" in diff
