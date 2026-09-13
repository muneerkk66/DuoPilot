from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from .config import Settings
from .prompts import DUOPILOT_INSTRUCTIONS
from .tools import create_local_tools


@asynccontextmanager
async def xcode_mcp(settings: Settings) -> AsyncIterator[MCPServerStdio | None]:
    if not settings.mcp_command:
        yield None
        return

    async with MCPServerStdio(
        name="DuoPilot Xcode MCP",
        params={
            "command": settings.mcp_command,
            "args": settings.mcp_args,
        },
        cache_tools_list=True,
    ) as server:
        yield server


def build_agent(settings: Settings, project_path: Path, mcp_server=None) -> Agent:
    write_policy = (
        "Project modification is ENABLED. You may use trusted MCP tools to edit files when needed."
        if settings.allow_writes
        else "Project modification is DISABLED. Do not use any tool that changes project files."
    )

    instructions = (
        DUOPILOT_INSTRUCTIONS
        + f"\n\nProject root: {project_path.resolve()}\n{write_policy}"
    )

    kwargs = {
        "name": "DuoPilot",
        "instructions": instructions,
        "model": settings.model,
        "tools": create_local_tools(project_path, settings.allow_writes),
    }
    if mcp_server is not None:
        kwargs["mcp_servers"] = [mcp_server]

    return Agent(**kwargs)


async def run_duopilot(project_path: Path, task: str, settings: Settings) -> str:
    project_path = project_path.resolve()
    async with xcode_mcp(settings) as server:
        agent = build_agent(settings, project_path, server)
        result = await Runner.run(agent, task)
        return str(result.final_output)
