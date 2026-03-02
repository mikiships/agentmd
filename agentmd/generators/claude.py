"""Generator for CLAUDE.md (Claude Code format)."""

from __future__ import annotations

from agentmd.generators.base import BaseGenerator


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

        return "\n".join(lines)
