"""Tests for Rust project detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentmd.detectors.rust import detect_rust_project


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_files(tmp_path: Path, structure: dict[str, str]) -> list[Path]:
    """Write files under tmp_path and return relative Path list."""
    paths: list[Path] = []
    for rel, content in structure.items():
        full = tmp_path / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        paths.append(Path(rel))
    return paths


# ---------------------------------------------------------------------------
# Project file tests
# ---------------------------------------------------------------------------

def test_detects_cargo_toml(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"Cargo.toml": '[package]\nname = "myapp"\nversion = "0.1.0"\n'})
    result = detect_rust_project(tmp_path, files)
    assert "cargo-toml" in result.values
    assert "Cargo.toml" in result.evidence.get("cargo-toml", [])


def test_detects_cargo_lock(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n',
        "Cargo.lock": "# This file is automatically @generated\n",
    })
    result = detect_rust_project(tmp_path, files)
    assert "cargo-lock" in result.values
    assert "Cargo.lock" in result.evidence.get("cargo-lock", [])


def test_detects_rust_toolchain_toml(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n',
        "rust-toolchain.toml": '[toolchain]\nchannel = "stable"\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "rust-toolchain" in result.values
    assert "rust-toolchain.toml" in result.evidence.get("rust-toolchain", [])


# ---------------------------------------------------------------------------
# Build tool tests
# ---------------------------------------------------------------------------

def test_cargo_implied_by_cargo_toml(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"Cargo.toml": '[package]\nname = "myapp"\n'})
    result = detect_rust_project(tmp_path, files)
    assert "cargo" in result.values


def test_detects_build_rs(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n',
        "build.rs": "fn main() { println!(\"cargo:rerun-if-changed=build.rs\"); }\n",
    })
    result = detect_rust_project(tmp_path, files)
    assert "build-rs" in result.values
    assert "build.rs" in result.evidence.get("build-rs", [])


def test_no_cargo_without_cargo_toml(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {"README.md": "# My project\n"})
    result = detect_rust_project(tmp_path, files)
    assert "cargo" not in result.values


# ---------------------------------------------------------------------------
# Framework / library detection
# ---------------------------------------------------------------------------

def test_detects_tokio(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n\n[dependencies]\ntokio = { version = "1", features = ["full"] }\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "tokio" in result.values
    assert "Cargo.toml" in result.evidence.get("tokio", [])


def test_detects_serde(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n\n[dependencies]\nserde = { version = "1", features = ["derive"] }\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "serde" in result.values


def test_detects_actix_web(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n\n[dependencies]\nactix-web = "4"\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "actix-web" in result.values


def test_detects_axum(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n\n[dependencies]\naxum = "0.7"\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "axum" in result.values


def test_detects_clap(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n\n[dependencies]\nclap = { version = "4", features = ["derive"] }\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "clap" in result.values


def test_detects_sqlx(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n\n[dependencies]\nsqlx = "0.7"\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "sqlx" in result.values


def test_detects_diesel(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n\n[dependencies]\ndiesel = { version = "2", features = ["postgres"] }\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "diesel" in result.values


def test_detects_rocket(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n\n[dependencies]\nrocket = "0.5"\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "rocket" in result.values


def test_detects_warp(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n\n[dependencies]\nwarp = "0.3"\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "warp" in result.values


def test_detects_bevy(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n\n[dependencies]\nbevy = "0.13"\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "bevy" in result.values


def test_no_false_positive_dep_prefix(tmp_path: Path) -> None:
    """'tokioutils' should NOT match 'tokio'."""
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n\n[dependencies]\ntokioutils = "1"\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "tokio" not in result.values


def test_no_deps_section_no_frameworks(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\nversion = "0.1.0"\n',
    })
    result = detect_rust_project(tmp_path, files)
    for dep in ["tokio", "serde", "clap", "axum", "actix-web"]:
        assert dep not in result.values


# ---------------------------------------------------------------------------
# Linter detection
# ---------------------------------------------------------------------------

def test_detects_clippy_config_file(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n',
        ".clippy.toml": 'avoid-breaking-exported-api = false\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "clippy" in result.values
    assert ".clippy.toml" in result.evidence.get("clippy", [])


def test_detects_clippy_in_cargo_toml(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n\n[lints.clippy]\nneedless_pass_by_value = "warn"\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "clippy" in result.values
    assert "Cargo.toml" in result.evidence.get("clippy", [])


def test_detects_rustfmt_toml(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n',
        "rustfmt.toml": 'max_width = 100\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "rustfmt" in result.values
    assert "rustfmt.toml" in result.evidence.get("rustfmt", [])


def test_detects_dot_rustfmt_toml(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n',
        ".rustfmt.toml": 'edition = "2021"\n',
    })
    result = detect_rust_project(tmp_path, files)
    assert "rustfmt" in result.values
    assert ".rustfmt.toml" in result.evidence.get("rustfmt", [])


# ---------------------------------------------------------------------------
# CI detection
# ---------------------------------------------------------------------------

def test_detects_cargo_in_github_actions(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n',
        ".github/workflows/ci.yml": (
            "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
            "    steps:\n      - run: cargo test\n"
        ),
    })
    result = detect_rust_project(tmp_path, files)
    assert "cargo-ci" in result.values
    assert result.evidence.get("cargo-ci")


def test_no_cargo_ci_without_cargo_in_workflow(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "Cargo.toml": '[package]\nname = "myapp"\n',
        ".github/workflows/ci.yml": (
            "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
            "    steps:\n      - run: pytest\n"
        ),
    })
    result = detect_rust_project(tmp_path, files)
    assert "cargo-ci" not in result.values


# ---------------------------------------------------------------------------
# Negative / empty project
# ---------------------------------------------------------------------------

def test_empty_project_returns_empty(tmp_path: Path) -> None:
    files = _make_files(tmp_path, {
        "README.md": "# My Project\n",
        "main.py": "print('hello')\n",
    })
    result = detect_rust_project(tmp_path, files)
    assert result.values == []
    assert result.evidence == {}


# ---------------------------------------------------------------------------
# Ordering guarantee
# ---------------------------------------------------------------------------

def test_ordering_is_deterministic(tmp_path: Path) -> None:
    """Project files come before build tools, frameworks, linters, then CI."""
    files = _make_files(tmp_path, {
        "Cargo.toml": (
            '[package]\nname = "myapp"\n\n'
            '[dependencies]\ntokio = "1"\nserde = "1"\n\n'
            '[lints.clippy]\nneedless_pass_by_value = "warn"\n'
        ),
        "Cargo.lock": "# auto-generated\n",
        "rustfmt.toml": "max_width = 100\n",
        ".github/workflows/ci.yml": "name: CI\non: [push]\nsteps:\n  - run: cargo test\n",
    })
    result = detect_rust_project(tmp_path, files)

    idx_cargo_toml = result.values.index("cargo-toml")
    idx_cargo_lock = result.values.index("cargo-lock")
    idx_cargo = result.values.index("cargo")
    idx_tokio = result.values.index("tokio")
    idx_clippy = result.values.index("clippy")
    idx_rustfmt = result.values.index("rustfmt")
    idx_ci = result.values.index("cargo-ci")

    # Project files before build tools
    assert idx_cargo_toml < idx_cargo
    assert idx_cargo_lock < idx_cargo
    # Build tools before frameworks
    assert idx_cargo < idx_tokio
    # Frameworks before linters
    assert idx_tokio < idx_clippy
    assert idx_tokio < idx_rustfmt
    # Linters before CI
    assert idx_clippy < idx_ci
    assert idx_rustfmt < idx_ci
