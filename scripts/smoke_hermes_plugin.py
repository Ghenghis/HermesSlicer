from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.proof import log_event, write_json  # noqa: E402

PLUGIN_NAME = "hermes-slicer"
TOOL_NAME = "hermes_agent_tools"
TOOLSET = "hermes_agent"
EXPECTED_HERMES_PACKAGE_VERSION = "0.14.0"
EXPECTED_HERMES_RELEASE_TAG = "v2026.5.16"
EXPECTED_HERMES_RELEASE_DATE = "2026.5.16"
PROJECT_PLUGIN_DIR = ROOT / ".hermes" / "plugins" / PLUGIN_NAME
INTEGRATION_PLUGIN_DIR = ROOT / "integrations" / PLUGIN_NAME
REPORT_PATH = ROOT / "proof" / "runtime" / "hermes-plugin-smoke.json"


class FakeHermesContext:
    def __init__(self) -> None:
        self.tools: list[dict[str, Any]] = []

    def register_tool(self, **kwargs: Any) -> None:
        self.tools.append(kwargs)


def run_command(args: list[str], cwd: Path = ROOT, timeout: int = 30) -> dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "status": "blocked",
            "args": args,
            "error_type": type(exc).__name__,
            "reason": str(exc),
        }
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "args": args,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def load_plugin_module(plugin_dir: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(
        module_name,
        plugin_dir / "__init__.py",
        submodule_search_locations=[str(plugin_dir)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load plugin module from {plugin_dir}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def local_registration_smoke(plugin_dir: Path) -> dict[str, Any]:
    required_files = [plugin_dir / "plugin.yaml", plugin_dir / "__init__.py"]
    missing = [str(path.relative_to(ROOT)) for path in required_files if not path.exists()]
    if missing:
        return {
            "status": "failed",
            "plugin_dir": str(plugin_dir.relative_to(ROOT)),
            "reason": "Required Hermes plugin files are missing.",
            "missing": missing,
        }

    previous_root = os.environ.get("HERMES_SLICER_ROOT")
    os.environ["HERMES_SLICER_ROOT"] = str(ROOT)
    try:
        module = load_plugin_module(plugin_dir, f"hermes_slicer_smoke_{plugin_dir.parent.name}_{plugin_dir.name}")
        ctx = FakeHermesContext()
        module.register(ctx)
    except Exception as exc:
        return {
            "status": "failed",
            "plugin_dir": str(plugin_dir.relative_to(ROOT)),
            "reason": f"Plugin register(ctx) failed: {type(exc).__name__}: {exc}",
        }
    finally:
        if previous_root is None:
            os.environ.pop("HERMES_SLICER_ROOT", None)
        else:
            os.environ["HERMES_SLICER_ROOT"] = previous_root

    selected = [tool for tool in ctx.tools if tool.get("name") == TOOL_NAME]
    if not selected:
        return {
            "status": "failed",
            "plugin_dir": str(plugin_dir.relative_to(ROOT)),
            "reason": f"Plugin did not register {TOOL_NAME}.",
            "registered_tools": ctx.tools,
        }

    tool = selected[0]
    schema = tool.get("schema", {})
    actions = schema.get("parameters", {}).get("properties", {}).get("action", {}).get("enum", [])
    checks = {
        "toolset": tool.get("toolset") == TOOLSET,
        "handler_callable": callable(tool.get("handler")),
        "has_export_preflight": "export_preflight" in actions,
        "has_hermes_proof_mcp": "hermes_proof_mcp" in actions,
    }
    status = "passed" if all(checks.values()) else "failed"
    return {
        "status": status,
        "plugin_dir": str(plugin_dir.relative_to(ROOT)),
        "registered_tool": {
            "name": tool.get("name"),
            "toolset": tool.get("toolset"),
            "description": tool.get("description"),
            "action_count": len(actions),
        },
        "checks": checks,
    }


def parse_hermes_version(text: str) -> dict[str, Any]:
    match = re.search(r"Hermes Agent v(?P<version>[0-9.]+)\s+\((?P<date>[^)]+)\)", text)
    if not match:
        return {"version": "", "release_date": "", "matches_expected": False}
    version = match.group("version")
    release_date = match.group("date")
    return {
        "version": version,
        "release_date": release_date,
        "expected_package_version": EXPECTED_HERMES_PACKAGE_VERSION,
        "expected_release_tag": EXPECTED_HERMES_RELEASE_TAG,
        "matches_expected": version == EXPECTED_HERMES_PACKAGE_VERSION and release_date == EXPECTED_HERMES_RELEASE_DATE,
    }


def parse_plugin_list(text: str) -> dict[str, Any]:
    for line in text.splitlines():
        if PLUGIN_NAME in line:
            lowered = line.lower()
            return {
                "listed": True,
                "enabled": "enabled" in lowered and "not enabled" not in lowered,
                "line": line.strip(),
            }
    return {"listed": False, "enabled": False, "line": ""}


def active_cli_probe() -> dict[str, Any]:
    hermes_path = shutil.which("hermes") or shutil.which("hermes.exe")
    if not hermes_path:
        return {
            "status": "blocked",
            "available": False,
            "reason": "No active hermes CLI was found on PATH.",
            "required": ["active Hermes Agent CLI", EXPECTED_HERMES_RELEASE_TAG],
        }

    version_result = run_command([hermes_path, "version"])
    version = parse_hermes_version(version_result.get("stdout", ""))
    list_result = run_command([hermes_path, "plugins", "list"])
    plugin_list = parse_plugin_list(list_result.get("stdout", ""))
    version_ok = bool(version.get("matches_expected"))
    plugin_ok = bool(plugin_list.get("listed") and plugin_list.get("enabled"))

    reasons: list[str] = []
    if not version_ok:
        observed = version.get("version") or "unknown"
        observed_date = version.get("release_date") or "unknown"
        reasons.append(
            f"Active Hermes CLI is v{observed} ({observed_date}); expected {EXPECTED_HERMES_RELEASE_TAG} / package {EXPECTED_HERMES_PACKAGE_VERSION}."
        )
    if not plugin_list.get("listed"):
        reasons.append("Active Hermes plugins list does not include hermes-slicer.")
    elif not plugin_list.get("enabled"):
        reasons.append("Active Hermes plugins list includes hermes-slicer but it is not enabled.")

    return {
        "status": "passed" if version_ok and plugin_ok else "blocked",
        "available": True,
        "path": hermes_path,
        "version_command": version_result,
        "plugins_list_command": list_result,
        "version": version,
        "plugin": plugin_list,
        "reason": " ".join(reasons) if reasons else "Active Hermes CLI and plugin gate passed.",
        "required": [
            EXPECTED_HERMES_RELEASE_TAG,
            "active hermes CLI sees hermes-slicer",
            "hermes plugins enable hermes-slicer",
        ],
    }


def active_project_plugin_harness() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="hermes-slicer-plugin-smoke-") as temp_root:
        temp_root_path = Path(temp_root)
        hermes_home = temp_root_path / "hermes-home"
        project_root = temp_root_path / "project"
        project_plugin_dir = project_root / ".hermes" / "plugins" / PLUGIN_NAME
        hermes_home.mkdir(parents=True)
        project_plugin_dir.parent.mkdir(parents=True)
        shutil.copytree(PROJECT_PLUGIN_DIR, project_plugin_dir)
        (hermes_home / "config.yaml").write_text(
            "plugins:\n  enabled:\n    - hermes-slicer\n",
            encoding="utf-8",
        )

        code = """
import json
from hermes_cli.plugins import discover_plugins, get_plugin_manager

discover_plugins(force=True)
plugins = get_plugin_manager().list_plugins()
selected = [
    plugin for plugin in plugins
    if plugin.get("name") == "hermes-slicer" or plugin.get("key") == "hermes-slicer"
]
status = (
    "passed"
    if selected and selected[0].get("enabled") and selected[0].get("tools", 0) >= 1 and not selected[0].get("error")
    else "failed"
)
print(json.dumps({"status": status, "selected": selected, "plugins_seen": len(plugins)}, sort_keys=True))
raise SystemExit(0 if status == "passed" else 2)
""".strip()
        env = os.environ.copy()
        env["HERMES_HOME"] = str(hermes_home)
        env["HERMES_ENABLE_PROJECT_PLUGINS"] = "1"
        env["HERMES_SLICER_ROOT"] = str(ROOT)
        env.setdefault("PYTHONIOENCODING", "utf-8")
        try:
            completed = subprocess.run(
                [sys.executable, "-c", code],
                cwd=str(project_root),
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=45,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {
                "status": "blocked",
                "reason": f"Could not run isolated active Hermes plugin harness: {type(exc).__name__}: {exc}",
            }
        try:
            parsed = json.loads(completed.stdout.strip().splitlines()[-1]) if completed.stdout.strip() else {}
        except (IndexError, json.JSONDecodeError):
            parsed = {}
        return {
            "status": parsed.get("status", "failed") if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "parsed": parsed,
        }


def build_report() -> dict[str, Any]:
    project_registration = local_registration_smoke(PROJECT_PLUGIN_DIR)
    integration_registration = local_registration_smoke(INTEGRATION_PLUGIN_DIR)
    active_cli = active_cli_probe()
    harness = active_project_plugin_harness() if PROJECT_PLUGIN_DIR.exists() else {"status": "failed", "reason": "Project plugin wrapper is missing."}

    local_failed = [
        result
        for result in (project_registration, integration_registration)
        if result.get("status") != "passed"
    ]
    if local_failed:
        status = "failed"
        reason = "One or more committed Hermes plugin wrappers failed local register(ctx) smoke."
    elif active_cli.get("status") == "passed" and harness.get("status") == "passed":
        status = "passed"
        reason = "Active Hermes CLI, project plugin harness, and committed wrappers passed."
    else:
        status = "blocked"
        reason = active_cli.get("reason") or "Active Hermes plugin gate is blocked by external install/config state."

    return {
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "plugin": PLUGIN_NAME,
        "reason": reason,
        "required": [
            EXPECTED_HERMES_RELEASE_TAG,
            "HERMES_ENABLE_PROJECT_PLUGINS=1 for project plugin loading",
            "hermes plugins enable hermes-slicer in the active Hermes install",
        ],
        "committed_project_plugin": project_registration,
        "integration_plugin": integration_registration,
        "active_hermes_cli": active_cli,
        "isolated_active_project_plugin_harness": harness,
    }


def main() -> int:
    report = build_report()
    write_json(REPORT_PATH, report)
    log_event(
        "proof",
        "hermes.plugin_smoke",
        report["status"],
        outputs={
            "status": report["status"],
            "active_hermes_status": report["active_hermes_cli"]["status"],
            "project_harness_status": report["isolated_active_project_plugin_harness"]["status"],
        },
        proof_files=["proof/runtime/hermes-plugin-smoke.json"],
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
