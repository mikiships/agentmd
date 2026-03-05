"""Drift detection between existing and freshly generated context files."""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from agentmd.analyzer import ProjectAnalyzer
from agentmd.generators import BaseGenerator, GENERATOR_MAP

DRIFT_REPORT_SCHEMA: dict[str, object] = {
    "name": "agentmd.drift.report",
    "version": "1.0.0",
}


@dataclass
class SectionStaleDetail:
    """Detailed stale section report."""

    section: str
    status: Literal["added", "changed", "removed"]
    existing_line_count: int
    generated_line_count: int
    diff: str

    def to_dict(self) -> dict[str, object]:
        return {
            "section": self.section,
            "status": self.status,
            "existing_line_count": self.existing_line_count,
            "generated_line_count": self.generated_line_count,
            "diff": self.diff,
        }


@dataclass
class FileDriftReport:
    """Drift report for a single generated context file."""

    agent: str
    file: str
    status: Literal["fresh", "stale", "missing"]
    has_drift: bool
    sections_added: list[str] = field(default_factory=list)
    sections_removed: list[str] = field(default_factory=list)
    sections_changed: list[str] = field(default_factory=list)
    sections_fresh: list[str] = field(default_factory=list)
    sections_stale: list[str] = field(default_factory=list)
    stale_details: list[SectionStaleDetail] = field(default_factory=list)
    diff: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "agent": self.agent,
            "file": self.file,
            "status": self.status,
            "has_drift": self.has_drift,
            "sections_added": self.sections_added,
            "sections_removed": self.sections_removed,
            "sections_changed": self.sections_changed,
            "sections_fresh": self.sections_fresh,
            "sections_stale": self.sections_stale,
            "stale_details": [item.to_dict() for item in self.stale_details],
            "summary": {
                "added": len(self.sections_added),
                "removed": len(self.sections_removed),
                "changed": len(self.sections_changed),
                "fresh": len(self.sections_fresh),
                "stale": len(self.sections_stale),
            },
            "diff": self.diff,
        }


@dataclass
class DriftReport:
    """Drift report across all context files for selected generators."""

    root_path: str
    has_drift: bool
    files: list[FileDriftReport]

    def to_dict(self) -> dict[str, object]:
        total_added = sum(len(item.sections_added) for item in self.files)
        total_removed = sum(len(item.sections_removed) for item in self.files)
        total_changed = sum(len(item.sections_changed) for item in self.files)
        total_stale = sum(len(item.sections_stale) for item in self.files)
        return {
            "schema": DRIFT_REPORT_SCHEMA,
            "root_path": self.root_path,
            "has_drift": self.has_drift,
            "summary": {
                "files": len(self.files),
                "files_with_drift": sum(1 for item in self.files if item.has_drift),
                "sections_added": total_added,
                "sections_removed": total_removed,
                "sections_changed": total_changed,
                "sections_stale": total_stale,
            },
            "files": [item.to_dict() for item in self.files],
        }


def detect_drift(
    root: Path,
    agents: dict[str, type[BaseGenerator]],
    *,
    minimal: bool = False,
) -> DriftReport:
    """Generate fresh context and compare with checked-in versions."""
    analysis = ProjectAnalyzer().analyze(root)
    file_reports: list[FileDriftReport] = []

    for agent_name, generator_cls in agents.items():
        generator = generator_cls(analysis, minimal=minimal)
        output_path = root / generator.output_filename

        generated_content = generator.generate()
        file_exists = output_path.exists()
        existing_content = output_path.read_text(encoding="utf-8") if file_exists else ""

        has_drift = existing_content != generated_content
        sections = compare_sections(existing_content, generated_content)

        file_reports.append(
            FileDriftReport(
                agent=agent_name,
                file=generator.output_filename,
                status=_file_status(file_exists=file_exists, has_drift=has_drift),
                has_drift=has_drift,
                sections_added=sections["sections_added"],
                sections_removed=sections["sections_removed"],
                sections_changed=sections["sections_changed"],
                sections_fresh=sections["sections_fresh"],
                sections_stale=sections["sections_stale"],
                stale_details=sections["stale_details"],
                diff=build_file_diff(
                    file_name=generator.output_filename,
                    existing=existing_content,
                    generated=generated_content,
                    file_exists=file_exists,
                )
                if has_drift
                else None,
            )
        )

    return DriftReport(
        root_path=str(root),
        has_drift=any(item.has_drift for item in file_reports),
        files=file_reports,
    )


def compare_sections(existing: str, generated: str) -> dict[str, object]:
    """Compare markdown sections between existing and generated context content."""
    existing_sections = split_markdown_sections(existing)
    generated_sections = split_markdown_sections(generated)

    existing_names = set(existing_sections)
    generated_names = set(generated_sections)
    common_names = existing_names & generated_names

    sections_added = sorted(generated_names - existing_names)
    sections_removed = sorted(existing_names - generated_names)
    sections_changed = sorted(
        name
        for name in common_names
        if _normalize_section(existing_sections[name]) != _normalize_section(generated_sections[name])
    )
    sections_fresh = sorted(common_names - set(sections_changed))

    stale_details: list[SectionStaleDetail] = []
    for name in sections_added:
        stale_details.append(
            _section_detail(
                section=name,
                status="added",
                existing="",
                generated=generated_sections[name],
            )
        )
    for name in sections_changed:
        stale_details.append(
            _section_detail(
                section=name,
                status="changed",
                existing=existing_sections[name],
                generated=generated_sections[name],
            )
        )
    for name in sections_removed:
        stale_details.append(
            _section_detail(
                section=name,
                status="removed",
                existing=existing_sections[name],
                generated="",
            )
        )

    sections_stale = sorted(set(sections_changed) | set(sections_removed))
    return {
        "sections_added": sections_added,
        "sections_removed": sections_removed,
        "sections_changed": sections_changed,
        "sections_fresh": sections_fresh,
        "sections_stale": sections_stale,
        "stale_details": stale_details,
    }


