from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BRIDGE_URL = "http://127.0.0.1:8765"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.proof import log_event, write_json  # noqa: E402


def bridge_request(path: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(BRIDGE_URL + path, data=data, method=method, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def slicer_bridge(action: str = "health", payload: dict | None = None) -> dict:
    routes = {
        "health": ("GET", "/health"),
        "actions": ("GET", "/api/actions"),
        "profiles": ("GET", "/api/orca/profiles"),
        "flsun_inventory": ("GET", "/api/orca/flsun"),
        "orca_version": ("POST", "/api/orca/version"),
        "dry_run": ("POST", "/api/slice/dry-run"),
    }
    if action not in routes:
        result = {"status": "failed", "error": "Unsupported action", "allowed": sorted(routes)}
        log_event("hermes_tool", f"slicer_bridge.{action}", "failed", outputs=result)
        return result
    method, path = routes[action]
    result = bridge_request(path, method, payload or {})
    proof_status = "passed" if result.get("status") in {"ok", "passed"} or "error" not in result else "failed"
    if result.get("status") in {"blocked", "warning"}:
        proof_status = str(result["status"])
    log_event("hermes_tool", f"slicer_bridge.{action}", proof_status, inputs={"action": action}, outputs=result)
    return result


def register(ctx):
    ctx.register_tool(
        name="slicer_bridge",
        description="Call the local HermesSlicer bridge for health, actions, Orca version, or dry-run validation.",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["health", "actions", "profiles", "flsun_inventory", "orca_version", "dry_run"]},
                "payload": {"type": "object"},
            },
            "required": ["action"],
        },
        handler=lambda action="health", payload=None: slicer_bridge(action, payload),
    )


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "health"
    result = slicer_bridge(action)
    write_json(ROOT / "proof" / "runtime" / f"hermes-tool-{action}.json", result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
