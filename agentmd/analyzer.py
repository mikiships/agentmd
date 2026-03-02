"""Project analysis engine."""

from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path

from agentmd.detectors import (
    detect_ci_systems,
    detect_frameworks,
    detect_languages,
    detect_linters,
    detect_package_managers,
    detect_rust_project,
    detect_swift_project,
    detect_test_runners,
)
from agentmd.detectors.common import collect_project_files, read_text, top_ranked
from agentmd.types import (
    DirectoryStructure,
    ExistingContextFile,
    GitHistorySummary,
    ProjectAnalysis,
)

CONTEXT_FILE_NAMES = ["CLAUDE.md", "AGENTS.md", ".cursorrules", "copilot-instructions.md"]

CONTEXT_MARKERS: dict[str, list[str]] = {
    "CLAUDE.md": ["/init", "/review", "/compact", "claude"],
    "AGENTS.md": ["sandbox", "approval", "codex", "apply_patch"],
    ".cursorrules": ["cursor", "rules", "always"],
    "copilot-instructions.md": ["copilot", "instruction", "github"],
}

SOURCE_DIR_CANDIDATES = {
    "src",
    "app",
    "apps",
    "lib",
    "libs",
    "services",
    "server",
    "client",
    "backend",
    "frontend",
    "pkg",
    "cmd",
}

TEST_DIR_CANDIDATES = {"tests", "test", "spec", "__tests__"}
MONOREPO_DIR_HINTS = {"packages", "apps", "services"}
MANIFEST_FILE_NAMES = {
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
}


