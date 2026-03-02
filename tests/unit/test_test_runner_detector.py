import json
from pathlib import Path

from agentmd.detectors.common import collect_project_files
from agentmd.detectors.test_runner import detect_test_runners


def test_detect_test_runners(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_example.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    package_json = {"devDependencies": {"jest": "^29", "vitest": "^2"}}
    (tmp_path / "package.json").write_text(json.dumps(package_json), encoding="utf-8")

    (tmp_path / "Cargo.toml").write_text("[package]\nname='x'\n", encoding="utf-8")
    (tmp_path / "go.mod").write_text("module x\n", encoding="utf-8")
    (tmp_path / "main_test.go").write_text("package main\n", encoding="utf-8")

    (tmp_path / "spec").mkdir()
    (tmp_path / "spec" / "app_spec.rb").write_text("describe 'x' do end\n", encoding="utf-8")

    (tmp_path / "pom.xml").write_text("<project/>\n", encoding="utf-8")
    junit_path = tmp_path / "src" / "test" / "java"
    junit_path.mkdir(parents=True)
    (junit_path / "AppTest.java").write_text("class AppTest {}\n", encoding="utf-8")

    files = collect_project_files(tmp_path)
    result = detect_test_runners(tmp_path, files)

    assert "pytest" in result.values
    assert "jest" in result.values
    assert "vitest" in result.values
    assert "cargo test" in result.values
    assert "go test" in result.values
    assert "rspec" in result.values
    assert "JUnit" in result.values