def split_markdown_sections(markdown: str) -> dict[str, str]:
    """Return section name -> body, using markdown headings as boundaries."""
    sections: dict[str, str] = {}
    current_title: str | None = None
    current_lines: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("# "):
            # Ignore document title for section comparisons.
            continue

        if line.startswith("## "):
            if current_title is not None:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = line[3:].strip()
            current_lines = []
            continue

        if current_title is not None:
            current_lines.append(line)

    if current_title is not None:
        sections[current_title] = "\n".join(current_lines).strip()

    if sections:
        return sections

    # Fallback for non-markdown context files.
    content = markdown.strip()
    if content:
        return {"full_document": content}
    return {}


def build_file_diff(file_name: str, existing: str, generated: str, file_exists: bool) -> str:
    """Build a unified diff for the full context file."""
    from_label = file_name if file_exists else f"{file_name} (missing)"
    to_label = f"{file_name} (generated)"
    return "".join(
        difflib.unified_diff(
            existing.splitlines(keepends=True),
            generated.splitlines(keepends=True),
            fromfile=from_label,
            tofile=to_label,
        )
    )


def render_text_report(report: DriftReport) -> str:
    """Render human-readable drift summary."""
    lines: list[str] = []
    if report.has_drift:
        lines.append("Context drift detected.")
    else:
        lines.append("Context files are fresh.")

    for file_report in report.files:
        lines.append(f"{file_report.file}: {file_report.status}")
        if not file_report.has_drift:
            continue

        lines.append(
            "  added={added} removed={removed} changed={changed} stale={stale}".format(
                added=len(file_report.sections_added),
                removed=len(file_report.sections_removed),
                changed=len(file_report.sections_changed),
                stale=len(file_report.sections_stale),
            )
        )

        if file_report.sections_added:
            lines.append(f"  sections_added: {', '.join(file_report.sections_added)}")
        if file_report.sections_removed:
            lines.append(f"  sections_removed: {', '.join(file_report.sections_removed)}")
        if file_report.sections_changed:
            lines.append(f"  sections_changed: {', '.join(file_report.sections_changed)}")
        if file_report.sections_stale:
            lines.append(f"  sections_stale: {', '.join(file_report.sections_stale)}")

    return "\n".join(lines)


def render_github_annotations(report: DriftReport) -> str:
    """Render drift as GitHub workflow command annotations."""
    lines: list[str] = []
    if not report.has_drift:
        lines.append("::notice title=agentmd drift::No context drift detected")
        return "\n".join(lines)

    for file_report in report.files:
        if not file_report.has_drift:
            lines.append(
                "::notice file={file},title=agentmd drift::fresh".format(
                    file=_escape_github_field(file_report.file)
                )
            )
            continue

        summary = (
            f"status={file_report.status}, "
            f"added={len(file_report.sections_added)}, "
            f"removed={len(file_report.sections_removed)}, "
            f"changed={len(file_report.sections_changed)}, "
            f"stale={len(file_report.sections_stale)}"
        )
        lines.append(
            "::warning file={file},title=agentmd drift::{summary}".format(
                file=_escape_github_field(file_report.file),
                summary=_escape_github_message(summary),
            )
        )

        for detail in file_report.stale_details:
            message = f"{detail.section}: {detail.status}"
            lines.append(
                "::warning file={file},title=agentmd section::{message}".format(
                    file=_escape_github_field(file_report.file),
                    message=_escape_github_message(message),
                )
            )

    return "\n".join(lines)


def _file_status(*, file_exists: bool, has_drift: bool) -> Literal["fresh", "stale", "missing"]:
    if not file_exists:
        return "missing"
    if has_drift:
        return "stale"
    return "fresh"


def _normalize_section(section: str) -> str:
    lines = [line.rstrip() for line in section.strip().splitlines()]
    return "\n".join(lines)


def _section_detail(
    section: str,
    status: Literal["added", "changed", "removed"],
    existing: str,
    generated: str,
) -> SectionStaleDetail:
    section_diff = "".join(
        difflib.unified_diff(
            existing.splitlines(keepends=True),
            generated.splitlines(keepends=True),
            fromfile=f"{section} (existing)",
            tofile=f"{section} (generated)",
        )
    )
    return SectionStaleDetail(
        section=section,
        status=status,
        existing_line_count=len(existing.splitlines()),
        generated_line_count=len(generated.splitlines()),
        diff=section_diff,
    )


def _escape_github_field(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_github_message(value: str) -> str:
    return (
        value.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
    )


def select_generators(agent: str | None) -> dict[str, type[BaseGenerator]]:
    """Select one generator or all generators, preserving deterministic order."""
    if agent:
        return {agent: GENERATOR_MAP[agent]}
    return dict(GENERATOR_MAP)