class ProjectAnalyzer:
    """Analyze codebase structure, tools, and existing context files."""

    def __init__(self, max_git_commits: int = 100) -> None:
        self.max_git_commits = max_git_commits

    def analyze(self, path: str | Path = ".") -> ProjectAnalysis:
        """Run full project analysis for a path."""
        root = Path(path).resolve()
        files = collect_project_files(root)

        language_findings = detect_languages(root, files)
        package_manager_findings = detect_package_managers(root, files)
        framework_findings = detect_frameworks(root, files)
        test_runner_findings = detect_test_runners(root, files)
        linter_findings = detect_linters(root, files)
        ci_findings = detect_ci_systems(root, files)
        swift_findings = detect_swift_project(root, files)
        rust_findings = detect_rust_project(root, files)

        directory_structure = self._analyze_directory_structure(root, files)
        git_history = self._analyze_git_history(root)
        context_files = self._detect_existing_context_files(root)

        detection_reasons: dict[str, dict[str, list[str]]] = {
            "languages": language_findings.evidence,
            "package_managers": package_manager_findings.evidence,
            "frameworks": framework_findings.evidence,
            "test_runners": test_runner_findings.evidence,
            "linters": linter_findings.evidence,
            "ci_systems": ci_findings.evidence,
            "swift": swift_findings.evidence,
            "rust": rust_findings.evidence,
            "directory_structure": {
                "source_directories": directory_structure.source_directories,
                "test_directories": directory_structure.test_directories,
                "monorepo_indicators": directory_structure.monorepo_indicators,
            },
            "existing_context_files": {
                item.name: [item.path] for item in context_files if item.present
            },
        }

        return ProjectAnalysis(
            root_path=str(root),
            languages=language_findings.values,
            package_managers=package_manager_findings.values,
            frameworks=framework_findings.values,
            test_runners=test_runner_findings.values,
            linters=linter_findings.values,
            ci_systems=ci_findings.values,
            swift_components=swift_findings.values,
            rust_components=rust_findings.values,
            directory_structure=directory_structure,
            git_history=git_history,
            existing_context_files=context_files,
            detection_reasons=detection_reasons,
        )

    def _analyze_directory_structure(self, root: Path, files: list[Path]) -> DirectoryStructure:
        top_level_dirs = sorted({path.parts[0] for path in files if len(path.parts) > 1})
        top_level_files = sorted({path.name for path in files if len(path.parts) == 1})

        source_directories = sorted(
            {directory for directory in top_level_dirs if directory.lower() in SOURCE_DIR_CANDIDATES}
        )
        test_directories = sorted(
            {directory for directory in top_level_dirs if directory.lower() in TEST_DIR_CANDIDATES}
        )

        monorepo_indicators = self._monorepo_indicators(root, files)
        return DirectoryStructure(
            top_level_directories=top_level_dirs,
            top_level_files=top_level_files,
            source_directories=source_directories,
            test_directories=test_directories,
            is_monorepo=bool(monorepo_indicators),
            monorepo_indicators=monorepo_indicators,
        )

    def _monorepo_indicators(self, root: Path, files: list[Path]) -> list[str]:
        indicators: list[str] = []
        file_names = {path.name for path in files}

        if "pnpm-workspace.yaml" in file_names:
            indicators.append("pnpm workspace file present")

        package_json = root / "package.json"
        if package_json.exists():
            package_json_content = read_text(package_json, max_chars=25000)
            if "\"workspaces\"" in package_json_content:
                indicators.append("package.json defines workspaces")

        manifest_dirs = {
            path.parts[0]
            for path in files
            if path.name in MANIFEST_FILE_NAMES and len(path.parts) > 1
        }
        if len(manifest_dirs) > 1:
            indicators.append("multiple top-level directories contain package manifests")

        for hinted_dir in MONOREPO_DIR_HINTS:
            candidate = root / hinted_dir
            if not candidate.exists() or not candidate.is_dir():
                continue
            child_count = 0
            for child in candidate.iterdir():
                if not child.is_dir():
                    continue
                if any((child / manifest).exists() for manifest in MANIFEST_FILE_NAMES):
                    child_count += 1
            if child_count >= 2:
                indicators.append(f"{hinted_dir}/ has {child_count} package subprojects")

        return sorted(set(indicators))

    def _analyze_git_history(self, root: Path) -> GitHistorySummary:
        if not (root / ".git").exists():
            return GitHistorySummary()

        inside_git = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
            text=True,
        )
        if inside_git.returncode != 0 or inside_git.stdout.strip().lower() != "true":
            return GitHistorySummary()

        log_result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "log",
                f"-n{self.max_git_commits}",
                "--pretty=format:__COMMIT__%s",
                "--name-only",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if log_result.returncode != 0:
            return GitHistorySummary()

        extension_counter: Counter[str] = Counter()
        directory_counter: Counter[str] = Counter()
        message_prefix_counter: Counter[str] = Counter()
        commit_count = 0

        for line in log_result.stdout.splitlines():
            if not line:
                continue
            if line.startswith("__COMMIT__"):
                commit_count += 1
                message = line.replace("__COMMIT__", "", 1).strip()
                if not message:
                    continue
                if ":" in message:
                    prefix = message.split(":", 1)[0].strip().lower()
                else:
                    prefix = message.split()[0].strip().lower()
                if prefix:
                    message_prefix_counter[prefix] += 1
                continue

            changed_path = Path(line.strip())
            if changed_path.suffix:
                extension_counter[changed_path.suffix.lower()] += 1
            else:
                extension_counter["[no_ext]"] += 1
            if changed_path.parts:
                directory_counter[changed_path.parts[0]] += 1

        return GitHistorySummary(
            commit_count=commit_count,
            common_file_extensions=top_ranked(extension_counter),
            common_directories=top_ranked(directory_counter),
            common_message_prefixes=top_ranked(message_prefix_counter),
        )

    def _detect_existing_context_files(self, root: Path) -> list[ExistingContextFile]:
        records: list[ExistingContextFile] = []
        for file_name in CONTEXT_FILE_NAMES:
            full_path = root / file_name
            relative_path = file_name
            if not full_path.exists():
                records.append(
                    ExistingContextFile(name=file_name, path=relative_path, present=False)
                )
                continue

            content = read_text(full_path, max_chars=50000)
            lines = content.splitlines()
            first_heading = self._first_heading(lines)
            markers = self._detect_markers(file_name, content)
            records.append(
                ExistingContextFile(
                    name=file_name,
                    path=relative_path,
                    present=True,
                    line_count=len(lines),
                    first_heading=first_heading,
                    agent_markers=markers,
                )
            )
        return records

    @staticmethod
    def _first_heading(lines: list[str]) -> str | None:
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                return stripped
            return stripped[:120]
        return None

    @staticmethod
    def _detect_markers(file_name: str, content: str) -> list[str]:
        lowered = content.lower()
        markers = []
        for marker in CONTEXT_MARKERS.get(file_name, []):
            if marker.lower() in lowered:
                markers.append(marker)
        return sorted(set(markers))


def analyze_project(path: str | Path = ".") -> ProjectAnalysis:
    """Convenience wrapper for one-shot analysis."""
    return ProjectAnalyzer().analyze(path)
