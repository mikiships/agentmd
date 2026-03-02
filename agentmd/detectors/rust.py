"""Rust project detection heuristics."""

from __future__ import annotations

from pathlib import Path

from agentmd.detectors.common import read_text
from agentmd.types import DetectorFindings

# Ordered lists for deterministic output
PROJECT_FILE_ORDER = ["cargo-toml", "cargo-lock", "rust-toolchain"]
BUILD_TOOL_ORDER = ["cargo", "build-rs"]
FRAMEWORK_ORDER = [
    "tokio", "actix-web", "rocket", "serde", "clap", "warp", "axum",
    "bevy", "diesel", "sqlx",
]
LINTER_ORDER = ["clippy", "rustfmt"]
CI_ORDER = ["cargo-ci"]

KNOWN_DEPS = [
    "tokio", "actix-web", "rocket", "serde", "clap", "warp", "axum",
    "bevy", "diesel", "sqlx",
]


def detect_rust_project(root: Path, files: list[Path]) -> DetectorFindings:
    """Detect Rust project files, frameworks, build tools, linters, and CI usage."""
    detected: set[str] = set()
    evidence: dict[str, list[str]] = {}

    file_names = {path.name for path in files}

    # --- Project file detection ---
    if "Cargo.toml" in file_names:
        detected.add("cargo-toml")
        evidence.setdefault("cargo-toml", []).append("Cargo.toml")

    if "Cargo.lock" in file_names:
        detected.add("cargo-lock")
        evidence.setdefault("cargo-lock", []).append("Cargo.lock")

    if "rust-toolchain.toml" in file_names:
        detected.add("rust-toolchain")
        evidence.setdefault("rust-toolchain", []).append("rust-toolchain.toml")

    # --- Build tool detection ---
    # cargo is implied by Cargo.toml
    if "cargo-toml" in detected:
        detected.add("cargo")
        evidence.setdefault("cargo", []).append("Cargo.toml")

    if "build.rs" in file_names:
        detected.add("build-rs")
        evidence.setdefault("build-rs", []).append("build.rs")

    # --- Framework/library detection via Cargo.toml [dependencies] ---
    cargo_toml_path = root / "Cargo.toml"
    if cargo_toml_path.exists():
        content = read_text(cargo_toml_path, max_chars=50000)
        if content:
            in_deps_section = False
            for line in content.splitlines():
                stripped = line.strip()
                # Section headers
                if stripped.startswith("["):
                    # Match [dependencies], [dev-dependencies], [build-dependencies]
                    # and workspace variants
                    lower = stripped.lower()
                    in_deps_section = "dependencies" in lower
                    continue
                if in_deps_section and stripped and not stripped.startswith("#"):
                    for dep in KNOWN_DEPS:
                        if dep not in detected:
                            # Match "dep = ..." or "dep.workspace = ..." etc.
                            if stripped.startswith(dep) and (
                                len(stripped) == len(dep)
                                or stripped[len(dep)] in (" ", "=", ".")
                            ):
                                detected.add(dep)
                                evidence.setdefault(dep, []).append("Cargo.toml")

            # Also check for clippy config in Cargo.toml
            if "[lints.clippy]" in content or "[workspace.lints.clippy]" in content:
                detected.add("clippy")
                evidence.setdefault("clippy", []).append("Cargo.toml")

    # --- Linter detection ---
    if ".clippy.toml" in file_names:
        detected.add("clippy")
        evidence.setdefault("clippy", []).append(".clippy.toml")

    if "rustfmt.toml" in file_names:
        detected.add("rustfmt")
        evidence.setdefault("rustfmt", []).append("rustfmt.toml")

    if ".rustfmt.toml" in file_names:
        detected.add("rustfmt")
        evidence.setdefault("rustfmt", []).append(".rustfmt.toml")

    # --- CI: cargo commands in GitHub Actions workflows ---
    workflow_files = [
        root / path
        for path in files
        if str(path).startswith(".github/workflows/") and path.suffix in {".yml", ".yaml"}
    ]
    for wf in workflow_files:
        content = read_text(wf, max_chars=20000)
        if content and "cargo" in content:
            detected.add("cargo-ci")
            evidence.setdefault("cargo-ci", []).append(str(wf.relative_to(root)))
            break

    # Build ordered values list
    order = (
        PROJECT_FILE_ORDER
        + BUILD_TOOL_ORDER
        + FRAMEWORK_ORDER
        + LINTER_ORDER
        + CI_ORDER
    )
    values = [item for item in order if item in detected]
    trimmed_evidence = {k: sorted(set(v))[:5] for k, v in evidence.items() if k in detected}
    return DetectorFindings(values=values, evidence=trimmed_evidence)
