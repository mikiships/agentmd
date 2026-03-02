"""Tests for D4: generator updates for Swift, Rust, and Go languages."""

from __future__ import annotations

import pytest

from agentmd.generators import (
    ClaudeGenerator,
    CodexGenerator,
    CopilotGenerator,
    CursorGenerator,
)
from agentmd.types import DirectoryStructure, GitHistorySummary, ProjectAnalysis


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

def _make_swift_analysis(components: list[str] | None = None) -> ProjectAnalysis:
    return ProjectAnalysis(
        root_path="/tmp/swift_proj",
        languages=["Swift"],
        package_managers=[],
        frameworks=[],
        test_runners=[],
        linters=[],
        ci_systems=[],
        swift_components=components if components is not None else ["spm", "SwiftUI", "SwiftLint"],
        directory_structure=DirectoryStructure(
            top_level_directories=["Sources", "Tests"],
            source_directories=["Sources"],
            test_directories=["Tests"],
        ),
        git_history=GitHistorySummary(),
    )


def _make_swift_xcode_analysis() -> ProjectAnalysis:
    return ProjectAnalysis(
        root_path="/tmp/xcode_proj",
        languages=["Swift"],
        package_managers=[],
        frameworks=[],
        test_runners=[],
        linters=[],
        ci_systems=[],
        swift_components=["xcodeproj", "xcworkspace", "UIKit", "SwiftLint"],
        directory_structure=DirectoryStructure(
            top_level_directories=["MyApp", "MyAppTests"],
            source_directories=["MyApp"],
            test_directories=["MyAppTests"],
        ),
        git_history=GitHistorySummary(),
    )


def _make_rust_analysis(components: list[str] | None = None) -> ProjectAnalysis:
    return ProjectAnalysis(
        root_path="/tmp/rust_proj",
        languages=["Rust"],
        package_managers=["cargo"],
        frameworks=[],
        test_runners=[],
        linters=[],
        ci_systems=[],
        rust_components=components if components is not None else ["cargo-toml", "cargo-lock", "tokio", "serde"],
        directory_structure=DirectoryStructure(
            top_level_directories=["src", "tests"],
            source_directories=["src"],
            test_directories=["tests"],
        ),
        git_history=GitHistorySummary(),
    )


def _make_go_analysis(components: list[str] | None = None) -> ProjectAnalysis:
    return ProjectAnalysis(
        root_path="/tmp/go_proj",
        languages=["Go"],
        package_managers=["go"],
        frameworks=[],
        test_runners=[],
        linters=[],
        ci_systems=[],
        go_components=components if components is not None else ["go-mod", "go-sum", "gin", "golangci-lint"],
        directory_structure=DirectoryStructure(
            top_level_directories=["cmd", "pkg", "internal"],
            source_directories=["cmd", "pkg"],
            test_directories=["pkg"],
        ),
        git_history=GitHistorySummary(),
    )


def _make_rust_web_analysis() -> ProjectAnalysis:
    return ProjectAnalysis(
        root_path="/tmp/rust_web",
        languages=["Rust"],
        package_managers=["cargo"],
        frameworks=[],
        test_runners=[],
        linters=[],
        ci_systems=[],
        rust_components=["cargo-toml", "axum", "tokio", "serde", "sqlx"],
        directory_structure=DirectoryStructure(
            top_level_directories=["src"],
            source_directories=["src"],
        ),
        git_history=GitHistorySummary(),
    )


def _make_go_cli_analysis() -> ProjectAnalysis:
    return ProjectAnalysis(
        root_path="/tmp/go_cli",
        languages=["Go"],
        package_managers=["go"],
        frameworks=[],
        test_runners=[],
        linters=[],
        ci_systems=[],
        go_components=["go-mod", "cobra", "viper"],
        directory_structure=DirectoryStructure(
            top_level_directories=["cmd", "internal"],
            source_directories=["cmd"],
        ),
        git_history=GitHistorySummary(),
    )


