from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BRIDGE_URL = os.environ.get("HERMES_SLICER_BRIDGE_URL", "http://127.0.0.1:8765").rstrip("/")
ROOT = Path(os.environ.get("HERMES_SLICER_ROOT", Path(__file__).resolve().parents[1])).resolve()
sys.path.insert(0, str(ROOT))

try:
    from hermes_slicer.proof import log_event, write_json  # noqa: E402
except Exception:  # pragma: no cover - used when copied outside the repo without package install.
    def log_event(*args, **kwargs):
        return None

    def write_json(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


TOOL_NAME = "slicer_bridge"
TOOLSET = "hermes_orca"
ACTIONS = {
    "health": ("GET", "/health"),
    "actions": ("GET", "/api/actions"),
    "profiles": ("GET", "/api/orca/profiles"),
    "flsun_inventory": ("GET", "/api/orca/flsun"),
    "orca_version": ("POST", "/api/orca/version"),
    "dry_run": ("POST", "/api/slice/dry-run"),
}
TOOL_SCHEMA = {
    "name": TOOL_NAME,
    "description": "Call the local HermesSlicer bridge for health, Orca profile discovery, FLSUN inventory, or dry-run validation.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": sorted(ACTIONS)},
            "payload": {"type": "object"},
        },
        "required": ["action"],
    },
}


def bridge_request(path: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(BRIDGE_URL + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            body = {"error": exc.reason}
        return {"status": "failed", "http_status": exc.code, **body}
    except (OSError, TimeoutError, URLError) as exc:
        return {
            "status": "blocked",
            "reason": "HermesSlicer bridge is unavailable. Start it with scripts/start_bridge.ps1.",
            "error_type": type(exc).__name__,
        }


def slicer_bridge(action: str = "health", payload: dict | None = None) -> dict:
    if action not in ACTIONS:
        result = {"status": "failed", "error": "Unsupported action", "allowed": sorted(ACTIONS)}
        log_event("hermes_tool", f"slicer_bridge.{action}", "failed", outputs=result)
        return result
    method, path = ACTIONS[action]
    result = bridge_request(path, method, payload or {})
    proof_status = "passed" if result.get("status") in {"ok", "passed"} or "error" not in result else "failed"
    if result.get("status") in {"blocked", "warning"}:
        proof_status = str(result["status"])
    log_event("hermes_tool", f"slicer_bridge.{action}", proof_status, inputs={"action": action}, outputs=result)
    return result


def slicer_bridge_handler(args: dict | None = None, **_: object) -> str:
    args = args or {}
    if not isinstance(args, dict):
        args = {}
    action = str(args.get("action", "health"))
    raw_payload = args.get("payload", {})
    payload = raw_payload if isinstance(raw_payload, dict) else {}
    return json.dumps(slicer_bridge(action, payload), indent=2)


def register(ctx):
    ctx.register_tool(
        name=TOOL_NAME,
        toolset=TOOLSET,
        schema=TOOL_SCHEMA,
        handler=slicer_bridge_handler,
        description=TOOL_SCHEMA["description"],
    )


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "health"
    result = slicer_bridge(action)
    write_json(ROOT / "proof" / "runtime" / f"hermes-tool-{action}.json", result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
