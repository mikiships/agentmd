"""Data models used by agentmd."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class DetectorFindings:
    """Generic detector output with evidence per detected value."""

    values: list[str] = field(default_factory=list)
    evidence: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class DirectoryStructure:
    """High-level project layout details."""

    top_level_directories: list[str] = field(default_factory=list)
    top_level_files: list[str] = field(default_factory=list)
    source_directories: list[str] = field(default_factory=list)
    test_directories: list[str] = field(default_factory=list)
    is_monorepo: bool = False
    monorepo_indicators: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class GitHistorySummary:
    """Summarized commit history signals."""

    commit_count: int = 0
    common_file_extensions: list[str] = field(default_factory=list)
    common_directories: list[str] = field(default_factory=list)
    common_message_prefixes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class ExistingContextFile:
    """Metadata for a detected context file."""

    name: str
    path: str
    present: bool
    line_count: int = 0
    first_heading: str | None = None
    agent_markers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class ProjectAnalysis:
    """Full analyzer output."""

    root_path: str
    languages: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    test_runners: list[str] = field(default_factory=list)
    linters: list[str] = field(default_factory=list)
    ci_systems: list[str] = field(default_factory=list)
    swift_components: list[str] = field(default_factory=list)
    rust_components: list[str] = field(default_factory=list)
    directory_structure: DirectoryStructure = field(default_factory=DirectoryStructure)
    git_history: GitHistorySummary = field(default_factory=GitHistorySummary)
    existing_context_files: list[ExistingContextFile] = field(default_factory=list)
    detection_reasons: dict[str, dict[str, list[str]]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "root_path": self.root_path,
            "languages": self.languages,
            "package_managers": self.package_managers,
            "frameworks": self.frameworks,
            "test_runners": self.test_runners,
            "linters": self.linters,
            "ci_systems": self.ci_systems,
            "swift_components": self.swift_components,
            "rust_components": self.rust_components,
            "directory_structure": self.directory_structure.to_dict(),
            "git_history": self.git_history.to_dict(),
            "existing_context_files": [item.to_dict() for item in self.existing_context_files],
            "detection_reasons": self.detection_reasons,
        }
