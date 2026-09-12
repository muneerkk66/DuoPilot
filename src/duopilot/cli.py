from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from .agent import run_duopilot
from .config import load_settings

app = typer.Typer(help="DuoPilot — OpenAI-powered iPhone Duo migration agent")
console = Console()


@app.command()
def run(
    project: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    task: str = typer.Option(
        "Analyze this iOS project for iPhone Duo compatibility, propose required changes, and verify what you can with the available Xcode tools.",
        "--task",
        "-t",
    ),
) -> None:
    """Run DuoPilot against an iOS project."""
    settings = load_settings()
    console.print(
        Panel.fit(
            f"Project: {project.resolve()}\nModel: {settings.model}\nWrites: {'enabled' if settings.allow_writes else 'disabled'}",
            title="DuoPilot",
        )
    )
    result = asyncio.run(run_duopilot(project, task, settings))
    console.print(result)


if __name__ == "__main__":
    app()
