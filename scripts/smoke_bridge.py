from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE = os.environ.get("HERMES_SLICER_BRIDGE_URL", "http://127.0.0.1:8765").rstrip("/")


def request(path: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def main() -> int:
    checks = [
        ("health", request("/health")),
        ("actions", request("/api/actions")),
        ("profiles", request("/api/orca/profiles")),
        ("flsun", request("/api/orca/flsun")),
        ("voices", request("/api/voices/azure/en")),
        ("hermes_proof_mcp", request("/api/hermes/proof-mcp")),
        ("orca", request("/api/orca/version", "POST", {})),
        ("dry_run", request("/api/slice/dry-run", "POST", {})),
        ("export_preflight", request("/api/slice/export-preflight", "POST", {})),
        ("tool_request", request("/api/hermes-agent/tool-request", "POST", {"message": "slice.export_preflight", "agent": "orchestrator"})),
        ("compat_chat_alias", request("/api/chat/message", "POST", {"message": "bridge.actions", "agent": "orchestrator"})),
        ("tts_blocked", request("/api/tts/speak", "POST", {"agent": "orchestrator", "voice": "en-US-JennyNeural", "text": "Hermes voice smoke test."})),
        ("dispatch_health", request("/api/action", "POST", {"action": "bridge.health"})),
        ("dispatch_flsun", request("/api/action", "POST", {"action": "orca.flsun_inventory"})),
        ("dispatch_preflight", request("/api/action", "POST", {"action": "slice.export_preflight"})),
        ("dispatch_tool_request", request("/api/action", "POST", {"action": "hermes_agent.tool_request", "payload": {"message": "hermes.proof_mcp"}})),
        ("dispatch_tts", request("/api/action", "POST", {"action": "tts.speak", "payload": {"voice": "en-US-JennyNeural", "text": "Hermes voice smoke test."}})),
        ("invalid", request("/api/action", "POST", {"action": "not.allowed"})),
    ]
    failed = []
    for name, (status, payload) in checks:
        print(f"{name}: HTTP {status}")
        print(json.dumps(payload, indent=2)[:1600])
        if name == "invalid":
            if status != 400:
                failed.append(name)
        elif status >= 400:
            failed.append(name)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
