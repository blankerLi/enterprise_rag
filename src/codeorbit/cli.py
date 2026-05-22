from __future__ import annotations

from pathlib import Path

import typer

from .reporting import render_markdown_report
from .service import CodeOrbitService


app = typer.Typer(help="MiMo CodeOrbit repository-level AI coding assistant.")


@app.command()
def scan(repo_path: str = typer.Argument(..., help="Path to the repository to scan.")) -> None:
    """Generate and print a repository snapshot."""
    snapshot = CodeOrbitService().scan(repo_path)
    typer.echo(f"Repository: {snapshot.root}")
    typer.echo("Languages:")
    for language, count in snapshot.languages.items():
        typer.echo(f"  - {language}: {count}")
    typer.echo("Key files:")
    for path in snapshot.key_files:
        typer.echo(f"  - {path}")
    typer.echo("Test commands:")
    for command in snapshot.test_commands:
        typer.echo(f"  - {command}")


@app.command()
def run(
    repo_path: str = typer.Argument(..., help="Path to the repository to analyze."),
    task: str = typer.Option(..., "--task", "-t", help="Natural-language coding task."),
) -> None:
    """Run a full CodeOrbit analysis."""
    service = CodeOrbitService()
    result = service.run_analysis(repo_path, task)
    typer.echo(f"Run #{result.id} status: {result.status}")
    if result.error:
        typer.echo(f"Error: {result.error}")
        raise typer.Exit(code=1)
    if result.result:
        typer.echo("\nImplementation plan:")
        for index, step in enumerate(result.result.implementation_plan, start=1):
            typer.echo(f"{index}. {step}")
        typer.echo(f"\nReport: mimo-codeorbit report {result.id}")


@app.command()
def report(
    run_id: int = typer.Argument(..., help="Run ID to export."),
    output: Path | None = typer.Option(None, "--output", "-o", help="Optional Markdown output path."),
) -> None:
    """Export a Markdown report for a run."""
    run_data = CodeOrbitService().get_run(run_id)
    markdown = render_markdown_report(run_data)
    if output:
        output.write_text(markdown, encoding="utf-8")
        typer.echo(f"Wrote report to {output}")
    else:
        typer.echo(markdown)


if __name__ == "__main__":
    app()
