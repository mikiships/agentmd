from pathlib import Path

from agentmd.detectors.common import collect_project_files
from agentmd.detectors.language import detect_languages


def test_detect_languages_covers_all_required_targets(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "app.tsx").write_text("export const a = 1;\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "lib.rs").write_text("fn main() {}\n", encoding="utf-8")
    (tmp_path / "go").mkdir()
    (tmp_path / "go" / "main.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "ruby").mkdir()
    (tmp_path / "ruby" / "app.rb").write_text("puts 'x'\n", encoding="utf-8")
    (tmp_path / "java").mkdir()
    (tmp_path / "java" / "Main.java").write_text("class Main {}\n", encoding="utf-8")
    (tmp_path / "csharp").mkdir()
    (tmp_path / "csharp" / "Program.cs").write_text("class Program {}\n", encoding="utf-8")
    (tmp_path / "ios").mkdir()
    (tmp_path / "ios" / "App.swift").write_text("import SwiftUI\n", encoding="utf-8")

    files = collect_project_files(tmp_path)
    result = detect_languages(tmp_path, files)

    assert "Python" in result.values
    assert "TypeScript/JavaScript" in result.values
    assert "Rust" in result.values
    assert "Go" in result.values
    assert "Ruby" in result.values
    assert "Java" in result.values
    assert "C#" in result.values
    assert "Swift" in result.values
