"""Generator for .cursorrules (Cursor IDE format)."""

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


class CursorGenerator(BaseGenerator):
    """Generates .cursorrules for use with Cursor IDE."""

    output_filename = ".cursorrules"

    def _build_sections(self) -> list[str]:
        return [
            self._section_header(),
            self._section_always_rules(),
            self._section_never_rules(),
            self._section_project_overview(),
            self._section_commands(),
            self._section_directory_structure(),
            self._section_file_patterns(),
            self._section_conventions(),
            self._section_context_preferences(),
        ]

    def _section_header(self) -> str:
        return (
            "# .cursorrules\n\n"
            "Cursor IDE rules. These rules are applied to every AI interaction in this project."
        )

    def _section_always_rules(self) -> str:
        a = self.analysis
        langs = [lang.lower() for lang in a.languages]
        test_cmds = _test_commands(a)
        lint_cmds = _lint_commands(a)

        rules = [
            "## Always",
            "- Read the relevant source files before making changes.",
            "- Make minimal, targeted edits — avoid reformatting unrelated code.",
            "- Respect the existing code style (indentation, naming, import order).",
        ]

        if test_cmds:
            rules.append(f"- Run `{test_cmds[0]}` after every non-trivial change.")
        if lint_cmds:
            rules.append(f"- Run `{lint_cmds[0]}` before finalizing changes.")

        if "python" in langs:
            rules += [
                "- Add type annotations to all new public functions.",
                "- Use `pathlib.Path` instead of `os.path` for file operations.",
            ]
        if "typescript" in langs:
            rules += [
                "- Use TypeScript strict mode conventions.",
                "- Prefer named exports over default exports.",
            ]
        if "go" in langs:
            rules += [
                "- Handle all returned errors explicitly.",
                "- Run `gofmt` before submitting changes.",
            ]
        if "rust" in langs:
            rules += [
                "- Use the `?` operator for error propagation.",
                "- Document all public items with `///` comments.",
            ]
        if "swift" in langs:
            rules += [
                "- Use `guard let` / `if let` for optional unwrapping — avoid force `!`.",
                "- Run `swift build` or `xcodebuild` after structural changes.",
            ]
            if a.swift_components:
                swift_cmds = _swift_build_commands(a)
                rules.append(f"- Build command: `{swift_cmds[0]}`")

        # Rust-specific always rules
        if a.rust_components:
            rust_cmds = _rust_build_commands(a)
            rules.append(f"- After changes, run: `{rust_cmds[0]}` then `{rust_cmds[1]}`")
            rules.append("- Keep clippy clean: `cargo clippy -- -D warnings`")

        # Go-specific always rules
        if a.go_components:
            go_cmds = _go_build_commands(a)
            rules.append(f"- After changes, run: `{go_cmds[0]}` then `{go_cmds[1]}`")
            rules.append("- Keep vet clean: `go vet ./...`")

        return "\n".join(rules)

    def _section_never_rules(self) -> str:
        a = self.analysis
        langs = [lang.lower() for lang in a.languages]
        rules = [
            "## Never",
            "- Never commit API keys, tokens, or credentials.",
            "- Never delete tests to make the suite pass.",
            "- Never use `TODO` comments without a linked issue or explanation.",
            "- Never make changes outside the scope of the current task without flagging them.",
        ]

        if "python" in langs:
            rules += [
                "- Never use `except:` without specifying the exception type.",
                "- Never use `eval()` or `exec()` on untrusted input.",
            ]
        if "typescript" in langs or "javascript" in langs:
            rules += [
                "- Never use `var` — use `const` or `let`.",
                "- Never use `any` as a type without a documented justification.",
            ]
        if "go" in langs:
            rules.append("- Never use `_` to discard returned errors silently.")
        if "rust" in langs:
            rules.append("- Never use `unwrap()` in library code without a clear comment.")
        if "swift" in langs:
            rules += [
                "- Never force-unwrap (`!`) an optional without a guaranteed non-nil value.",
                "- Never call `DispatchQueue.main.sync` from the main thread.",
            ]

        # Additional never rules based on detected components
        if a.rust_components:
            rules.append("- Never introduce `unsafe` without a documented safety invariant.")
        if a.go_components:
            rules.append("- Never assign a returned error to `_` without a comment explaining why.")

        return "\n".join(rules)

    def _section_file_patterns(self) -> str:
        a = self.analysis
        ds = a.directory_structure
        langs = [lang.lower() for lang in a.languages]
        lines = ["## File Patterns"]

        if ds.source_directories:
            lines.append(
                "**Source files:** "
                + ", ".join(f"`{d}/**`" for d in ds.source_directories)
            )
        if ds.test_directories:
            lines.append(
                "**Test files:** "
                + ", ".join(f"`{d}/**`" for d in ds.test_directories)
            )

        if "python" in langs:
            lines += [
                "**Python source:** `**/*.py`",
                "**Python tests:** `**/test_*.py`, `**/*_test.py`",
            ]
        if "typescript" in langs:
            lines += [
                "**TypeScript source:** `**/*.ts`, `**/*.tsx`",
                "**TypeScript tests:** `**/*.test.ts`, `**/*.spec.ts`",
            ]
        if "go" in langs:
            lines += [
                "**Go source:** `**/*.go`",
                "**Go tests:** `**/*_test.go`",
            ]
        if "swift" in langs:
            lines += [
                "**Swift source:** `**/*.swift`",
                "**Xcode project:** `**/*.xcodeproj`, `**/*.xcworkspace`",
            ]
            if "spm" in a.swift_components:
                lines.append("**Swift Package:** `Package.swift`, `Sources/**/*.swift`")
        if "rust" in langs:
            lines += [
                "**Rust source:** `src/**/*.rs`",
                "**Rust tests:** `tests/**/*.rs`",
                "**Cargo config:** `Cargo.toml`, `Cargo.lock`",
            ]

        if len(lines) == 1:
            lines.append("_(No file patterns detected — add patterns here.)_")

        return "\n".join(lines)

    def _section_context_preferences(self) -> str:
        a = self.analysis
        ds = a.directory_structure
        lines = [
            "## Context Preferences",
            "When writing or reviewing code, prefer to include in context:",
        ]

        all_dirs = ds.source_directories + ds.test_directories
        if all_dirs:
            lines.append(
                "- " + ", ".join(f"`{d}/`" for d in all_dirs) + " (primary code locations)"
            )

        lines += [
            "- The file being edited and its direct imports.",
            "- Relevant test files alongside source files.",
            "- Configuration files when modifying build or tooling behavior.",
        ]

        if a.frameworks:
            lines.append(
                f"- Framework-specific files for: {', '.join(a.frameworks)}"
            )

        if a.swift_components:
            lines.append("- For Swift: include `Package.swift` or `.xcodeproj` alongside source files.")
            if "SwiftUI" in a.swift_components:
                lines.append("- For SwiftUI: include the View file and its associated ViewModel/ObservableObject.")
        if a.rust_components:
            lines.append("- For Rust: include `Cargo.toml` when adding or changing dependencies.")
            lines.append("- For Rust: include the `src/lib.rs` or `src/main.rs` entry point for structural context.")
        if a.go_components:
            lines.append("- For Go: include `go.mod` when modifying module dependencies.")
            lines.append("- For Go: include the package's `*_test.go` alongside the implementation file.")

        return "\n".join(lines)
