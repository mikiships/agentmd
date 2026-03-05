"""Base generator with common section builders."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agentmd.types import ProjectAnalysis


class BaseGenerator(ABC):
    """Shared logic for all context file generators."""

    output_filename: str = ""

    def __init__(self, analysis: ProjectAnalysis, *, minimal: bool = False) -> None:
        self.analysis = analysis
        self.minimal = minimal

    def generate(self) -> str:
        """Return the full content of the context file."""
        sections = self._build_sections_minimal() if self.minimal else self._build_sections()
        return "\n\n".join(s.strip() for s in sections if s.strip()) + "\n"

    @abstractmethod
    def _build_sections(self) -> list[str]:
        """Return ordered list of markdown sections."""

    def _build_sections_minimal(self) -> list[str]:
        """Return minimal sections: header, commands, trimmed directory structure."""
        return [
            self._section_header_minimal(),
            self._section_commands(),
            self._section_directory_structure_minimal(),
        ]

    def _section_header_minimal(self) -> str:
        """One-line header for minimal mode. Subclasses may override."""
        return f"# {self.output_filename}"

    def _section_directory_structure_minimal(self) -> str:
        """Directory structure showing only source and test directories."""
        a = self.analysis
        ds = a.directory_structure
        lines = ["## Directory Structure"]
        if ds.source_directories:
            lines.append(
                "**Source roots:** " + ", ".join(f"`{d}`" for d in ds.source_directories)
            )
        if ds.test_directories:
            lines.append(
                "**Test roots:** " + ", ".join(f"`{d}`" for d in ds.test_directories)
            )
        if not ds.source_directories and not ds.test_directories:
            lines.append(
                "_(No source or test directories detected.)_"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Shared section builders
    # ------------------------------------------------------------------

    def _section_project_overview(self) -> str:
        a = self.analysis
        lines = ["## Project Overview"]
        if a.languages:
            lines.append(f"**Primary languages:** {', '.join(a.languages)}")
        if a.frameworks:
            lines.append(f"**Frameworks/libraries:** {', '.join(a.frameworks)}")
        if a.package_managers:
            lines.append(f"**Package managers:** {', '.join(a.package_managers)}")
        if a.ci_systems:
            lines.append(f"**CI:** {', '.join(a.ci_systems)}")
        if a.directory_structure.is_monorepo:
            lines.append(
                f"**Monorepo:** yes ({'; '.join(a.directory_structure.monorepo_indicators)})"
            )
        if not a.languages and not a.frameworks:
            lines.append("_(No language or framework detected — update this section manually.)_")
        return "\n".join(lines)

    def _section_commands(self) -> str:
        a = self.analysis
        lines = ["## Build, Test, and Lint Commands"]
        test_cmds = _test_commands(a)
        lint_cmds = _lint_commands(a)
        install_cmds = _install_commands(a)

        # Swift / Rust / Go build commands (added when components are detected)
        if a.swift_components:
            swift_cmds = _swift_build_commands(a)
            lines.append("**Swift / Xcode:**")
            for cmd in swift_cmds:
                lines.append(f"```\n{cmd}\n```")
        if a.rust_components:
            rust_cmds = _rust_build_commands(a)
            lines.append("**Rust / Cargo:**")
            for cmd in rust_cmds:
                lines.append(f"```\n{cmd}\n```")
        if a.go_components:
            go_cmds = _go_build_commands(a)
            lines.append("**Go:**")
            for cmd in go_cmds:
                lines.append(f"```\n{cmd}\n```")

        if install_cmds:
            lines.append("**Install dependencies:**")
            for cmd in install_cmds:
                lines.append(f"```\n{cmd}\n```")
        if test_cmds:
            lines.append("**Run tests:**")
            for cmd in test_cmds:
                lines.append(f"```\n{cmd}\n```")
        if lint_cmds:
            lines.append("**Lint / format:**")
            for cmd in lint_cmds:
                lines.append(f"```\n{cmd}\n```")
        if not test_cmds and not lint_cmds and not install_cmds and not a.swift_components and not a.rust_components and not a.go_components:
            lines.append(
                "_(No build tooling detected. Add your commands here so agents don't guess.)_"
            )
        return "\n".join(lines)

    def _section_directory_structure(self) -> str:
        a = self.analysis
        ds = a.directory_structure
        lines = ["## Directory Structure"]
        if ds.top_level_directories:
            lines.append(
                "**Top-level directories:** "
                + ", ".join(f"`{d}`" for d in ds.top_level_directories)
            )
        if ds.source_directories:
            lines.append(
                "**Source roots:** " + ", ".join(f"`{d}`" for d in ds.source_directories)
            )
        if ds.test_directories:
            lines.append(
                "**Test roots:** " + ", ".join(f"`{d}`" for d in ds.test_directories)
            )
        gh = a.git_history
        if gh.common_directories:
            lines.append(
                "**Most-changed directories:** "
                + ", ".join(f"`{d}`" for d in gh.common_directories)
            )
        if not ds.top_level_directories:
            lines.append(
                "_(Directory structure not detected — run agentmd from the project root.)_"
            )
        return "\n".join(lines)

    def _section_conventions(self) -> str:
        a = self.analysis
        lines = ["## Conventions Inferred from Codebase"]
        gh = a.git_history
        if gh.common_message_prefixes:
            lines.append(
                "**Commit prefix style:** "
                + ", ".join(f"`{p}`" for p in gh.common_message_prefixes)
                + " (follow this pattern)"
            )
        if gh.common_file_extensions:
            lines.append(
                "**Common file extensions:** "
                + ", ".join(f"`{e}`" for e in gh.common_file_extensions)
            )
        for convention in _language_conventions(a):
            lines.append(f"- {convention}")
        # Language-specific deep conventions
        if a.swift_components:
            for c in _swift_conventions(a):
                lines.append(f"- {c}")
        if a.rust_components:
            for c in _rust_conventions(a):
                lines.append(f"- {c}")
        if a.go_components:
            for c in _go_conventions(a):
                lines.append(f"- {c}")
        if len(lines) == 1:
            lines.append("_(No conventions detected — add project-specific conventions here.)_")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _test_commands(a: ProjectAnalysis) -> list[str]:
    cmds: list[str] = []
    ds = a.directory_structure
    test_dir = ds.test_directories[0] if ds.test_directories else "tests"
    for runner in a.test_runners:
        r = runner.lower()
        if "pytest" in r:
            cmds.append(f"python3 -m pytest {test_dir}/ -x")
        elif "jest" in r:
            cmds.append("npx jest --no-coverage")
        elif "vitest" in r:
            cmds.append("npx vitest run")
        elif "mocha" in r:
            cmds.append("npx mocha")
        elif "go test" in r or r == "go":
            cmds.append("go test ./...")
        elif "cargo test" in r or r == "cargo":
            cmds.append("cargo test")
        elif "rspec" in r:
            cmds.append("bundle exec rspec")
        elif "maven" in r:
            cmds.append("mvn test")
        elif "gradle" in r:
            cmds.append("./gradlew test")
    return cmds


def _lint_commands(a: ProjectAnalysis) -> list[str]:
    cmds: list[str] = []
    for linter in a.linters:
        lint = linter.lower()
        if "ruff" in lint:
            cmds.append("ruff check . && ruff format --check .")
        elif "flake8" in lint:
            cmds.append("flake8 .")
        elif "black" in lint:
            cmds.append("black --check .")
        elif "mypy" in lint:
            cmds.append("mypy .")
        elif "eslint" in lint:
            cmds.append("npx eslint .")
        elif "prettier" in lint:
            cmds.append("npx prettier --check .")
        elif "clippy" in lint:
            cmds.append("cargo clippy -- -D warnings")
        elif "golangci" in lint or "golint" in lint:
            cmds.append("golangci-lint run")
        elif "rubocop" in lint:
            cmds.append("bundle exec rubocop")
    return cmds


def _install_commands(a: ProjectAnalysis) -> list[str]:
    cmds: list[str] = []
    for pm in a.package_managers:
        p = pm.lower()
        if "pip" in p:
            cmds.append("pip install -e '.[dev]'")
        elif "poetry" in p:
            cmds.append("poetry install")
        elif "uv" in p:
            cmds.append("uv sync")
        elif "pnpm" in p:
            cmds.append("pnpm install")
        elif "yarn" in p:
            cmds.append("yarn install")
        elif "npm" in p:
            cmds.append("npm install")
        elif "cargo" in p:
            cmds.append("cargo build")
        elif "go" in p:
            cmds.append("go mod download")
    return cmds


def _language_conventions(a: ProjectAnalysis) -> list[str]:
    conventions: list[str] = []
    langs = [lang.lower() for lang in a.languages]
    if "python" in langs:
        conventions.append("Python: use type hints on all public functions")
        conventions.append("Python: snake_case for functions/variables, PascalCase for classes")
        if "pytest" in " ".join(a.test_runners).lower():
            conventions.append("Tests: files named `test_*.py`, functions named `test_*`")
    if "typescript" in langs or "javascript" in langs:
        conventions.append(
            "JS/TS: camelCase for variables/functions, PascalCase for classes/components"
        )
        if any("jest" in r.lower() or "vitest" in r.lower() for r in a.test_runners):
            conventions.append("Tests: files named `*.test.ts` or `*.spec.ts`")
    if "go" in langs:
        conventions.append("Go: exported names are PascalCase, unexported are camelCase")
        conventions.append("Go: error handling is explicit — check every `err != nil`")
    if "rust" in langs:
        conventions.append("Rust: snake_case everywhere, SCREAMING_SNAKE_CASE for constants")
        conventions.append("Rust: prefer `?` operator over explicit `unwrap()`")
    if "ruby" in langs:
        conventions.append("Ruby: snake_case for methods/variables, CamelCase for modules/classes")
    if "swift" in langs:
        conventions.append("Swift: camelCase for variables/functions, PascalCase for types")
        conventions.append("Swift: prefer value types (struct/enum) over classes where possible")
        conventions.append("Swift: use guard-let for early returns rather than deep if-let nesting")
    return conventions


# ------------------------------------------------------------------
# Language-specific section helpers (shared across generators)
# ------------------------------------------------------------------

def _swift_build_commands(a: ProjectAnalysis) -> list[str]:
    """Return Swift/Xcode build and test commands based on detected components."""
    cmds: list[str] = []
    components = a.swift_components
    if "xcodeproj" in components or "xcworkspace" in components:
        cmds.append("xcodebuild -scheme <SchemeName> build")
        cmds.append("xcodebuild -scheme <SchemeName> test")
    if "spm" in components:
        cmds.append("swift build")
        cmds.append("swift test")
    if "SwiftLint" in components:
        cmds.append("swiftlint lint")
    if "swift-format" in components:
        cmds.append("swift-format lint --recursive .")
    # Fallback if we only know it's a Swift project
    if not cmds:
        cmds.append("swift build")
        cmds.append("swift test")
    return cmds


def _rust_build_commands(a: ProjectAnalysis) -> list[str]:
    """Return Rust/Cargo build and test commands based on detected components."""
    cmds = [
        "cargo build",
        "cargo test",
        "cargo clippy -- -D warnings",
        "cargo fmt --check",
    ]
    return cmds


def _go_build_commands(a: ProjectAnalysis) -> list[str]:
    """Return Go build and test commands based on detected components."""
    cmds = [
        "go build ./...",
        "go test ./...",
        "go vet ./...",
    ]
    if "golangci-lint" in a.go_components or any(
        "golangci" in linter.lower() for linter in a.linters
    ):
        cmds.append("golangci-lint run")
    return cmds


def _swift_conventions(a: ProjectAnalysis) -> list[str]:
    """Return Swift-specific convention lines."""
    lines: list[str] = []
    components = a.swift_components
    if "SwiftUI" in components:
        lines.append("SwiftUI: prefer `@StateObject` for owned models, `@ObservedObject` for injected ones.")
        lines.append("SwiftUI: keep View bodies thin — extract subviews and view models.")
    if "UIKit" in components:
        lines.append("UIKit: use Auto Layout with constraints or `UIStackView`; avoid hardcoded frames.")
        lines.append("UIKit: lifecycle methods (`viewDidLoad`, `viewWillAppear`) should delegate to helpers.")
    if "Combine" in components:
        lines.append("Combine: store subscriptions in `Set<AnyCancellable>`; cancel on `deinit`.")
    if "SwiftLint" in components:
        lines.append("Linting: run `swiftlint lint` before committing; config in `.swiftlint.yml`.")
    if "swift-format" in components:
        lines.append("Formatting: run `swift-format lint --recursive .`; config in `.swift-format`.")
    return lines


def _rust_conventions(a: ProjectAnalysis) -> list[str]:
    """Return Rust-specific convention lines."""
    lines = [
        "Error handling: use `?` to propagate errors; avoid `unwrap()` in library code.",
        "Clippy: run `cargo clippy -- -D warnings`; treat all warnings as errors.",
        "Formatting: run `cargo fmt` before every commit.",
        "Documentation: all public items require `///` doc comments.",
    ]
    components = a.rust_components
    frameworks = [c.lower() for c in components]
    if "tokio" in frameworks:
        lines.append("Async: use `#[tokio::main]` entry point; prefer `async/await` over raw futures.")
    if any(f in frameworks for f in ("actix-web", "axum", "rocket", "warp")):
        lines.append("Web: keep handler functions thin; extract business logic into service layers.")
    if "serde" in frameworks:
        lines.append("Serde: derive `Serialize`/`Deserialize` on data structs; use `#[serde(rename_all)]` for API compatibility.")
    if "diesel" in frameworks or "sqlx" in frameworks:
        lines.append("Database: run migrations before tests; never hard-code connection strings.")
    return lines


def _go_conventions(a: ProjectAnalysis) -> list[str]:
    """Return Go-specific convention lines."""
    lines = [
        "Error handling: always check `err != nil`; never assign errors to `_` silently.",
        "Package naming: short, lowercase, no underscores (e.g., `httputil` not `http_util`).",
        "Interfaces: define interfaces at the point of use, not in the package that implements them.",
        "Context: pass `context.Context` as the first argument to any blocking function.",
    ]
    components = a.go_components
    frameworks = [c.lower() for c in components]
    if any(f in frameworks for f in ("gin", "echo", "fiber", "chi")):
        lines.append("HTTP: keep handler functions thin; extract business logic into service/use-case layers.")
    if "gorm" in frameworks or "ent" in frameworks:
        lines.append("Database: use migrations; never hardcode connection strings; close DB on shutdown.")
    if "cobra" in frameworks:
        lines.append("CLI: keep cobra command definitions in `cmd/`; business logic in separate packages.")
    if "golangci-lint" in components:
        lines.append("Linting: run `golangci-lint run`; config in `.golangci.yml`.")
    return lines
