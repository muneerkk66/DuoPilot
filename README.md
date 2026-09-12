# DuoPilot

**DuoPilot is an OpenAI-powered agent for analysing, migrating, building and validating iOS projects for iPhone Duo.**

> Current direction: **OpenAI only.** DuoPilot uses the OpenAI Agents SDK for the agent loop and MCP for local Xcode / Simulator capabilities. Google ADK is not required.

## Why OpenAI Agents SDK?

DuoPilot is not a single prompt/response workflow. A useful migration needs an iterative loop:

```text
Inspect project
    ↓
Find Duo-sensitive screens
    ↓
Modify SwiftUI / UIKit
    ↓
Build in Xcode
    ↓
Run tests
    ↓
Launch / inspect UI
    ↓
Problem found? ── yes ──> fix code ──> rebuild ──> verify again
    │
    no
    ↓
Mark verified + continue
```

The OpenAI Agents SDK manages the agent/tool loop while DuoPilot connects to local developer tooling through MCP.

## Architecture

```text
Developer
   ↓
DuoPilot CLI / future Mac app
   ↓
OpenAI Agents SDK
   ↓
DuoPilot migration instructions
   ↓
Local Xcode MCP server
   ↓
Xcode + Simulator + Tests + project files
```

The important boundary is that **Xcode stays on the developer's Mac**. DuoPilot does not require OpenAI to host Xcode. The local MCP server exposes the Xcode/Simulator operations the agent is allowed to use.

## Requirements

- macOS
- Python 3.11+
- Xcode installed
- An OpenAI API key
- A trusted MCP server that exposes the Xcode/Simulator tools you want DuoPilot to use

The exact iPhone Duo/Xcode support depends on the Xcode and SDK installed on your Mac. DuoPilot must not claim a target is verified unless the local build/runtime tools confirm it.

## Installation

```bash
git clone https://github.com/muneerkk66/DuoPilot.git
cd DuoPilot

python3 -m venv .venv
source .venv/bin/activate

pip install -e .
cp .env.example .env
```

Add your OpenAI API key to `.env`:

```bash
OPENAI_API_KEY=sk-...
```

Choose an OpenAI model available to your API project:

```bash
OPENAI_MODEL=gpt-5.6
```

## Configure Xcode MCP

DuoPilot uses the Agents SDK's local stdio MCP support. Configure the command that launches your trusted Xcode MCP server:

```bash
DUOPILOT_MCP_COMMAND=npx
DUOPILOT_MCP_ARGS='["-y","your-xcode-mcp-package"]'
```

Replace the example package with the MCP server you actually use. DuoPilot deliberately keeps this configurable rather than hard-coding an unreleased or changing Xcode integration.

## Safe first run

Code modifications are disabled by default:

```bash
DUOPILOT_ALLOW_WRITES=false
```

Run an analysis:

```bash
duopilot run /path/to/YourApp
```

Or provide a specific task:

```bash
duopilot run /path/to/YourApp \
  --task "Analyze the project for iPhone Duo compatibility. Focus on SwiftUI adaptive layout, fixed frames, safe areas, navigation and UIKit constraints. Do not modify files."
```

## Enable autonomous fixes

Once your MCP tools are trusted and you have committed/stashed your existing work:

```bash
DUOPILOT_ALLOW_WRITES=true
```

Then run:

```bash
duopilot run /path/to/YourApp \
  --task "Migrate this project for iPhone Duo. Make the smallest safe fixes, build after each logical change, run relevant tests, inspect affected UI with available simulator tools, and repeat until verified or blocked."
```

## Target tool capabilities

For the full autonomous experience, the connected local tooling should eventually expose capabilities equivalent to:

```text
project.inspect
project.read_file
project.apply_patch
xcode.build
xcode.test
simulator.list
simulator.boot
simulator.launch
simulator.screenshot
ui.inspect
```

The concrete MCP tool names may differ. DuoPilot's agent discovers and uses the tools exposed by the configured server.

## Intended validation loop

For every affected screen DuoPilot should aim for:

```text
Source inspection     ✓
Build                 ✓
Relevant tests        ✓
Runtime launch        ✓
Duo layout inspection ✓
Visual verification   ✓
```

If visual verification reports an overlap, clipped content, unsafe fixed sizing, navigation issue or other Duo-specific problem, the agent should return to the implementation, patch it and verify again.

## Current status

This repository is an early OpenAI-only foundation. The next implementation steps are:

1. Connect the actual Xcode MCP server used by the development environment.
2. Add structured Duo migration findings and a per-screen verification state.
3. Add screenshot/UI validation rules.
4. Add git diff checkpoints and human approval for risky edits.
5. Add a Mac UI showing scan progress, issues, before/after screenshots and verification status.

## Security

MCP tools execute with the permissions available on your machine. Only connect DuoPilot to MCP servers you trust. Keep write mode disabled until you have reviewed the exposed tools, and work from a clean git branch so every agent change is auditable.

## License

MIT
