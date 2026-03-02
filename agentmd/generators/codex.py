"""Generator for AGENTS.md (Codex / OpenAI Codex format)."""

from __future__ import annotations

from agentmd.generators.base import (
    BaseGenerator,
    _test_commands,
    _lint_commands,
    _swift_build_commands,
    _rust_build_commands,
    _go_build_commands,
)


class CodexGenerator(BaseGenerator):
    """Generates AGENTS.md for use with OpenAI Codex."""

    output_filename = "AGENTS.md"

    def _build_sections(self) -> list[str]:
        return [
            self._section_header(),
            self._section_project_overview(),
            self._section_commands(),
            self._section_directory_structure(),
            self._section_sandbox_notes(),
            self._section_conventions(),
            self._section_apply_patch_notes(),
            self._section_approval_gates(),
            self._section_antipatterns(),
        ]

    def _section_header(self) -> str:
        return (
            "# AGENTS.md\n\n"
            "Agent context for OpenAI Codex. "
            "This file is read automatically by the Codex sandbox at session start."
        )

    def _section_sandbox_notes(self) -> str:
        a = self.analysis
        lines = [
            "## Sandbox Awareness",
            "The Codex sandbox has network access disabled by default during code execution.",
            "- Do not make HTTP requests in tests — mock all external calls.",
            "- Do not rely on system-installed tools; prefer project-local binaries (`./node_modules/.bin/`, virtualenv, etc.).",
            "- The sandbox resets between sessions — do not rely on persistent state outside the repo.",
        ]

        if "pip" in " ".join(a.package_managers).lower() or "poetry" in " ".join(a.package_managers).lower():
            lines.append(
                "- Python dependencies: install into a virtualenv. "
                "The sandbox may not have all packages pre-installed."
            )

        if "npm" in " ".join(a.package_managers).lower() or "pnpm" in " ".join(a.package_managers).lower():
            lines.append(
                "- Node dependencies: run the install command before running tests."
            )

        # Swift sandbox notes
        if a.swift_components:
            lines.append(
                "- Swift/Xcode builds require macOS. If running in a Linux sandbox, use Swift Package Manager (`swift build/test`) — Xcode is not available."
            )
            if "xcodeproj" in a.swift_components or "xcworkspace" in a.swift_components:
                lines.append(
                    "- `xcodebuild` requires a valid scheme. Run `xcodebuild -list` to discover available schemes."
                )
            if "cocoapods" in a.swift_components:
                lines.append(
                    "- CocoaPods: run `pod install` before building; use the `.xcworkspace` (not `.xcodeproj`) afterward."
                )

        # Rust sandbox notes
        if a.rust_components:
            lines.append(
                "- Rust builds may require downloading crates. Ensure `cargo build` runs before `cargo test` in a cold sandbox."
            )
            lines.append(
                "- `cargo clippy` and `cargo fmt` are separate tools — both must pass before a task is complete."
            )
            components = a.rust_components
            if any(c in components for c in ("diesel", "sqlx")):
                lines.append(
                    "- Database crates (diesel/sqlx) require a running database or migrations; mock the DB layer in sandbox tests."
                )

        # Go sandbox notes
        if a.go_components:
            lines.append(
                "- Go module dependencies: run `go mod download` before building in an offline sandbox."
            )
            lines.append(
                "- `go vet ./...` is cheap and catches real bugs — run it after every change."
            )
            if any(c in a.go_components for c in ("gorm", "ent")):
                lines.append(
                    "- Database packages require a live DB or mocked interface; do not make real DB calls in sandbox tests."
                )

        return "\n".join(lines)

    def _section_apply_patch_notes(self) -> str:
        lines = [
            "## apply_patch Usage",
            "When modifying files, prefer `apply_patch` over full-file writes for surgical changes:",
            "- Keep patches small and focused on the minimal diff.",
            "- After applying a patch, run the test command to verify correctness.",
            "- Use `apply_patch` with `create` action for new files, `modify` for existing ones.",
            "- For large structural refactors, consider writing the full new file instead of a complex patch.",
        ]
        return "\n".join(lines)

    def _section_approval_gates(self) -> str:
        a = self.analysis
        test_cmds = _test_commands(a)
        lint_cmds = _lint_commands(a)
        lines = [
            "## Approval Gates",
            "Before marking a task complete, verify ALL of the following:",
        ]

        if test_cmds:
            lines.append(f"- [ ] Tests pass: `{test_cmds[0]}`")
        elif a.swift_components:
            swift_cmds = _swift_build_commands(a)
            lines.append(f"- [ ] Tests pass: `{swift_cmds[1] if len(swift_cmds) > 1 else swift_cmds[0]}`")
        elif a.rust_components:
            lines.append("- [ ] Tests pass: `cargo test`")
        elif a.go_components:
            lines.append("- [ ] Tests pass: `go test ./...`")
        else:
            lines.append("- [ ] Tests pass (add test command here)")

        if lint_cmds:
            lines.append(f"- [ ] Linting clean: `{lint_cmds[0]}`")
        elif a.rust_components:
            lines.append("- [ ] Linting clean: `cargo clippy -- -D warnings`")
        elif a.go_components:
            lines.append("- [ ] Linting clean: `go vet ./...`")
        elif a.swift_components and "SwiftLint" in a.swift_components:
            lines.append("- [ ] Linting clean: `swiftlint lint`")

        if a.rust_components:
            lines.append("- [ ] Formatting clean: `cargo fmt --check`")
        if a.go_components:
            lines.append("- [ ] Formatting clean: `gofmt -l . | grep -q . && exit 1 || true`")

        lines += [
            "- [ ] No unintended files modified (check `git diff --stat`)",
            "- [ ] New code has corresponding tests (if behavior change)",
            "- [ ] Commit message follows the project prefix convention",
        ]

        return "\n".join(lines)

    def _section_antipatterns(self) -> str:
        lines = [
            "## Anti-Patterns to Avoid",
            "- **Do not** make network calls in the sandbox — all external calls must be mocked.",
            "- **Do not** commit secrets, API keys, or credentials.",
            "- **Do not** modify test fixtures or golden files to make tests pass without understanding why.",
            "- **Do not** introduce new dependencies without updating the lock file.",
            "- **Do not** skip linting or type-check steps — they are part of the approval gate.",
        ]
        return "\n".join(lines)