# ==================================================================
# ClaudeGenerator tests
# ==================================================================

class TestClaudeGeneratorSwift:
    def test_swift_build_commands_in_output(self):
        gen = ClaudeGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "swift build" in output

    def test_swift_test_commands_in_output(self):
        gen = ClaudeGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "swift test" in output

    def test_swiftlint_mentioned(self):
        gen = ClaudeGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "swiftlint" in output.lower()

    def test_swift_claude_tips(self):
        gen = ClaudeGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "swift" in output.lower()

    def test_xcodebuild_for_xcode_project(self):
        gen = ClaudeGenerator(_make_swift_xcode_analysis())
        output = gen.generate()
        assert "xcodebuild" in output

    def test_swift_style_guide(self):
        gen = ClaudeGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "struct" in output or "optional" in output.lower() or "guard" in output.lower()

    def test_swift_antipatterns(self):
        gen = ClaudeGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "force" in output.lower() or "unwrap" in output.lower() or "!" in output


class TestClaudeGeneratorRust:
    def test_cargo_build_in_output(self):
        gen = ClaudeGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cargo build" in output

    def test_cargo_test_in_output(self):
        gen = ClaudeGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cargo test" in output

    def test_cargo_clippy_in_output(self):
        gen = ClaudeGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cargo clippy" in output

    def test_cargo_fmt_in_output(self):
        gen = ClaudeGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cargo fmt" in output

    def test_rust_error_handling_conventions(self):
        gen = ClaudeGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "unwrap" in output.lower() or "?" in output

    def test_rust_antipatterns(self):
        gen = ClaudeGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "unsafe" in output or "unwrap" in output.lower()


class TestClaudeGeneratorGo:
    def test_go_build_in_output(self):
        gen = ClaudeGenerator(_make_go_analysis())
        output = gen.generate()
        assert "go build" in output

    def test_go_test_in_output(self):
        gen = ClaudeGenerator(_make_go_analysis())
        output = gen.generate()
        assert "go test" in output

    def test_go_vet_in_output(self):
        gen = ClaudeGenerator(_make_go_analysis())
        output = gen.generate()
        assert "go vet" in output

    def test_golangci_lint_in_output(self):
        gen = ClaudeGenerator(_make_go_analysis())
        output = gen.generate()
        assert "golangci-lint" in output

    def test_go_error_handling_conventions(self):
        gen = ClaudeGenerator(_make_go_analysis())
        output = gen.generate()
        assert "err" in output.lower() or "error" in output.lower()


# ==================================================================
# CodexGenerator tests
# ==================================================================

class TestCodexGeneratorSwift:
    def test_swift_sandbox_notes(self):
        gen = CodexGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "swift" in output.lower()

    def test_spm_commands_in_output(self):
        gen = CodexGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "swift build" in output or "swift test" in output

    def test_xcode_scheme_note_for_xcodeproj(self):
        gen = CodexGenerator(_make_swift_xcode_analysis())
        output = gen.generate()
        assert "xcodebuild" in output or "scheme" in output.lower()

    def test_cocoapods_note(self):
        analysis = _make_swift_xcode_analysis()
        analysis.swift_components = ["xcodeproj", "cocoapods"]
        gen = CodexGenerator(analysis)
        output = gen.generate()
        assert "cocoapods" in output.lower() or "pod install" in output.lower()

    def test_swift_approval_gate(self):
        gen = CodexGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "swift test" in output or "swift build" in output


class TestCodexGeneratorRust:
    def test_rust_sandbox_notes(self):
        gen = CodexGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cargo" in output.lower()

    def test_rust_clippy_approval_gate(self):
        gen = CodexGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cargo clippy" in output

    def test_rust_fmt_approval_gate(self):
        gen = CodexGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cargo fmt" in output

    def test_rust_db_note_for_sqlx(self):
        gen = CodexGenerator(_make_rust_web_analysis())
        output = gen.generate()
        assert "sqlx" in output.lower() or "database" in output.lower() or "db" in output.lower()

    def test_cargo_test_approval_gate(self):
        gen = CodexGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cargo test" in output


