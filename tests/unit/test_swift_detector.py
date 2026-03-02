"""Tests for Swift/Xcode project detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentmd.detectors.swift import detect_swift_project


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_files(tmp_path: Path, structure: dict[str, str]) -> list[Path]:
    """Write files under tmp_path and return relative Path list."""
    paths: list[Path] = []
    for rel, content in structure.items():
        full = tmp_path / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        paths.append(Path(rel))
    return paths


# ---------------------------------------------------------------------------
# Project file tests
# ---------------------------------------------------------------------------

def test_detects_xcodeproj(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "MyApp.xcodeproj/project.pbxproj": "// xcode project",
    })
    result = detect_swift_project(tmp_path, files)
    assert "xcodeproj" in result.values
    assert any("xcodeproj" in e for e in result.evidence.get("xcodeproj", []))


def test_detects_package_swift(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Package.swift": 'let package = Package(name: "MyLib")',
    })
    result = detect_swift_project(tmp_path, files)
    assert "spm" in result.values
    assert "Package.swift" in result.evidence.get("spm", [])


def test_detects_podfile(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Podfile": "platform :ios, '14.0'\npod 'Alamofire'",
    })
    result = detect_swift_project(tmp_path, files)
    assert "cocoapods" in result.values
    assert "Podfile" in result.evidence.get("cocoapods", [])


def test_detects_xcworkspace(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "MyApp.xcworkspace/contents.xcworkspacedata": "<Workspace/>",
    })
    result = detect_swift_project(tmp_path, files)
    assert "xcworkspace" in result.values


# ---------------------------------------------------------------------------
# Framework detection tests
# ---------------------------------------------------------------------------

def test_detects_swiftui(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Sources/ContentView.swift": "import SwiftUI\nstruct ContentView: View { var body: some View { Text(\"Hi\") } }",
    })
    result = detect_swift_project(tmp_path, files)
    assert "SwiftUI" in result.values
    assert result.evidence.get("SwiftUI")


def test_detects_uikit(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Sources/AppDelegate.swift": "import UIKit\n@main class AppDelegate: UIResponder, UIApplicationDelegate {}",
    })
    result = detect_swift_project(tmp_path, files)
    assert "UIKit" in result.values


def test_detects_appkit(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Sources/Main.swift": "import AppKit\nclass MainWindowController: NSWindowController {}",
    })
    result = detect_swift_project(tmp_path, files)
    assert "AppKit" in result.values


def test_detects_combine(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Sources/ViewModel.swift": "import Combine\nimport Foundation\nclass VM: ObservableObject {}",
    })
    result = detect_swift_project(tmp_path, files)
    assert "Combine" in result.values


# ---------------------------------------------------------------------------
# Linter detection tests
# ---------------------------------------------------------------------------

def test_detects_swiftlint_yml(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "swiftlint.yml": "disabled_rules:\n  - trailing_whitespace",
    })
    result = detect_swift_project(tmp_path, files)
    assert "SwiftLint" in result.values
    assert "swiftlint.yml" in result.evidence.get("SwiftLint", [])


def test_detects_dot_swiftlint_yml(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        ".swiftlint.yml": "disabled_rules: []",
    })
    result = detect_swift_project(tmp_path, files)
    assert "SwiftLint" in result.values
    assert ".swiftlint.yml" in result.evidence.get("SwiftLint", [])


def test_detects_swift_format(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        ".swift-format": '{"version": 1, "indentation": {"spaces": 4}}',
    })
    result = detect_swift_project(tmp_path, files)
    assert "swift-format" in result.values
    assert ".swift-format" in result.evidence.get("swift-format", [])


# ---------------------------------------------------------------------------
# CI detection tests
# ---------------------------------------------------------------------------

def test_detects_xcodebuild_in_github_actions(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        ".github/workflows/ci.yml": (
            "name: CI\non: [push]\njobs:\n  build:\n    runs-on: macos-latest\n"
            "    steps:\n      - run: xcodebuild -scheme MyApp -destination 'platform=iOS Simulator'\n"
        ),
    })
    result = detect_swift_project(tmp_path, files)
    assert "xcodebuild-ci" in result.values
    assert result.evidence.get("xcodebuild-ci")


def test_no_xcodebuild_in_non_swift_workflow(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest\n",
    })
    result = detect_swift_project(tmp_path, files)
    assert "xcodebuild-ci" not in result.values


# ---------------------------------------------------------------------------
# Empty / no-Swift project
# ---------------------------------------------------------------------------

def test_empty_project_returns_empty(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "README.md": "# My Project",
        "main.py": "print('hello')",
    })
    result = detect_swift_project(tmp_path, files)
    assert result.values == []
    assert result.evidence == {}


# ---------------------------------------------------------------------------
# Ordering guarantee
# ---------------------------------------------------------------------------

def test_ordering_is_deterministic(tmp_path: Path) -> None:
    """Project types come before frameworks, linters, then CI."""
    files = _make_files(tmp_path, {
        "Package.swift": "let package = Package(name: \"X\")",
        "Sources/View.swift": "import SwiftUI\nimport Combine",
        ".swiftlint.yml": "disabled_rules: []",
        ".github/workflows/ci.yml": "name: CI\nruns-on: macos\nsteps:\n  - run: xcodebuild\n",
    })
    result = detect_swift_project(tmp_path, files)
    # spm (project) must appear before SwiftUI/Combine (frameworks) before SwiftLint (linter)
    idx_spm = result.values.index("spm")
    idx_swiftui = result.values.index("SwiftUI")
    idx_linter = result.values.index("SwiftLint")
    assert idx_spm < idx_swiftui
    assert idx_swiftui < idx_linter
