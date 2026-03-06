"""Subsystem boundary detector for tiered context generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from agentmd.detectors.common import collect_project_files

# Extensions considered "source code" for counting purposes.
SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".rs", ".go", ".rb", ".java", ".kt", ".swift",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".scala",
}

# Manifest files that indicate a package boundary.
PACKAGE_MANIFESTS = {
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt",
    "package.json", "Cargo.toml", "go.mod", "Gemfile",
    "pom.xml", "build.gradle", "build.gradle.kts",
}

# Minimum number of source files for a directory to be a candidate subsystem.
MIN_SOURCE_FILES = 3

# Project size thresholds — below these, tiered mode is unnecessary.
MIN_PROJECT_SOURCE_FILES = 20
MIN_PROJECT_LINES = 2000


@dataclass
class SubsystemInfo:
    """Describes a detected subsystem directory."""

    name: str
    path: str
    file_count: int
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)


def _count_lines(root: Path, rel_path: Path) -> int:
    """Count lines in a source file, returning 0 on error."""
    try:
        return len((root / rel_path).read_text(encoding="utf-8").splitlines())
    except (OSError, UnicodeDecodeError):
        return 0


def _detect_languages_for_files(files: list[Path]) -> list[str]:
    """Infer languages from file extensions."""
    ext_to_lang: dict[str, str] = {
        ".py": "Python",
        ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
        ".ts": "TypeScript", ".tsx": "TypeScript",
        ".rs": "Rust",
        ".go": "Go",
        ".rb": "Ruby",
        ".java": "Java",
        ".kt": "Kotlin",
        ".swift": "Swift",
        ".c": "C", ".cpp": "C++", ".h": "C", ".hpp": "C++",
        ".cs": "C#",
        ".scala": "Scala",
    }
    langs: set[str] = set()
    for f in files:
        lang = ext_to_lang.get(f.suffix.lower())
        if lang:
            langs.add(lang)
    return sorted(langs)


def _detect_frameworks_for_dir(root: Path, dir_path: str, files: list[Path]) -> list[str]:
    """Lightweight framework detection for a subsystem directory."""
    frameworks: list[str] = []
    names = {f.name for f in files}

    if "package.json" in names:
        try:
            content = (root / dir_path / "package.json").read_text(encoding="utf-8")
            for fw, marker in [("React", "react"), ("Next.js", "next"),
                               ("Vue", "vue"), ("Express", "express"),
                               ("Fastify", "fastify")]:
                if f'"{marker}"' in content:
                    frameworks.append(fw)
        except (OSError, UnicodeDecodeError):
            pass

    if "Cargo.toml" in names:
        try:
            content = (root / dir_path / "Cargo.toml").read_text(encoding="utf-8")
            for fw, marker in [("Actix", "actix"), ("Axum", "axum"),
                               ("Tokio", "tokio"), ("Serde", "serde")]:
                if marker in content:
                    frameworks.append(fw)
        except (OSError, UnicodeDecodeError):
            pass

    if "go.mod" in names:
        try:
            content = (root / dir_path / "go.mod").read_text(encoding="utf-8")
            for fw, marker in [("Gin", "gin-gonic"), ("Echo", "labstack/echo"),
                               ("Chi", "go-chi/chi")]:
                if marker in content:
                    frameworks.append(fw)
        except (OSError, UnicodeDecodeError):
            pass

    # Check for pyproject.toml or requirements.txt
    for manifest in ("pyproject.toml", "requirements.txt", "setup.py"):
        if manifest in names:
            try:
                content = (root / dir_path / manifest).read_text(encoding="utf-8")
                for fw, marker in [("FastAPI", "fastapi"), ("Django", "django"),
                                   ("Flask", "flask"), ("SQLAlchemy", "sqlalchemy")]:
                    if marker in content.lower():
                        frameworks.append(fw)
            except (OSError, UnicodeDecodeError):
                pass

    return sorted(set(frameworks))


def is_project_too_small(root: Path, files: list[Path] | None = None) -> bool:
    """Return True if the project is too small for tiered context."""
    if files is None:
        files = collect_project_files(root)

    source_files = [f for f in files if f.suffix.lower() in SOURCE_EXTENSIONS]
    if len(source_files) < MIN_PROJECT_SOURCE_FILES:
        return True

    total_lines = 0
    for f in source_files:
        total_lines += _count_lines(root, f)
        if total_lines >= MIN_PROJECT_LINES:
            return False
    return True


def detect_subsystems(root: Path, files: list[Path] | None = None) -> list[SubsystemInfo]:
    """Identify subsystem boundaries in a project directory.

    A subsystem is a directory containing at least MIN_SOURCE_FILES source files
    or containing a package manifest file.
    """
    if files is None:
        files = collect_project_files(root)

    # Group source files by their top-level (or second-level under src/) directory.
    dir_files: dict[str, list[Path]] = {}
    for f in files:
        if f.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        parts = f.parts
        if len(parts) < 2:
            continue  # Top-level files don't form subsystems

        # For src/<subdir>/... patterns, use src/<subdir> as the subsystem path
        # but name it after the subdir.
        if parts[0].lower() in ("src", "lib", "pkg", "cmd", "apps", "services", "packages"):
            if len(parts) >= 3:
                dir_key = str(Path(parts[0]) / parts[1])
            else:
                dir_key = parts[0]
        else:
            dir_key = parts[0]

        dir_files.setdefault(dir_key, []).append(f)

    # Also check for package manifest boundaries (monorepo packages)
    for f in files:
        if f.name in PACKAGE_MANIFESTS and len(f.parts) >= 2:
            parent_dir = str(f.parent)
            if parent_dir not in dir_files:
                # Collect source files under this directory
                src_files = [
                    sf for sf in files
                    if sf.suffix.lower() in SOURCE_EXTENSIONS
                    and str(sf).startswith(parent_dir + "/")
                ]
                if src_files:
                    dir_files[parent_dir] = src_files

    subsystems: list[SubsystemInfo] = []
    for dir_path, src_files in sorted(dir_files.items()):
        if len(src_files) < MIN_SOURCE_FILES:
            continue

        # Derive a clean name from the directory path
        path_obj = Path(dir_path)
        name = path_obj.name  # Use the last component as the name

        languages = _detect_languages_for_files(src_files)
        frameworks = _detect_frameworks_for_dir(root, dir_path, src_files)

        subsystems.append(SubsystemInfo(
            name=name,
            path=dir_path,
            file_count=len(src_files),
            languages=languages,
            frameworks=frameworks,
        ))

    return subsystems