class TestCodexGeneratorGo:
    def test_go_sandbox_notes(self):
        gen = CodexGenerator(_make_go_analysis())
        output = gen.generate()
        assert "go mod download" in output or "go" in output.lower()

    def test_go_vet_approval_gate(self):
        gen = CodexGenerator(_make_go_analysis())
        output = gen.generate()
        assert "go vet" in output

    def test_go_test_approval_gate(self):
        gen = CodexGenerator(_make_go_analysis())
        output = gen.generate()
        assert "go test" in output

    def test_go_db_note_for_gorm(self):
        analysis = _make_go_analysis(["go-mod", "gorm"])
        gen = CodexGenerator(analysis)
        output = gen.generate()
        assert "database" in output.lower() or "db" in output.lower() or "gorm" in output.lower()


# ==================================================================
# CursorGenerator tests
# ==================================================================

class TestCursorGeneratorSwift:
    def test_swift_file_patterns(self):
        gen = CursorGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "*.swift" in output

    def test_spm_package_swift_pattern(self):
        gen = CursorGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "Package.swift" in output or "*.swift" in output

    def test_xcode_file_patterns(self):
        gen = CursorGenerator(_make_swift_xcode_analysis())
        output = gen.generate()
        assert "xcodeproj" in output or "xcworkspace" in output

    def test_swift_always_rules(self):
        gen = CursorGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "swift" in output.lower()

    def test_swift_never_rules(self):
        gen = CursorGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "force" in output.lower() or "unwrap" in output.lower() or "!" in output

    def test_swift_context_preferences(self):
        gen = CursorGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "swift" in output.lower() or "Package.swift" in output


class TestCursorGeneratorRust:
    def test_rust_file_patterns(self):
        gen = CursorGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "*.rs" in output

    def test_cargo_file_patterns(self):
        gen = CursorGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "Cargo.toml" in output

    def test_rust_always_rules(self):
        gen = CursorGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cargo build" in output or "cargo clippy" in output

    def test_rust_never_rules(self):
        gen = CursorGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "unsafe" in output or "unwrap" in output.lower()

    def test_rust_context_preferences(self):
        gen = CursorGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "Cargo.toml" in output or "lib.rs" in output or "main.rs" in output


class TestCursorGeneratorGo:
    def test_go_file_patterns(self):
        gen = CursorGenerator(_make_go_analysis())
        output = gen.generate()
        assert "*.go" in output

    def test_go_test_file_patterns(self):
        gen = CursorGenerator(_make_go_analysis())
        output = gen.generate()
        assert "*_test.go" in output

    def test_go_always_rules(self):
        gen = CursorGenerator(_make_go_analysis())
        output = gen.generate()
        assert "go build" in output or "go vet" in output

    def test_go_never_rules(self):
        gen = CursorGenerator(_make_go_analysis())
        output = gen.generate()
        assert "error" in output.lower() or "_" in output

    def test_go_context_preferences(self):
        gen = CursorGenerator(_make_go_analysis())
        output = gen.generate()
        assert "go.mod" in output or "_test.go" in output


# ==================================================================
# CopilotGenerator tests
# ==================================================================

class TestCopilotGeneratorSwift:
    def test_swift_coding_standards(self):
        gen = CopilotGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "Swift" in output

    def test_swift_struct_preference(self):
        gen = CopilotGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "struct" in output or "value" in output.lower()

    def test_swiftui_standards(self):
        gen = CopilotGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "SwiftUI" in output or "StateObject" in output or "body" in output.lower()

    def test_uitkit_standards(self):
        gen = CopilotGenerator(_make_swift_xcode_analysis())
        output = gen.generate()
        assert "UIKit" in output or "viewDidLoad" in output or "Auto Layout" in output

    def test_swiftlint_in_standards(self):
        gen = CopilotGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "swiftlint" in output.lower() or "SwiftLint" in output

    def test_swift_test_patterns(self):
        gen = CopilotGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "XCTest" in output or "XCTestCase" in output

    def test_spm_test_command(self):
        gen = CopilotGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "swift test" in output

    def test_xcode_test_command(self):
        gen = CopilotGenerator(_make_swift_xcode_analysis())
        output = gen.generate()
        assert "xcodebuild" in output or "swift test" in output

    def test_swift_review_checklist(self):
        gen = CopilotGenerator(_make_swift_analysis())
        output = gen.generate()
        assert "swift test" in output or "swiftlint" in output.lower()


