from __future__ import annotations

import fnmatch
import re
import subprocess
from pathlib import Path
from typing import Any, Callable

from agents import function_tool


_SWIFT_SUFFIXES = {".swift", ".m", ".mm", ".h", ".storyboard", ".xib"}


def _safe_path(root: Path, relative: str) -> Path:
    """Resolve a user supplied path without allowing it to escape the project."""
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Path is outside the project root: {relative}") from exc
    return candidate


def _run(command: list[str], *, cwd: Path, timeout: int = 900) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return f"Command not available: {command[0]}"
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        return f"Command timed out after {timeout}s:\n{output}"
    output = completed.stdout.strip()
    status = "ok" if completed.returncode == 0 else f"exit {completed.returncode}"
    return f"[{status}] {' '.join(command)}\n{output}".strip()


def _simulator_destination(root: Path) -> str:
    """Select a concrete available iPhone when CoreSimulator exposes one."""
    try:
        listing = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "available"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            check=False,
        ).stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "generic/platform=iOS Simulator"
    for state in ("Booted", "Shutdown"):
        match = re.search(rf"iPhone[^\n(]* \(([0-9A-F-]+)\) \({state}\)", listing)
        if match:
            return f"id={match.group(1)}"
    return "generic/platform=iOS Simulator"


def _project_files(root: Path) -> list[Path]:
    ignored = {".git", ".build", "DerivedData", "build", "Pods"}
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        if path.suffix in _SWIFT_SUFFIXES or path.name.endswith((".xcodeproj", ".xcworkspace")):
            files.append(path)
    return sorted(files)


def layout_findings(root: Path) -> list[str]:
    """Return deterministic findings for common fixed-layout hazards."""
    rules = [
        (r"UIScreen\.main\.bounds", "UIScreen.main.bounds couples layout to one screen size; use container geometry or adaptive layout."),
        (r"\.frame\s*\(\s*width\s*:", "A fixed frame width can clip or leave excess space on Duo layouts; prefer maxWidth/minWidth or flexible stacks."),
        (r"ignoresSafeArea\s*\(\s*\)", "Unscoped ignoresSafeArea can place content under system or hinge safe areas; scope the edges and validate on device."),
        (r"\.frame\s*\(\s*height\s*:", "A fixed height may clip Dynamic Type or split layouts; prefer content-driven sizing."),
    ]
    findings: list[str] = []
    for path in _project_files(root):
        if path.suffix != ".swift":
            continue
        relative = str(path.relative_to(root))
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, 1):
            for pattern, message in rules:
                if re.search(pattern, line):
                    findings.append(f"{relative}:{number}: {message} ({line.strip()})")
    return findings


