"""Tests for D1: subsystem boundary detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentmd.detectors.subsystem import (
    MIN_SOURCE_FILES,
    SubsystemInfo,
    detect_subsystems,
    is_project_too_small,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _create_files(tmp_path: Path, file_list: list[str]) -> None:
    """Create empty files at the given relative paths."""
    for f in file_list:
        p = tmp_path / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# line\n" * 200, encoding="utf-8")  # 200 lines each


def _create_small_files(tmp_path: Path, file_list: list[str]) -> None:
    """Create files with minimal content."""
    for f in file_list:
        p = tmp_path / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# small\n", encoding="utf-8")


# ------------------------------------------------------------------
# is_project_too_small
# ------------------------------------------------------------------

class TestIsProjectTooSmall:
    def test_empty_directory(self, tmp_path: Path) -> None:
        assert is_project_too_small(tmp_path) is True

    def test_few_source_files(self, tmp_path: Path) -> None:
        _create_files(tmp_path, ["src/a.py", "src/b.py"])
        assert is_project_too_small(tmp_path) is True

    def test_enough_files_but_few_lines(self, tmp_path: Path) -> None:
        files = [f"src/f{i}.py" for i in range(25)]
        for f in files:
            p = tmp_path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x = 1\n", encoding="utf-8")  # 1 line each = 25 lines
        assert is_project_too_small(tmp_path) is True

    def test_large_project(self, tmp_path: Path) -> None:
        files = [f"src/f{i}.py" for i in range(25)]
        _create_files(tmp_path, files)  # 25 files × 200 lines = 5000 lines
        assert is_project_too_small(tmp_path) is False

    def test_non_source_files_not_counted(self, tmp_path: Path) -> None:
        # 30 markdown files should not count as source
        _create_files(tmp_path, [f"docs/d{i}.md" for i in range(30)])
        assert is_project_too_small(tmp_path) is True

    def test_mixed_languages_count(self, tmp_path: Path) -> None:
        files = [f"src/f{i}.py" for i in range(10)] + [f"lib/f{i}.ts" for i in range(15)]
        _create_files(tmp_path, files)
        assert is_project_too_small(tmp_path) is False

    def test_accepts_precomputed_files(self, tmp_path: Path) -> None:
        files = [f"src/f{i}.py" for i in range(25)]
        _create_files(tmp_path, files)
        from agentmd.detectors.common import collect_project_files
        collected = collect_project_files(tmp_path)
        assert is_project_too_small(tmp_path, collected) is False


# ------------------------------------------------------------------
# detect_subsystems
# ------------------------------------------------------------------

class TestDetectSubsystems:
    def test_no_subsystems_in_small_project(self, tmp_path: Path) -> None:
        _create_files(tmp_path, ["a.py", "b.py"])
        result = detect_subsystems(tmp_path)
        assert result == []

    def test_single_directory_with_enough_files(self, tmp_path: Path) -> None:
        files = [f"api/handler{i}.py" for i in range(5)]
        _create_files(tmp_path, files)
        result = detect_subsystems(tmp_path)
        assert len(result) == 1
        assert result[0].name == "api"
        assert result[0].path == "api"
        assert result[0].file_count == 5
        assert "Python" in result[0].languages

    def test_multiple_subsystems(self, tmp_path: Path) -> None:
        files = (
            [f"api/h{i}.py" for i in range(4)]
            + [f"db/model{i}.py" for i in range(3)]
            + [f"web/page{i}.ts" for i in range(5)]
        )
        _create_files(tmp_path, files)
        result = detect_subsystems(tmp_path)
        names = {s.name for s in result}
        assert "api" in names
        assert "db" in names
        assert "web" in names

    def test_below_threshold_skipped(self, tmp_path: Path) -> None:
        files = [f"api/h{i}.py" for i in range(5)] + ["tiny/one.py", "tiny/two.py"]
        _create_files(tmp_path, files)
        result = detect_subsystems(tmp_path)
        names = {s.name for s in result}
        assert "api" in names
        assert "tiny" not in names

    def test_src_subdir_pattern(self, tmp_path: Path) -> None:
        """src/<subdir> should use subdir as the subsystem name."""
        files = [f"src/api/f{i}.py" for i in range(4)]
        _create_files(tmp_path, files)
        result = detect_subsystems(tmp_path)
        assert len(result) == 1
        assert result[0].name == "api"
        assert result[0].path == "src/api"

    def test_top_level_files_not_subsystem(self, tmp_path: Path) -> None:
        """Top-level files don't form subsystems."""
        _create_files(tmp_path, ["a.py", "b.py", "c.py", "d.py"])
        result = detect_subsystems(tmp_path)
        assert result == []

    def test_language_detection_typescript(self, tmp_path: Path) -> None:
        files = [f"frontend/comp{i}.tsx" for i in range(4)]
        _create_files(tmp_path, files)
        result = detect_subsystems(tmp_path)
        assert len(result) == 1
        assert "TypeScript" in result[0].languages

    def test_language_detection_go(self, tmp_path: Path) -> None:
        files = [f"server/handler{i}.go" for i in range(4)]
        _create_files(tmp_path, files)
        result = detect_subsystems(tmp_path)
        assert len(result) == 1
        assert "Go" in result[0].languages

    def test_language_detection_rust(self, tmp_path: Path) -> None:
        files = [f"engine/mod{i}.rs" for i in range(3)]
        _create_files(tmp_path, files)
        result = detect_subsystems(tmp_path)
        assert len(result) == 1
        assert "Rust" in result[0].languages

    def test_mixed_languages_in_subsystem(self, tmp_path: Path) -> None:
        files = [f"app/f{i}.py" for i in range(2)] + [f"app/g{i}.js" for i in range(2)]
        _create_files(tmp_path, files)
        result = detect_subsystems(tmp_path)
        assert len(result) == 1
        langs = result[0].languages
        assert "Python" in langs
        assert "JavaScript" in langs

    def test_monorepo_packages(self, tmp_path: Path) -> None:
        """Directories with package manifests should be considered."""
        files = (
            [f"packages/auth/src/f{i}.ts" for i in range(4)]
            + ["packages/auth/package.json"]
        )
        _create_files(tmp_path, files)
        result = detect_subsystems(tmp_path)
        # packages/auth should be detected as subsystem
        assert any(s.name == "auth" for s in result)

    def test_sorted_output(self, tmp_path: Path) -> None:
        files = (
            [f"zebra/f{i}.py" for i in range(3)]
            + [f"alpha/f{i}.py" for i in range(3)]
        )
        _create_files(tmp_path, files)
        result = detect_subsystems(tmp_path)
        names = [s.name for s in result]
        assert names == sorted(names)

    def test_accepts_precomputed_files(self, tmp_path: Path) -> None:
        files = [f"api/h{i}.py" for i in range(5)]
        _create_files(tmp_path, files)
        from agentmd.detectors.common import collect_project_files
        collected = collect_project_files(tmp_path)
        result = detect_subsystems(tmp_path, collected)
        assert len(result) == 1

    def test_subsystem_info_fields(self, tmp_path: Path) -> None:
        files = [f"core/mod{i}.py" for i in range(4)]
        _create_files(tmp_path, files)
        result = detect_subsystems(tmp_path)
        s = result[0]
        assert isinstance(s, SubsystemInfo)
        assert s.name == "core"
        assert s.path == "core"
        assert s.file_count == 4
        assert isinstance(s.languages, list)
        assert isinstance(s.frameworks, list)