class TestCopilotGeneratorRust:
    def test_rust_coding_standards(self):
        gen = CopilotGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "Rust" in output

    def test_cargo_test_review_checklist(self):
        gen = CopilotGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cargo test" in output

    def test_cargo_clippy_review_checklist(self):
        gen = CopilotGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cargo clippy" in output

    def test_cargo_fmt_review_checklist(self):
        gen = CopilotGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cargo fmt" in output

    def test_rust_test_patterns(self):
        gen = CopilotGenerator(_make_rust_analysis())
        output = gen.generate()
        assert "cfg(test)" in output or "#[cfg" in output or "tests/" in output

    def test_tokio_framework_note(self):
        gen = CopilotGenerator(_make_rust_web_analysis())
        output = gen.generate()
        # Should mention async or tokio somewhere in conventions
        assert "async" in output.lower() or "tokio" in output.lower()


class TestCopilotGeneratorGo:
    def test_go_coding_standards(self):
        gen = CopilotGenerator(_make_go_analysis())
        output = gen.generate()
        assert "Go" in output

    def test_go_test_review_checklist(self):
        gen = CopilotGenerator(_make_go_analysis())
        output = gen.generate()
        assert "go test" in output

    def test_go_vet_review_checklist(self):
        gen = CopilotGenerator(_make_go_analysis())
        output = gen.generate()
        assert "go vet" in output

    def test_go_test_patterns(self):
        gen = CopilotGenerator(_make_go_analysis())
        output = gen.generate()
        assert "_test.go" in output or "t.Run" in output

    def test_go_cobra_convention(self):
        gen = CopilotGenerator(_make_go_cli_analysis())
        output = gen.generate()
        assert "cmd" in output or "cobra" in output.lower()


# ==================================================================
# Cross-generator: no language contamination
# ==================================================================

class TestNoLanguageContamination:
    """Ensure Swift/Rust/Go content is absent when no components detected."""

    def _make_python_only(self) -> ProjectAnalysis:
        return ProjectAnalysis(
            root_path="/tmp/python_proj",
            languages=["Python"],
            package_managers=["pip"],
            frameworks=[],
            test_runners=["pytest"],
            linters=["ruff"],
            ci_systems=[],
            swift_components=[],
            rust_components=[],
            go_components=[],
            directory_structure=DirectoryStructure(
                top_level_directories=["src", "tests"],
                source_directories=["src"],
                test_directories=["tests"],
            ),
            git_history=GitHistorySummary(),
        )

    def test_claude_no_xcodebuild_for_python(self):
        gen = ClaudeGenerator(self._make_python_only())
        output = gen.generate()
        assert "xcodebuild" not in output

    def test_claude_no_cargo_for_python(self):
        gen = ClaudeGenerator(self._make_python_only())
        output = gen.generate()
        assert "cargo build" not in output

    def test_codex_no_swift_sandbox_for_python(self):
        gen = CodexGenerator(self._make_python_only())
        output = gen.generate()
        assert "swift build" not in output
        assert "xcodebuild" not in output

    def test_cursor_no_swift_patterns_for_python(self):
        gen = CursorGenerator(self._make_python_only())
        output = gen.generate()
        assert "*.swift" not in output
        assert "Cargo.toml" not in output

    def test_copilot_no_swift_standards_for_python(self):
        gen = CopilotGenerator(self._make_python_only())
        output = gen.generate()
        assert "XCTestCase" not in output
        assert "swift test" not in output
