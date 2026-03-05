"""Generator for copilot-instructions.md (GitHub Copilot format)."""

from __future__ import annotations

from agentmd.generators.base import (
    BaseGenerator,
    _test_commands,
    _lint_commands,
    _swift_build_commands,
    _rust_build_commands,
    _go_build_commands,
    _swift_conventions,
    _rust_conventions,
    _go_conventions,
)


class CopilotGenerator(BaseGenerator):
    """Generates copilot-instructions.md for GitHub Copilot."""

    output_filename = "copilot-instructions.md"

    def _build_sections(self) -> list[str]:
        return [
            self._section_header(),
            self._section_project_overview(),
            self._section_commands(),
            self._section_directory_structure(),
            self._section_coding_standards(),
            self._section_test_patterns(),
            self._section_conventions(),
            self._section_review_checklist(),
        ]

    def _build_sections_minimal(self) -> list[str]:
        return super()._build_sections_minimal()

    def _section_header(self) -> str:
        return (
            "# Copilot Instructions\n\n"
            "GitHub Copilot context for this repository. "
            "Copilot uses this file to tailor suggestions to the project's conventions."
        )

    def _section_coding_standards(self) -> str:
        a = self.analysis
        langs = [lang.lower() for lang in a.languages]
        lines = ["## Coding Standards"]

        if "python" in langs:
            lines += [
                "### Python",
                "- Type-annotate all public functions and class attributes.",
                "- Use dataclasses or Pydantic models for structured data — avoid plain dicts for complex payloads.",
                "- Keep functions focused: one responsibility per function, typically under 40 lines.",
                "- Use `pathlib.Path` for file operations, not `os.path`.",
                "- Prefer f-strings over `.format()` or `%` formatting.",
            ]
            if "ruff" in " ".join(a.linters).lower():
                lines.append("- Code style enforced by `ruff`; do not fight the formatter.")
            if "mypy" in " ".join(a.linters).lower():
                lines.append("- Type checking enforced by `mypy`; avoid `Any` unless necessary.")

        if "typescript" in langs:
            lines += [
                "### TypeScript",
                "- Enable strict mode: `\"strict\": true` in tsconfig.",
                "- Use interfaces for object shapes, types for unions and aliases.",
                "- Avoid `any`; use `unknown` with type guards instead.",
                "- Prefer async/await over raw Promises.",
                "- Use optional chaining (`?.`) and nullish coalescing (`??`) over manual null checks.",
            ]

        if "javascript" in langs and "typescript" not in langs:
            lines += [
                "### JavaScript",
                "- Use `const` by default, `let` only when reassignment is needed. Never `var`.",
                "- Prefer arrow functions for callbacks.",
                "- Use modern ES2020+ features where supported.",
            ]

        if "go" in langs:
            lines += [
                "### Go",
                "- Return errors explicitly — never panic in library code.",
                "- Keep struct definitions small; compose via embedding rather than deep inheritance.",
                "- Use `context.Context` as the first parameter for any function that may block.",
                "- Use table-driven tests with `t.Run` for subtests.",
            ]

        if "rust" in langs:
            lines += [
                "### Rust",
                "- Prefer `Result<T, E>` over panicking — use `?` to propagate.",
                "- Use `derive` macros for standard traits (`Debug`, `Clone`, `PartialEq`).",
                "- Document public items with `///` doc comments; run `cargo doc` to verify.",
                "- Keep `unsafe` blocks small and document the invariant being upheld.",
            ]

        if "swift" in langs or a.swift_components:
            lines += [
                "### Swift",
                "- Prefer `struct` and `enum` over `class` for value semantics.",
                "- Use `guard let` for early returns on nil; avoid force-unwrap (`!`) in production code.",
                "- Mark view controllers and delegate callbacks `@MainActor` where UI mutations occur.",
                "- Use `Result<T, Error>` or `throws` for explicit error paths.",
            ]
            if a.swift_components:
                if "SwiftUI" in a.swift_components:
                    lines += [
                        "- SwiftUI: keep `body` computed property thin; extract subviews into separate `View` structs.",
                        "- SwiftUI: use `@StateObject` for owned models, `@ObservedObject` for injected ones.",
                    ]
                if "UIKit" in a.swift_components:
                    lines += [
                        "- UIKit: configure views in `viewDidLoad`; update UI on the main thread only.",
                        "- UIKit: use Auto Layout programmatically or via Interface Builder — avoid fixed frames.",
                    ]
                if "SwiftLint" in a.swift_components:
                    lines.append("- Code style enforced by SwiftLint; run `swiftlint lint` before committing.")

        if len(lines) == 1:
            lines.append("_(No language-specific standards inferred — add coding standards here.)_")

        return "\n".join(lines)

    def _section_test_patterns(self) -> str:
        a = self.analysis
        langs = [lang.lower() for lang in a.languages]
        test_cmds = _test_commands(a)
        lines = ["## Test Patterns"]

        if test_cmds:
            lines.append(f"**Run tests:** `{test_cmds[0]}`")

        if "python" in langs and any("pytest" in r.lower() for r in a.test_runners):
            ds = a.directory_structure
            test_dir = ds.test_directories[0] if ds.test_directories else "tests"
            lines += [
                f"- Test files live in `{test_dir}/`, named `test_*.py`.",
                "- Use `pytest.fixture` for reusable test setup.",
                "- Use `pytest.mark.parametrize` for table-driven tests.",
                "- Mock external services with `unittest.mock` or `pytest-mock`.",
                "- One logical assertion per test where possible; complex state assertions can use multiple asserts.",
            ]

        if "typescript" in langs or "javascript" in langs:
            if any("jest" in r.lower() for r in a.test_runners):
                lines += [
                    "- Test files: `*.test.ts` or `*.spec.ts` co-located with source or in a `__tests__/` directory.",
                    "- Use `describe` blocks to group related tests.",
                    "- Mock modules with `jest.mock()` at the top of the file.",
                ]
            elif any("vitest" in r.lower() for r in a.test_runners):
                lines += [
                    "- Test files: `*.test.ts` or `*.spec.ts`.",
                    "- Use Vitest's `vi.mock()` for module mocking.",
                ]

        if "go" in langs:
            lines += [
                "- Test files: `*_test.go` in the same package.",
                "- Use table-driven tests with `[]struct{ name string; ... }` and `t.Run`.",
                "- Use `t.Helper()` in test helpers to improve failure output.",
            ]

        if "rust" in langs:
            lines += [
                "- Unit tests: `#[cfg(test)]` module at the bottom of each source file.",
                "- Integration tests: `tests/` directory at the crate root.",
                "- Use `#[should_panic]` for expected panics.",
            ]

        if "swift" in langs or a.swift_components:
            lines += [
                "- Swift unit tests: XCTest framework; test classes inherit from `XCTestCase`.",
                "- Async tests: use `async throws` test methods or `XCTestExpectation`.",
                "- Use `XCTAssertEqual`, `XCTAssertNil`, `XCTAssertThrowsError` for assertions.",
            ]
            if a.swift_components:
                if "spm" in a.swift_components:
                    lines.append("- SPM tests: run `swift test`; test targets declared in `Package.swift`.")
                if "xcodeproj" in a.swift_components:
                    lines.append("- Xcode tests: run via `xcodebuild test -scheme <SchemeName>`.")

        if len(lines) == 1:
            lines.append("_(No test runner detected — add test patterns here.)_")

        return "\n".join(lines)

    def _section_review_checklist(self) -> str:
        a = self.analysis
        test_cmds = _test_commands(a)
        lint_cmds = _lint_commands(a)
        lines = [
            "## PR Review Checklist",
            "Copilot should flag suggestions or changes that violate any of the following:",
            "",
        ]

        checklist = [
            "All new public functions have type annotations and docstrings.",
            "No hardcoded secrets, credentials, or environment-specific paths.",
            "New behavior is covered by at least one test.",
            "Existing tests are not deleted or skipped to make CI pass.",
            "Dependencies added to the lock file and justification noted in the PR.",
            "Commit messages follow the project prefix convention.",
        ]

        if test_cmds:
            checklist.append(f"Test suite passes: `{test_cmds[0]}`")
        elif a.swift_components:
            swift_cmds = _swift_build_commands(a)
            checklist.append(f"Test suite passes: `{swift_cmds[1] if len(swift_cmds) > 1 else swift_cmds[0]}`")
        elif a.rust_components:
            checklist.append("Test suite passes: `cargo test`")
        elif a.go_components:
            checklist.append("Test suite passes: `go test ./...`")

        if lint_cmds:
            checklist.append(f"Linting clean: `{lint_cmds[0]}`")
        elif a.rust_components:
            checklist.append("Linting clean: `cargo clippy -- -D warnings`")
            checklist.append("Formatting clean: `cargo fmt --check`")
        elif a.go_components:
            checklist.append("Linting clean: `go vet ./...`")
        elif a.swift_components and "SwiftLint" in a.swift_components:
            checklist.append("Linting clean: `swiftlint lint`")

        for item in checklist:
            lines.append(f"- [ ] {item}")

        return "\n".join(lines)
