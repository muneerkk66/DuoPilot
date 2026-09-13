#!/usr/bin/env bash
set -euo pipefail

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$repo_root"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "DuoPilot's local Xcode and Simulator tools require macOS." >&2
  exit 1
fi

command -v python3 >/dev/null || { echo "Install Python 3.11+ first." >&2; exit 1; }
python3 -m venv .venv
"$repo_root/.venv/bin/python" -m pip install --upgrade pip
"$repo_root/.venv/bin/pip" install -e .

if command -v xcodegen >/dev/null; then
  xcodegen generate --spec samples/DuoSample/project.yml --project samples/DuoSample
else
  echo "xcodegen is not installed; the sample source is ready, but generate the Xcode project with: brew install xcodegen"
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example. Add OPENAI_API_KEY before running DuoPilot."
fi

echo
echo "Setup complete. Activate with: source .venv/bin/activate"
echo "Analyse the sample: duopilot run samples/DuoSample"
echo "Enable the autonomous fix loop: duopilot run samples/DuoSample --fix"
