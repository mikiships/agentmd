from pathlib import Path

from agentmd.detectors.common import collect_project_files
from agentmd.detectors.package_manager import detect_package_managers


def test_detect_package_managers(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "uv.lock").write_text("", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "Cargo.toml").write_text("[package]\nname='x'\n", encoding="utf-8")
    (tmp_path / "go.mod").write_text("module example\n", encoding="utf-8")
    (tmp_path / "Gemfile").write_text("source 'https://rubygems.org'\n", encoding="utf-8")
    (tmp_path / "pom.xml").write_text("<project/>\n", encoding="utf-8")
    (tmp_path / "build.gradle").write_text("plugins {}\n", encoding="utf-8")

    files = collect_project_files(tmp_path)
    result = detect_package_managers(tmp_path, files)

    assert "uv" in result.values
    assert "pip" in result.values
    assert "npm" in result.values
    assert "cargo" in result.values
    assert "go mod" in result.values
    assert "bundler" in result.values
    assert "maven" in result.values
    assert "gradle" in result.values
