"""Additional matrix tests for markdown drift formatter output."""

from __future__ import annotations

import pytest

from agentmd.drift import DriftReport, FileDriftReport, SectionStaleDetail
from agentmd.formatters import render_markdown_report


def _single_file_report(*, added: int = 0, removed: int = 0, changed: int = 0) -> DriftReport:
    sections_added = [f"Added {i}" for i in range(added)]
    sections_removed = [f"Removed {i}" for i in range(removed)]
    sections_changed = [f"Changed {i}" for i in range(changed)]

    details: list[SectionStaleDetail] = []
    for section in sections_added:
        details.append(
            SectionStaleDetail(
                section=section,
                status="added",
                existing_line_count=0,
                generated_line_count=1,
                diff=f"--- {section} (existing)\n+++ {section} (generated)\n+new\n",
            )
        )
    for section in sections_changed:
        details.append(
            SectionStaleDetail(
                section=section,
                status="changed",
                existing_line_count=1,
                generated_line_count=1,
                diff=f"--- {section} (existing)\n+++ {section} (generated)\n-old\n+new\n",
            )
        )
    for section in sections_removed:
        details.append(
            SectionStaleDetail(
                section=section,
                status="removed",
                existing_line_count=1,
                generated_line_count=0,
                diff=f"--- {section} (existing)\n+++ {section} (generated)\n-old\n",
            )
        )

    has_drift = bool(sections_added or sections_removed or sections_changed)
    file_report = FileDriftReport(
        agent="claude",
        file="CLAUDE.md",
        status="stale" if has_drift else "fresh",
        has_drift=has_drift,
        sections_added=sections_added,
        sections_removed=sections_removed,
        sections_changed=sections_changed,
        sections_fresh=[] if has_drift else ["Overview"],
        sections_stale=sorted(sections_changed + sections_removed),
        stale_details=details,
        diff="diff" if has_drift else None,
    )

    return DriftReport(root_path="/tmp/demo", has_drift=has_drift, files=[file_report])


@pytest.mark.parametrize(
    ("added", "removed", "changed", "expected"),
    [
        (1, 0, 0, "⚠️ 1 section drifted in CLAUDE.md"),
        (0, 1, 0, "⚠️ 1 section drifted in CLAUDE.md"),
        (0, 0, 1, "⚠️ 1 section drifted in CLAUDE.md"),
        (1, 1, 0, "⚠️ 2 sections drifted in CLAUDE.md"),
        (2, 1, 1, "⚠️ 4 sections drifted in CLAUDE.md"),
        (0, 0, 0, "✅ Context files are fresh"),
    ],
)
def test_markdown_summary_single_file_variants(
    added: int,
    removed: int,
    changed: int,
    expected: str,
) -> None:
    output = render_markdown_report(_single_file_report(added=added, removed=removed, changed=changed))
    assert expected in output


@pytest.mark.parametrize(
    "drifting_files",
    [2, 3, 4, 5, 6],
)
def test_markdown_summary_multi_file_uses_across_phrase(drifting_files: int) -> None:
    files: list[FileDriftReport] = []
    for index in range(drifting_files):
        files.append(
            FileDriftReport(
                agent="claude",
                file=f"CLAUDE-{index}.md",
                status="stale",
                has_drift=True,
                sections_changed=["Overview"],
                sections_stale=["Overview"],
                stale_details=[
                    SectionStaleDetail(
                        section="Overview",
                        status="changed",
                        existing_line_count=1,
                        generated_line_count=1,
                        diff="--- Overview (existing)\n+++ Overview (generated)\n-old\n+new\n",
                    )
                ],
                diff="diff",
            )
        )

    report = DriftReport(root_path="/tmp/demo", has_drift=True, files=files)
    output = render_markdown_report(report)

    assert f"across {drifting_files} files" in output
    assert f"⚠️ {drifting_files} sections drifted" in output


@pytest.mark.parametrize(
    ("status", "expected_row_status"),
    [
        ("changed", "stale"),
        ("removed", "missing"),
        ("added", "new"),
    ],
)
def test_markdown_detail_status_mapping(status: str, expected_row_status: str) -> None:
    detail = SectionStaleDetail(
        section="Overview",
        status=status,
        existing_line_count=1,
        generated_line_count=1,
        diff="--- Overview (existing)\n+++ Overview (generated)\n-old\n+new\n",
    )
    file_report = FileDriftReport(
        agent="claude",
        file="CLAUDE.md",
        status="stale",
        has_drift=True,
        sections_changed=["Overview"] if status == "changed" else [],
        sections_removed=["Overview"] if status == "removed" else [],
        sections_added=["Overview"] if status == "added" else [],
        sections_stale=["Overview"] if status != "added" else [],
        stale_details=[detail],
        diff="diff",
    )
    output = render_markdown_report(DriftReport(root_path="/tmp/demo", has_drift=True, files=[file_report]))

    assert f"({expected_row_status})" in output


@pytest.mark.parametrize(
    "section_name",
    [
        "Overview",
        "Commands",
        "Code Style",
        "Testing",
        "CI",
        "Release",
        "Troubleshooting",
    ],
)
def test_markdown_table_includes_file_prefix_for_each_section(section_name: str) -> None:
    file_report = FileDriftReport(
        agent="claude",
        file="CLAUDE.md",
        status="fresh",
        has_drift=False,
        sections_fresh=[section_name],
    )
    output = render_markdown_report(DriftReport(root_path="/tmp/demo", has_drift=False, files=[file_report]))
    assert f"| CLAUDE.md :: {section_name} | fresh |" in output
