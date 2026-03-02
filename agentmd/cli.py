"""CLI entrypoint for agentmd."""

import typer

app = typer.Typer(help="Analyze codebases and generate agent context files.")


def main() -> None:
    """Run the CLI app."""
    app()


if __name__ == "__main__":
    main()
