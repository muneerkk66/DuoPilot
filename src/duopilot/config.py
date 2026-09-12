from __future__ import annotations

import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    model: str
    mcp_command: str | None
    mcp_args: list[str]
    allow_writes: bool


def load_settings() -> Settings:
    load_dotenv()

    model = os.getenv("OPENAI_MODEL", "gpt-5.6")
    mcp_command = os.getenv("DUOPILOT_MCP_COMMAND")
    raw_args = os.getenv("DUOPILOT_MCP_ARGS", "[]")
    try:
        mcp_args = json.loads(raw_args)
    except json.JSONDecodeError as exc:
        raise RuntimeError("DUOPILOT_MCP_ARGS must be a JSON array") from exc

    if not isinstance(mcp_args, list) or not all(isinstance(x, str) for x in mcp_args):
        raise RuntimeError("DUOPILOT_MCP_ARGS must be a JSON array of strings")

    allow_writes = os.getenv("DUOPILOT_ALLOW_WRITES", "false").lower() in {
        "1", "true", "yes", "on"
    }

    return Settings(
        model=model,
        mcp_command=mcp_command,
        mcp_args=mcp_args,
        allow_writes=allow_writes,
    )
