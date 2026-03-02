"""Generator for .cursorrules (Cursor IDE format)."""

from __future__ import annotations

from agentmd.generators.base import BaseGenerator, _test_commands, _lint_commands


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

        return "\n".join(lines)