def create_local_tools(root: Path, allow_writes: bool) -> list[Callable[..., Any]]:
    """Create tools scoped to one project checkout.

    These tools intentionally use only the standard library and local Xcode command
    line tools. They keep ordinary project inspection usable without an extra
    filesystem MCP server; an optional MCP server can still add richer integrations.
    """

    @function_tool
    def list_project_files(pattern: str = "**/*") -> str:
        """List source and Xcode project files under the configured project root."""
        matches = [
            str(path.relative_to(root))
            for path in _project_files(root)
            if fnmatch.fnmatch(str(path.relative_to(root)), pattern)
        ]
        return "\n".join(matches) if matches else "No matching project files."

    @function_tool
    def read_project_file(path: str) -> str:
        """Read a UTF-8 text file inside the configured project root."""
        target = _safe_path(root, path)
        if not target.is_file():
            return f"File not found: {path}"
        try:
            return target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return f"File is not UTF-8 text: {path}"

    @function_tool
    def search_project(query: str, path_pattern: str = "**/*.swift") -> str:
        """Search Swift and UIKit source files for a text or regular expression."""
        try:
            matcher = re.compile(query, re.IGNORECASE)
            regex = True
        except re.error:
            matcher = None
            regex = False
        hits: list[str] = []
        for path in _project_files(root):
            relative = str(path.relative_to(root))
            if not fnmatch.fnmatch(relative, path_pattern):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(lines, 1):
                found = bool(matcher.search(line)) if regex and matcher else query.lower() in line.lower()
                if found:
                    hits.append(f"{relative}:{line_number}: {line.strip()}")
        return "\n".join(hits) if hits else "No matches."

    @function_tool
    def analyze_layout() -> str:
        """Find common fixed-width and safe-area patterns that break adaptive iPhone layouts."""
        findings = layout_findings(root)
        return "\n".join(findings) if findings else "No configured adaptive-layout hazards found."

    @function_tool
    def write_project_file(path: str, content: str) -> str:
        """Write a UTF-8 text file inside the project root when writes are enabled."""
        if not allow_writes:
            return "Writes are disabled. Re-run with --fix or DUOPILOT_ALLOW_WRITES=true."
        target = _safe_path(root, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {target.relative_to(root)} ({len(content)} bytes)."

    @function_tool
    def xcode_build(scheme: str = "", configuration: str = "Debug") -> str:
        """Build the first local Xcode project or workspace for the iOS Simulator."""
        project = next(root.glob("*.xcworkspace"), None) or next(root.glob("*.xcodeproj"), None)
        if not project:
            return "No .xcodeproj or .xcworkspace found in the project root."
        target_flag = "-workspace" if project.suffix == ".xcworkspace" else "-project"
        selected_scheme = scheme or project.stem
        destination = "generic/platform=iOS Simulator"
        return _run(
            ["xcodebuild", target_flag, str(project), "-scheme", selected_scheme,
             "-configuration", configuration, "-destination", destination,
             "-derivedDataPath", str(root / ".duopilot-derived"),
             "CODE_SIGNING_ALLOWED=NO", "build"],
            cwd=root,
        )

    @function_tool
    def xcode_test(scheme: str = "") -> str:
        """Run the local Xcode test scheme on the first available concrete iPhone Simulator."""
        project = next(root.glob("*.xcworkspace"), None) or next(root.glob("*.xcodeproj"), None)
        if not project:
            return "No .xcodeproj or .xcworkspace found in the project root."
        target_flag = "-workspace" if project.suffix == ".xcworkspace" else "-project"
        selected_scheme = scheme or project.stem
        return _run(
            ["xcodebuild", target_flag, str(project), "-scheme", selected_scheme,
             "-destination", _simulator_destination(root),
             "-derivedDataPath", str(root / ".duopilot-derived"),
             "CODE_SIGNING_ALLOWED=NO", "test"],
            cwd=root,
        )

    @function_tool
    def simulator_list() -> str:
        """List available local iOS Simulator devices and runtimes."""
        return _run(["xcrun", "simctl", "list", "devices", "available"], cwd=root, timeout=60)

    @function_tool
    def simulator_boot(device: str = "") -> str:
        """Boot a named simulator UDID, or the first available iPhone."""
        if device:
            return _run(["xcrun", "simctl", "boot", device], cwd=root, timeout=120)
        try:
            listing = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "available"],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return "xcrun/simctl is unavailable on this Mac."
        match = re.search(r"(iPhone[^\n(]*) \(([0-9A-F-]+)\) \(Shutdown\)", listing.stdout)
        if not match:
            return "No shutdown iPhone simulator found. Use simulator_list and pass a UDID."
        return _run(["xcrun", "simctl", "boot", match.group(2)], cwd=root, timeout=120)

    @function_tool
    def simulator_launch(bundle_id: str) -> str:
        """Launch an installed app by bundle identifier on the booted simulator."""
        return _run(["xcrun", "simctl", "launch", "booted", bundle_id], cwd=root, timeout=120)

    @function_tool
    def simulator_install(app_path: str) -> str:
        """Install a built .app bundle on the booted simulator."""
        target = _safe_path(root, app_path)
        if not target.exists():
            return f"App bundle not found: {app_path}"
        return _run(["xcrun", "simctl", "install", "booted", str(target)], cwd=root, timeout=120)

    @function_tool
    def simulator_screenshot(output_path: str = "duopilot-screenshot.png") -> str:
        """Capture a screenshot from the booted simulator into the project root."""
        target = _safe_path(root, output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        return _run(["xcrun", "simctl", "io", "booted", "screenshot", str(target)], cwd=root, timeout=120)

    return [
        list_project_files,
        read_project_file,
        search_project,
        analyze_layout,
        write_project_file,
        xcode_build,
        xcode_test,
        simulator_list,
        simulator_boot,
        simulator_install,
        simulator_launch,
        simulator_screenshot,
    ]
