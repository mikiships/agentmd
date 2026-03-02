"""Generator for CLAUDE.md (Claude Code format)."""

from __future__ import annotations

from agentmd.generators.base import (
    BaseGenerator,
    _swift_build_commands,
    _rust_build_commands,
    _go_build_commands,
)


class ClaudeGenerator(BaseGenerator):
    """Generates CLAUDE.md for use with Claude Code."""

    output_filename = "CLAUDE.md"

    def _build_sections(self) -> list[str]:
        return [
            self._section_header(),
            self._section_project_overview(),
            self._section_commands(),
            self._section_directory_structure(),
            self._section_conventions(),
            self._section_claude_tips(),
            self._section_style_guide(),
            self._section_antipatterns(),
        ]

    def _section_header(self) -> str:
        return "# CLAUDE.md\n\nAgent context for Claude Code. Keep this file up to date as the project evolves."

    def _section_claude_tips(self) -> str:
        lines = [
            "## Claude Code Tips",
            "- Use `/compact` when context grows large mid-session to avoid token limit errors.",
            "- Use `/review` before committing to get a focused code review.",
            "- Use `/init` in a new checkout to re-read this file and orient yourself.",
            "- Open multiple files in a single message when changes span files — reduces round-trips.",
            "- Prefer small, targeted edits over full-file rewrites when touching existing code.",
        ]

        a = self.analysis
        test_cmds = []
        ds = a.directory_structure
        test_dir = ds.test_directories[0] if ds.test_directories else "tests"
        for runner in a.test_runners:
            if "pytest" in runner.lower():
                test_cmds.append(f"python3 -m pytest {test_dir}/ -x")
            elif "jest" in runner.lower():
                test_cmds.append("npx jest --no-coverage")
            elif "vitest" in runner.lower():
                test_cmds.append("npx vitest run")

        if test_cmds:
            lines.append(
                f"- After every non-trivial change, run `{test_cmds[0]}` to confirm nothing broke."
            )

        a = self.analysis
        # Swift-specific Claude Code tips
        if a.swift_components:
            swift_cmds = _swift_build_commands(a)
            lines.append(
                f"- Use `/terminal` to run Swift build: `{swift_cmds[0]}`"
            )
            lines.append(
                "- Use `/search` to locate Swift files — Xcode project structure can be deep."
            )
            if "SwiftLint" in a.swift_components:
                lines.append("- Run `swiftlint lint` before committing to catch style violations early.")
            if "spm" in a.swift_components:
                lines.append("- Swift Package Manager: resolve dependencies with `swift package resolve`.")

        # Rust-specific Claude Code tips
        if a.rust_components:
            lines.append(
                "- Run `cargo check` for fast type-checking without a full build."
            )
            lines.append(
                "- Run `cargo clippy -- -D warnings` before committing to catch common mistakes."
            )
            lines.append(
                "- Use `cargo test -- --nocapture` to see `println!` output during tests."
            )

        # Go-specific Claude Code tips
        if a.go_components:
            lines.append(
                "- Run `go build ./...` to type-check the whole module quickly."
            )
            lines.append(
                "- Use `go test -run TestName ./...` to run a single test by name."
            )
            lines.append(
                "- Run `go vet ./...` before committing to catch common correctness issues."
            )

        return "\n".join(lines)

    def _section_style_guide(self) -> str:
        a = self.analysis
        langs = [lang.lower() for lang in a.languages]
        lines = ["## Style Guide"]

        if "python" in langs:
            lines += [
                "- All public functions and methods must have type annotations.",
                "- Docstrings: use triple-quoted strings on public classes and functions.",
                "- Maximum line length: 100 characters (unless project config says otherwise).",
                "- Imports: standard library first, third-party second, local last (separated by blank lines).",
            ]
            if "ruff" in " ".join(a.linters).lower():
                lines.append("- Linting enforced by `ruff` — run `ruff check .` before committing.")
            if "mypy" in " ".join(a.linters).lower():
                lines.append("- Type checking enforced by `mypy` — run `mypy .` before committing.")

        if "typescript" in langs:
            lines += [
                "- Prefer `interface` over `type` for object shapes.",
                "- Avoid `any` — use `unknown` and narrow appropriately.",
                "- Use `const` by default; only use `let` when reassignment is required.",
            ]
            if "eslint" in " ".join(a.linters).lower():
                lines.append("- Linting enforced by ESLint — check config at `.eslintrc.*`.")

        if "go" in langs:
            lines += [
                "- Run `gofmt` before every commit.",
                "- Errors are values — return them, don't panic.",
                "- Keep functions short; extract helpers when logic exceeds ~40 lines.",
            ]

        if "rust" in langs:
            lines += [
                "- Run `cargo fmt` before every commit.",
                "- Avoid `unwrap()` in library code; use `?` and propagate errors.",
                "- Document public items with `///` doc comments.",
            ]

        if "swift" in langs:
            lines += [
                "- Run `swift-format` or `swiftlint` before every commit.",
                "- Prefer `struct` over `class` for value semantics.",
                "- Use Swift's `Result` type or `throws` for explicit error handling.",
                "- Guard against optional unwrapping failures with `guard let` or `if let`.",
            ]

        if len(lines) == 1:
            lines.append("_(No language-specific style guide inferred — add rules here.)_")

        return "\n".join(lines)

    def _section_antipatterns(self) -> str:
        a = self.analysis
        langs = [lang.lower() for lang in a.languages]
        lines = ["## Anti-Patterns to Avoid"]

        lines += [
            "- **Do not** make broad refactors outside the scope of the current task.",
            "- **Do not** delete or skip existing tests to make CI green.",
            "- **Do not** add dependencies without noting them in the commit message.",
        ]

        if "python" in langs:
            lines += [
                "- **Do not** use bare `except:` — always catch specific exceptions.",
                "- **Do not** use mutable default arguments (e.g., `def f(x=[])`).",
            ]

        if "typescript" in langs or "javascript" in langs:
            lines += [
                "- **Do not** use `var` — use `const` or `let`.",
                "- **Do not** suppress TypeScript errors with `// @ts-ignore` without a comment explaining why.",
            ]

        if "go" in langs:
            lines += [
                "- **Do not** ignore returned errors (assign to `_`).",
                "- **Do not** use `init()` functions unless absolutely necessary.",
            ]

        if "swift" in langs:
            lines += [
                "- **Do not** force-unwrap optionals (`!`) without a guaranteed non-nil guarantee.",
                "- **Do not** use `DispatchQueue.main.sync` from the main thread — it deadlocks.",
                "- **Do not** mutate state from multiple threads without synchronization.",
            ]

        if "rust" in langs:
            lines += [
                "- **Do not** use `unwrap()` or `expect()` in production code paths.",
                "- **Do not** introduce `unsafe` blocks without a clear safety comment.",
            ]

        return "\n".join(lines)
