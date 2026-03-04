"""CLI entrypoint for agentmd."""

from __future__ import annotations

import difflib
import json
from pathlib import Path

import typer

from agentmd.analyzer import ProjectAnalyzer
from agentmd.drift import (
    detect_drift,
    render_github_annotations,
    render_text_report,
    select_generators,
)
from agentmd.formatters import render_markdown_report
from agentmd.generators import GENERATOR_MAP
from agentmd.scorer import ContextScorer

app = typer.Typer(help="Analyze codebases and generate agent context files.", add_completion=False)


def _resolve_path(path: str | None) -> Path:
    return Path(path).resolve() if path else Path.cwd()


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------

@app.command()
def scan(
    path: str = typer.Argument(None, help="Project root (defaults to cwd)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Analyze a project and print structured findings."""
    root = _resolve_path(path)
    if not root.is_dir():
        typer.echo(f"Error: {root} is not a directory", err=True)
        raise typer.Exit(1)

    analysis = ProjectAnalyzer().analyze(root)

    if json_output:
        typer.echo(json.dumps(analysis.to_dict(), indent=2))
        return

    typer.echo(f"Scanning {root} ...\n")

    def bullet(items: list[str], label: str) -> None:
        if items:
            typer.echo(f"  {label}: {', '.join(items)}")
        else:
            typer.echo(f"  {label}: (none detected)")

    typer.echo("Project Analysis")
    typer.echo("=" * 40)
    bullet(analysis.languages, "Languages")
    bullet(analysis.frameworks, "Frameworks")
    bullet(analysis.package_managers, "Package managers")
    bullet(analysis.test_runners, "Test runners")
    bullet(analysis.linters, "Linters")
    bullet(analysis.ci_systems, "CI systems")

    ds = analysis.directory_structure
    typer.echo(f"  Monorepo: {'yes' if ds.is_monorepo else 'no'}")
    if ds.source_directories:
        typer.echo(f"  Source dirs: {', '.join(ds.source_directories)}")
    if ds.test_directories:
        typer.echo(f"  Test dirs: {', '.join(ds.test_directories)}")

    typer.echo("\nContext Files")
    typer.echo("=" * 40)
    for ctx in analysis.existing_context_files:
        status = "present" if ctx.present else "absent"
        if ctx.present:
            typer.echo(f"  [{status}] {ctx.name}  ({ctx.line_count} lines)")
        else:
            typer.echo(f"  [{status}] {ctx.name}")


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

@app.command()
def generate(
    path: str = typer.Argument(None, help="Project root (defaults to cwd)"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent name: claude, codex, cursor, copilot"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview output without writing files"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing context files"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Generate context files for AI coding agents."""
    root = _resolve_path(path)
    if not root.is_dir():
        typer.echo(f"Error: {root} is not a directory", err=True)
        raise typer.Exit(1)

    if agent and agent not in GENERATOR_MAP:
        typer.echo(f"Error: unknown agent '{agent}'. Choose from: {', '.join(GENERATOR_MAP)}", err=True)
        raise typer.Exit(1)

    agents_to_run = {agent: GENERATOR_MAP[agent]} if agent else dict(GENERATOR_MAP)
    analysis = ProjectAnalyzer().analyze(root)

    if json_output:
        result: dict = {
            "path": str(root),
            "agents": [],
            "files_written": [],
            "files_skipped": [],
            "contents": {},
        }
        for name, GeneratorClass in agents_to_run.items():
            gen = GeneratorClass(analysis)
            content = gen.generate()
            output_path = root / gen.output_filename
            result["agents"].append(name)
            result["contents"][name] = content
            if not dry_run:
                if output_path.exists() and not force:
                    result["files_skipped"].append(gen.output_filename)
                else:
                    existed = output_path.exists()
                    output_path.write_text(content, encoding="utf-8")
                    result["files_written"].append(gen.output_filename)
        typer.echo(json.dumps(result, indent=2))
        return

    for name, GeneratorClass in agents_to_run.items():
        gen = GeneratorClass(analysis)
        content = gen.generate()
        output_path = root / gen.output_filename

        if dry_run:
            typer.echo(f"\n{'=' * 60}")
            typer.echo(f"[dry-run] Would write: {output_path}")
            typer.echo(f"{'=' * 60}")
            typer.echo(content)
            continue

        if output_path.exists() and not force:
            typer.echo(f"  skip  {gen.output_filename}  (exists; use --force to overwrite)")
            continue

        existed = output_path.exists()
        output_path.write_text(content, encoding="utf-8")
        action = "overwrite" if existed else "wrote"
        typer.echo(f"  {action}  {output_path}")


# ---------------------------------------------------------------------------
# score
# ---------------------------------------------------------------------------

@app.command()
def score(
    path: str = typer.Argument(None, help="Project root or context file (defaults to cwd)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Score existing context files in a project (or a single file)."""
    resolved = _resolve_path(path)
    scorer = ContextScorer()

    # If the user passed a specific file, score just that file.
    if resolved.is_file():
        file_content = resolved.read_text(encoding="utf-8")
        project_root = str(resolved.parent)
        result = scorer.score(file_content, file_path=str(resolved), project_root=project_root)
        if json_output:
            typer.echo(json.dumps([result.to_dict()], indent=2))
        else:
            _print_score(resolved.name, result)
        return

    root = resolved
    if not root.is_dir():
        typer.echo(f"Error: {root} is not a file or directory", err=True)
        raise typer.Exit(1)

    analysis = ProjectAnalyzer().analyze(root)

    found_any = False
    results_list = []
    for ctx in analysis.existing_context_files:
        if not ctx.present:
            continue
        found_any = True
        file_path = (root / ctx.path).resolve()
        file_content = file_path.read_text(encoding="utf-8")
        result = scorer.score(file_content, file_path=str(file_path), project_root=str(root))
        if json_output:
            results_list.append(result.to_dict())
        else:
            _print_score(ctx.name, result)

    if json_output:
        typer.echo(json.dumps(results_list, indent=2))
        return

    if not found_any:
        typer.echo("No context files found. Run `agentmd generate` first.")


def _print_score(name: str, result: object) -> None:
    """Print score results for a single context file."""
    typer.echo(f"\n{name}")
    typer.echo("-" * len(name))
    for dim in result.dimensions:
        bar = "#" * int(dim.score / 10)
        typer.echo(f"  {dim.name:<18} {dim.score:5.1f}  [{bar:<10}]  weight={dim.weight:.2f}")
    typer.echo(f"  {'composite':<18} {result.composite_score:5.1f}")
    if result.suggestions:
        typer.echo("  Suggestions:")
        for s in result.suggestions:
            typer.echo(f"    - {s}")


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------

@app.command()
def diff(
    path: str = typer.Argument(None, help="Project root (defaults to cwd)"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent name: claude, codex, cursor, copilot"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show diff between existing context files and generated output."""
    root = _resolve_path(path)
    if not root.is_dir():
        typer.echo(f"Error: {root} is not a directory", err=True)
        raise typer.Exit(1)

    if agent and agent not in GENERATOR_MAP:
        typer.echo(f"Error: unknown agent '{agent}'. Choose from: {', '.join(GENERATOR_MAP)}", err=True)
        raise typer.Exit(1)

    agents_to_run = {agent: GENERATOR_MAP[agent]} if agent else dict(GENERATOR_MAP)
    analysis = ProjectAnalyzer().analyze(root)
    any_diff = False

    if json_output:
        diff_results = []
        for name, GeneratorClass in agents_to_run.items():
            gen = GeneratorClass(analysis)
            output_path = root / gen.output_filename
            generated = gen.generate()
            existing = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
            has_changes = existing != generated
            diff_str: str | None = None
            if has_changes:
                from_label = str(output_path) if output_path.exists() else f"{gen.output_filename} (new file)"
                diff_str = "".join(
                    difflib.unified_diff(
                        existing.splitlines(keepends=True),
                        generated.splitlines(keepends=True),
                        fromfile=from_label,
                        tofile=f"{gen.output_filename} (generated)",
                    )
                )
            diff_results.append({
                "file": gen.output_filename,
                "agent": name,
                "has_changes": has_changes,
                "diff": diff_str,
            })
        typer.echo(json.dumps(diff_results, indent=2))
        return

    for name, GeneratorClass in agents_to_run.items():
        gen = GeneratorClass(analysis)
        output_path = root / gen.output_filename
        generated = gen.generate()

        existing = output_path.read_text(encoding="utf-8") if output_path.exists() else ""

        if existing == generated:
            typer.echo(f"  {gen.output_filename}: no changes")
            continue

        any_diff = True
        from_label = str(output_path) if output_path.exists() else f"{gen.output_filename} (new file)"
        delta = "".join(
            difflib.unified_diff(
                existing.splitlines(keepends=True),
                generated.splitlines(keepends=True),
                fromfile=from_label,
                tofile=f"{gen.output_filename} (generated)",
            )
        )
        typer.echo(delta)

    if not any_diff:
        typer.echo("All context files are up to date.")


# ---------------------------------------------------------------------------
# drift
# ---------------------------------------------------------------------------

@app.command()
def drift(
    path: str = typer.Argument(None, help="Project root (defaults to cwd)"),
    agent: str = typer.Option(None, "--agent", "-a", help="Agent name: claude, codex, cursor, copilot"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    output_format: str = typer.Option("text", "--format", help="Output format: text, github, or markdown"),
) -> None:
    """Detect context file drift against freshly generated output."""
    root = _resolve_path(path)
    if not root.is_dir():
        typer.echo(f"Error: {root} is not a directory", err=True)
        raise typer.Exit(1)

    if agent and agent not in GENERATOR_MAP:
        typer.echo(f"Error: unknown agent '{agent}'. Choose from: {', '.join(GENERATOR_MAP)}", err=True)
        raise typer.Exit(1)

    if output_format not in {"text", "github", "markdown"}:
        typer.echo("Error: --format must be one of: text, github, markdown", err=True)
        raise typer.Exit(1)

    if json_output and output_format != "text":
        typer.echo("Error: --json cannot be combined with --format", err=True)
        raise typer.Exit(1)

    report = detect_drift(root, select_generators(agent))
    if json_output:
        typer.echo(json.dumps(report.to_dict(), indent=2))
    elif output_format == "github":
        typer.echo(render_github_annotations(report))
    elif output_format == "markdown":
        typer.echo(render_markdown_report(report))
    else:
        typer.echo(render_text_report(report))

    if report.has_drift:
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the CLI app."""
    app()


if __name__ == "__main__":
    main()
