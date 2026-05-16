from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "proof" / "runtime" / "submodule-stack.json"

EXPECTED = [
    {
        "path": "upstream/OrcaSlicer",
        "url": "https://github.com/OrcaSlicer/OrcaSlicer.git",
        "license": "AGPL-3.0",
        "role": "Direct OrcaSlicer CLI, profile, and UI behavior reference.",
    },
    {
        "path": "upstream/FlsunSlicer",
        "url": "https://github.com/Flsun3d/FlsunSlicer.git",
        "license": "AGPL-3.0",
        "role": "FLSUN slicer and vendor profile behavior reference.",
    },
    {
        "path": "upstream/JusPrin",
        "url": "https://github.com/TheSpaghettiDetective/JusPrin.git",
        "license": "AGPL-3.0",
        "role": "GenAI slicing pattern reference.",
    },
    {
        "path": "upstream/PrusaSlicer",
        "url": "https://github.com/prusa3d/PrusaSlicer.git",
        "license": "AGPL-3.0",
        "role": "PrusaSlicer ancestry and CLI/profile behavior reference.",
    },
    {
        "path": "upstream/hermes-agent",
        "url": "https://github.com/NousResearch/hermes-agent.git",
        "license": "MIT",
        "role": "Hermes Agent tool, plugin, MCP, and orchestration reference.",
        "required_describe": "v2026.5.16",
        "required_package_version": "0.14.0",
    },
    {
        "path": "upstream/mcp-python-sdk",
        "url": "https://github.com/modelcontextprotocol/python-sdk.git",
        "license": "MIT",
        "role": "Official Model Context Protocol Python SDK reference.",
    },
    {
        "path": "upstream/moonraker",
        "url": "https://github.com/Arksine/moonraker.git",
        "license": "GPL-3.0",
        "role": "Klipper Web API server reference.",
    },
    {
        "path": "upstream/OctoPrint",
        "url": "https://github.com/OctoPrint/OctoPrint.git",
        "license": "AGPL-3.0",
        "role": "OctoPrint web UI and plugin/API reference.",
    },
    {
        "path": "upstream/klipper",
        "url": "https://github.com/Klipper3d/klipper.git",
        "license": "GPL-3.0",
        "role": "Klipper firmware and host protocol reference.",
    },
]


def run_git(path: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return result.returncode, result.stdout.strip()


def read_hermes_version(path: Path) -> str | None:
    pyproject = path / "pyproject.toml"
    init_py = path / "hermes_cli" / "__init__.py"
    version_pattern = re.compile(r'(?m)^(?:version\s*=|__version__\s*=)\s*"([^"]+)"')
    for file_path in (pyproject, init_py):
        if not file_path.exists():
            continue
        match = version_pattern.search(file_path.read_text(encoding="utf-8", errors="ignore"))
        if match:
            return match.group(1)
    return None


def validate() -> dict[str, object]:
    errors: list[str] = []
    submodules: list[dict[str, object]] = []

    for expected in EXPECTED:
        rel_path = expected["path"]
        path = ROOT / rel_path
        entry: dict[str, object] = {
            "path": rel_path,
            "expected_url": expected["url"],
            "license": expected["license"],
            "role": expected["role"],
            "exists": path.exists(),
        }

        if not path.exists():
            errors.append(f"{rel_path}: path missing")
            submodules.append(entry)
            continue

        for key, args in {
            "remote_url": ("remote", "get-url", "origin"),
            "commit": ("rev-parse", "HEAD"),
            "describe": ("describe", "--tags", "--always", "--dirty"),
            "branch": ("branch", "--show-current"),
            "status": ("status", "--short"),
        }.items():
            code, output = run_git(path, *args)
            entry[key] = output
            if code != 0:
                errors.append(f"{rel_path}: git {' '.join(args)} failed: {output}")

        if entry.get("remote_url") != expected["url"]:
            errors.append(f"{rel_path}: remote URL mismatch")

        commit = str(entry.get("commit", ""))
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            errors.append(f"{rel_path}: commit is not a 40-char SHA")

        if str(entry.get("describe", "")).endswith("-dirty") or entry.get("status"):
            errors.append(f"{rel_path}: submodule worktree is dirty")

        required_describe = expected.get("required_describe")
        if required_describe and entry.get("describe") != required_describe:
            errors.append(f"{rel_path}: expected describe {required_describe}")

        required_version = expected.get("required_package_version")
        if required_version:
            package_version = read_hermes_version(path)
            entry["package_version"] = package_version
            if package_version != required_version:
                errors.append(f"{rel_path}: expected package version {required_version}")

        submodules.append(entry)

    return {
        "status": "passed" if not errors else "failed",
        "submodules": submodules,
        "errors": errors,
    }


def main() -> int:
    report = validate()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
