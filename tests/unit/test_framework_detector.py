import json
from pathlib import Path

from agentmd.detectors.common import collect_project_files
from agentmd.detectors.framework import detect_frameworks


def test_detect_frameworks(tmp_path: Path) -> None:
    package_json = {
        "dependencies": {
            "express": "^4.0.0",
            "next": "^14.0.0",
            "react": "^18.0.0",
            "vue": "^3.0.0",
        }
    }
    (tmp_path / "package.json").write_text(json.dumps(package_json), encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\ndependencies=['fastapi','flask','django']\n", encoding="utf-8")
    (tmp_path / "Cargo.toml").write_text("[dependencies]\nactix-web='4'\n", encoding="utf-8")
    (tmp_path / "main.go").write_text("import \"github.com/gin-gonic/gin\"\n", encoding="utf-8")
    (tmp_path / "Gemfile").write_text("gem 'rails'\n", encoding="utf-8")

    files = collect_project_files(tmp_path)
    result = detect_frameworks(tmp_path, files)

    assert "FastAPI" in result.values
    assert "Flask" in result.values
    assert "Django" in result.values
    assert "Express" in result.values
    assert "Next.js" in result.values
    assert "React" in result.values
    assert "Vue" in result.values
    assert "actix-web" in result.values
    assert "gin" in result.values
    assert "Rails" in result.values
