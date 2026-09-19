# DuoPilot

**DuoPilot is an OpenAI-powered agent for analysing, migrating, building and validating iOS projects for iPhone Duo.**

> Current direction: **OpenAI only.** DuoPilot uses the OpenAI Agents SDK. Project inspection and edits work through built-in scoped tools; an MCP server is optional for richer local Xcode integrations. Google ADK is not required.

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

The OpenAI Agents SDK manages the agent/tool loop. DuoPilot ships scoped project tools for reading, searching, analysing and (when enabled) writing source files, plus a separate local adapter for Xcode and Simulator command-line operations.

## Architecture

```text
Developer
   ↓
DuoPilot CLI / future Mac app
   ↓
OpenAI Agents SDK
   ↓
DuoPilot migration instructions
   ├─→ Scoped project tools (read/search/analyse/edit)
   └─→ Local Xcode + Simulator adapter (build/test/boot/launch/screenshot)
```

The important boundary is that **Xcode stays on the developer's Mac**. DuoPilot does not require OpenAI to host Xcode. The local adapter and any optional MCP server invoke the Xcode/Simulator operations on that Mac.

## Requirements

- macOS
- Python 3.11+
- Xcode installed
- An OpenAI API key
- Optional: a trusted MCP server for capabilities beyond the built-in local adapter

The exact iPhone Duo/Xcode support depends on the Xcode and SDK installed on your Mac. DuoPilot must not claim a target is verified unless the local build/runtime tools confirm it.

## Installation

```bash
git clone https://github.com/muneerkk66/DuoPilot.git
cd DuoPilot
./setup.sh
source .venv/bin/activate
```

`setup.sh` creates a local `.env` file. Open that file and replace the placeholder with your key:

```bash
$EDITOR .env
chmod 600 .env
```

Set this line inside `.env`:

```dotenv
OPENAI_API_KEY=sk-your-key-here
```

`.env` is listed in `.gitignore`, so Git will not track it. You can confirm that before testing:

```bash
git check-ignore -v .env
```

For a one-off test without writing the key to disk, export it only in the current shell instead:

```bash
export OPENAI_API_KEY='sk-your-key-here'
duopilot run samples/DuoSample
```

Never paste the key into source files, commit messages, or chat. If a key is ever exposed, revoke it and create a replacement in the OpenAI dashboard.

Choose an OpenAI model available to your API project if you need to override the default:

```bash
OPENAI_MODEL=gpt-5.6
```

## Optional Xcode MCP

DuoPilot's built-in tools cover normal source inspection, edits, builds, tests and basic Simulator control. If you have a trusted MCP server with additional Xcode/UI capabilities, configure its stdio command:

```bash
DUOPILOT_MCP_COMMAND=npx
DUOPILOT_MCP_ARGS='["-y","your-xcode-mcp-package"]'
```

Replace the example package with the MCP server you actually use. Leaving `DUOPILOT_MCP_COMMAND` empty is the normal setup.

## Safe first run

Code modifications are disabled by default:

```bash
DUOPILOT_ALLOW_WRITES=false
```

Run an analysis (writes are disabled by default):

```bash
duopilot run samples/DuoSample
```

The same workflow is available through the Makefile after setup:

```bash
make analyze
make fix
make build
make test
make screenshot
```

`make run` builds, boots an iPhone Simulator, installs the app and launches it. Pass `DEVICE_ID=<simulator-udid>` when you want to select a particular device. `make screenshot` waits for the first frame before capturing. It defaults to the primary display; for iPhone Duo, use the screen ID shown by `xcrun simctl io <udid> enumerate` (for example, `DISPLAY=3 make screenshot`) when the current pose places the app on the other panel.

Or provide a specific task:

```bash
duopilot run /path/to/YourApp \
  --task "Analyze the project for iPhone Duo compatibility. Focus on SwiftUI adaptive layout, fixed frames, safe areas, navigation and UIKit constraints. Do not modify files."
```

## Enable autonomous fixes

The `--fix` flag enables the write/build/Simulator loop for this run. You can also set `DUOPILOT_ALLOW_WRITES=true` in `.env` for a default.

```bash
duopilot run samples/DuoSample --fix
```

The repository includes `samples/DuoSample`, a small SwiftUI app seeded with fixed screen-width frames, `UIScreen.main.bounds.width` and an unscoped `ignoresSafeArea()` call. `setup.sh` generates its Xcode project with XcodeGen when available.

## Target tool capabilities

The built-in local tools expose capabilities equivalent to:

```text
list_project_files
read_project_file
search_project
analyze_layout
write_project_file
xcode.build
xcode.test
simulator.list
simulator.boot
simulator.install
simulator.launch
simulator.screenshot
```

An optional MCP server can add visual inspection or other tools. DuoPilot's agent discovers and uses any tools exposed by the configured server alongside the built-ins.

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

This repository is an OpenAI-only developer tool foundation. The normal flow is ready for source analysis and edits without assembling a separate filesystem service; richer visual UI inspection remains dependent on the local Xcode/MCP capabilities available on the developer's Mac.

## Security

MCP tools execute with the permissions available on your machine. Only connect DuoPilot to MCP servers you trust. Keep write mode disabled until you have reviewed the exposed tools, and work from a clean git branch so every agent change is auditable.

## License

MIT
