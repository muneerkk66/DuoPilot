from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from .agent import run_duopilot
from .config import load_settings
from .tools import layout_findings

app = typer.Typer(help="DuoPilot — OpenAI-powered iPhone Duo migration agent", no_args_is_help=True)
console = Console()


@app.callback()
def main() -> None:
    """Run the OpenAI-only iPhone Duo migration agent."""


@app.command()
def run(
    project: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    task: str = typer.Option(
        "Analyze this iOS project for iPhone Duo compatibility. Inspect the source, identify adaptive-layout issues, and verify with local Xcode and Simulator tools. If writes are enabled, fix issues, rebuild, run tests, capture a screenshot, inspect the UI, and repeat until verified or blocked.",
        "--task",
        "-t",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Allow DuoPilot to edit project files and run the fix/build/verify loop.",
    ),
) -> None:
    """Run DuoPilot against an iOS project."""
    settings = load_settings()
    if fix:
        settings = settings.with_writes(True)
    console.print(
        Panel.fit(
            f"Project: {project.resolve()}\nModel: {settings.model}\nWrites: {'enabled' if settings.allow_writes else 'disabled'}",
            title="DuoPilot",
        )
    )
    findings = layout_findings(project.resolve())
    if findings:
        console.print(Panel("\n".join(findings), title="Local adaptive-layout scan"))
    try:
        result = asyncio.run(run_duopilot(project, task, settings))
    except Exception as exc:
        console.print(f"[red]DuoPilot failed:[/] {exc}")
        raise typer.Exit(code=1) from exc
    console.print(result)


if __name__ == "__main__":
    app()
