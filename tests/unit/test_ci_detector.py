from pathlib import Path

from agentmd.detectors.ci import detect_ci_systems
from agentmd.detectors.common import collect_project_files


def test_detect_ci_systems(tmp_path: Path) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    (tmp_path / ".gitlab-ci.yml").write_text("stages: [test]\n", encoding="utf-8")

    files = collect_project_files(tmp_path)
    result = detect_ci_systems(tmp_path, files)

    assert result.values == ["GitHub Actions", "GitLab CI"]
