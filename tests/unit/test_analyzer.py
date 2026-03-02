from __future__ import annotations

import subprocess
from pathlib import Path

from agentmd.analyzer import analyze_project


def _git(cmd: list[str], cwd: Path) -> None:
    subprocess.run(["git", *cmd], cwd=cwd, check=True, capture_output=True)


def test_analyze_project_includes_structure_git_and_context_files(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    (tmp_path / "packages" / "pkg1").mkdir(parents=True)
    (tmp_path / "packages" / "pkg2").mkdir(parents=True)
    (tmp_path / "packages" / "pkg1" / "package.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "packages" / "pkg2" / "package.json").write_text("{}\n", encoding="utf-8")

    (tmp_path / "CLAUDE.md").write_text("# Claude Context\nUse /init\n", encoding="utf-8")
    (tmp_path / ".cursorrules").write_text("Always run tests\n", encoding="utf-8")

    _git(["init"], cwd=tmp_path)
    _git(["config", "user.name", "Test User"], cwd=tmp_path)
    _git(["config", "user.email", "test@example.com"], cwd=tmp_path)
    _git(["add", "."], cwd=tmp_path)
    _git(["commit", "-m", "feat: initial"], cwd=tmp_path)

    (tmp_path / "src" / "main.py").write_text("print('updated')\n", encoding="utf-8")
    _git(["add", "src/main.py"], cwd=tmp_path)
    _git(["commit", "-m", "fix: update main"], cwd=tmp_path)

    analysis = analyze_project(tmp_path)

    assert analysis.languages
    assert analysis.directory_structure.is_monorepo is True
    assert analysis.git_history.commit_count >= 2
    assert ".py" in analysis.git_history.common_file_extensions

    context_files = {item.name: item for item in analysis.existing_context_files}
    assert context_files["CLAUDE.md"].present is True
    assert "/init" in context_files["CLAUDE.md"].agent_markers
    assert context_files["AGENTS.md"].present is False
