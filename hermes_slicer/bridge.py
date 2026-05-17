from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import __version__
from .config import ALLOWED_ACTIONS, DEFAULT_BIND, DEFAULT_PORT, ROOT, WEB_DIR, health_payload, load_agents, save_agents
from .proof import log_event, recent_events, write_json
from .security import sanitize_obj, secret_presence
from .slicer import ValidationError, dry_run_slice, export_gcode, flsun_export_preflight, flsun_profile_inventory, list_orca_profiles, orca_version_check
from .voices import load_voice_catalog


ACTION_ROUTES = {
    "bridge.health": ("GET", "/health"),
    "bridge.actions": ("GET", "/api/actions"),
    "orca.version": ("POST", "/api/orca/version"),
    "orca.profiles": ("GET", "/api/orca/profiles"),
    "orca.flsun_inventory": ("GET", "/api/orca/flsun"),
    "agents.list": ("GET", "/api/agents"),
    "proof.recent": ("GET", "/api/proof/recent"),
    "hermes.proof_mcp": ("GET", "/api/hermes/proof-mcp"),
    "slice.dry_run": ("POST", "/api/slice/dry-run"),
    "slice.export_preflight": ("POST", "/api/slice/export-preflight"),
    "slice.export_gcode": ("POST", "/api/slice/export-gcode"),
    "hermes_agent.tool_request": ("POST", "/api/hermes-agent/tool-request"),
    "tts.speak": ("POST", "/api/tts/speak"),
}


class BridgeHandler(BaseHTTPRequestHandler):
    server_version = f"HermesSlicerBridge/{__version__}"

    def log_message(self, format: str, *args: object) -> None:
        log_event(
            actor="bridge",
            action="http.request",
            status="passed",
            inputs={"client": self.client_address[0], "path": self.path},
            notes=format % args,
        )

    def end_headers(self) -> None:
        bind, port = _server_bind_port(self.server)
        self.send_header("Access-Control-Allow-Origin", f"http://{bind}:{port}")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/health":
            bind, port = _server_bind_port(self.server)
            payload = health_payload(bind=bind, port=port)
            payload["secrets"] = secret_presence_summary()
            write_json(ROOT / "proof" / "runtime" / "bridge-health.json", payload)
            log_event("bridge", "bridge.health", "passed", outputs=payload, proof_files=["proof/runtime/bridge-health.json"])
            self.respond_json(payload)
            return
        if route == "/api/actions":
            log_event("bridge", "bridge.actions", "passed", outputs={"count": len(ALLOWED_ACTIONS)})
            self.respond_json({"actions": ALLOWED_ACTIONS})
            return
        if route == "/api/voices/azure/en":
            payload = load_voice_catalog()
            log_event("bridge", "voices.azure.en", "passed", outputs={"count": payload["count"], "source": payload["source"]})
            self.respond_json(payload)
            return
        if route == "/api/orca/profiles":
            payload = list_orca_profiles()
            log_event("bridge", "orca.profiles", payload["status"], outputs={"vendor_count": payload["vendor_count"]})
            self.respond_json(payload)
            return
        if route == "/api/orca/flsun":
            payload = flsun_profile_inventory()
            log_event("bridge", "orca.flsun_inventory", payload["status"], outputs={"targets": [item["model"] for item in payload.get("targets", [])]})
            self.respond_json(payload)
            return
        if route == "/api/agents":
            self.respond_json({"agents": load_agents()})
            return
        if route == "/api/proof/recent":
            self.respond_json({"events": recent_events(25)})
            return
        if route == "/api/hermes/proof-mcp":
            payload = hermes_proof_mcp_status()
            log_event("bridge", "hermes.proof_mcp", _normalized_event_status(payload.get("status")), outputs=payload)
            self.respond_json(payload)
            return
        self.serve_static(route)

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        try:
            body = self.read_json_body()
            if route == "/api/action":
                bind, port = _server_bind_port(self.server)
                payload, status = dispatch_action(body, bind=bind, port=port)
                proof_status = "passed" if 200 <= status < 300 else "failed"
                if payload.get("status") in {"blocked", "warning"}:
                    proof_status = str(payload["status"])
                log_event("bridge", "bridge.dispatch", proof_status, inputs=body, outputs=payload)
                self.respond_json(payload, status=status)
                return
            if route == "/api/orca/version":
                payload = orca_version_check()
                log_event("bridge", "orca.version", payload["status"], inputs={}, outputs=payload)
                self.respond_json(payload, status=200 if payload["status"] != "failed" else 500)
                return
            if route == "/api/slice/dry-run":
                payload = dry_run_slice(body)
                log_event("bridge", "slice.dry_run", "passed", inputs=body, outputs=payload)
                self.respond_json(payload)
                return
            if route == "/api/slice/export-preflight":
                payload = flsun_export_preflight(body)
                log_event("bridge", "slice.export_preflight", payload["status"], inputs=body, outputs=payload)
                self.respond_json(payload)
                return
            if route == "/api/slice/export-gcode":
                payload = export_gcode(body)
                code = 200 if payload["status"] in {"passed", "blocked"} else 500
                log_event("bridge", "slice.export_gcode", payload["status"], inputs=body, outputs=payload)
                self.respond_json(payload, status=code)
                return
            if route in {"/api/hermes-agent/tool-request", "/api/chat/message"}:
                bind, port = _server_bind_port(self.server)
                payload = hermes_agent_tool_request(body, bind=bind, port=port)
                action_name = "hermes_agent.tool_request" if route != "/api/chat/message" else "hermes_agent.tool_request.compat"
                log_event("panel", action_name, payload["status"], inputs=body, outputs=payload)
                self.respond_json(payload)
                return
            if route == "/api/tts/speak":
                payload = tts_speak(body)
                log_event("bridge", "tts.speak", payload["status"], inputs=body, outputs=payload)
                self.respond_json(payload, status=200 if payload["status"] in {"passed", "blocked"} else 400)
                return
            if route == "/api/agents":
                agents = body.get("agents", [])
                if not isinstance(agents, list):
                    raise ValidationError("agents must be a list")
                save_agents(agents)
                log_event("panel", "agents.save", "passed", inputs={"count": len(agents)})
                self.respond_json({"status": "passed", "agents": agents})
                return
            self.respond_json({"error": "Unknown endpoint"}, status=404)
        except ValidationError as exc:
            log_event("bridge", route, "failed", inputs={"path": route}, outputs={"error": str(exc)})
            self.respond_json({"error": str(exc)}, status=400)
        except json.JSONDecodeError:
            self.respond_json({"error": "Invalid JSON body"}, status=400)

    def handle_chat(self, body: dict[str, object]) -> dict[str, object]:
        return hermes_agent_tool_request(body)

    def read_json_body(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def respond_json(self, payload: dict[str, object], status: int = 200) -> None:
        data = json.dumps(sanitize_obj(payload), indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def serve_static(self, route: str) -> None:
        if route in {"", "/"}:
            relative = "index.html"
        else:
            relative = unquote(route.lstrip("/"))
        candidate = (WEB_DIR / relative).resolve()
        if not str(candidate).startswith(str(WEB_DIR.resolve())) or not candidate.exists() or candidate.is_dir():
            self.respond_json({"error": "Not found"}, status=404)
            return
        content = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(candidate.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def secret_presence_summary() -> dict[str, object]:
    presence = secret_presence()
    env = presence.get("env", {})
    return {
        "env_present": env,
        "private_root_present": presence.get("private_root_present", False),
        "project_secret_file_present": presence.get("project_secret_file_present", False),
        "values_returned": False,
    }


def dispatch_action(body: dict[str, object], bind: str = DEFAULT_BIND, port: int = DEFAULT_PORT) -> tuple[dict[str, object], int]:
    action = str(body.get("action", "")).strip()
    payload = body.get("payload", {})
    if not action:
        return {"status": "failed", "error": "action is required", "allowed": sorted(ACTION_ROUTES)}, 400
    if action not in ACTION_ROUTES:
        return {"status": "failed", "error": f"invalid action: {action}", "allowed": sorted(ACTION_ROUTES)}, 400
    if action == "bridge.health":
        return health_payload(bind=bind, port=port), 200
    if action == "bridge.actions":
        return {"actions": ALLOWED_ACTIONS}, 200
    if action == "orca.version":
        result = orca_version_check()
        return result, 200 if result["status"] != "failed" else 500
    if action == "orca.profiles":
        return list_orca_profiles(), 200
    if action == "orca.flsun_inventory":
        return flsun_profile_inventory(), 200
    if action == "agents.list":
        return {"agents": load_agents()}, 200
    if action == "proof.recent":
        return {"events": recent_events(25)}, 200
    if action == "hermes.proof_mcp":
        return hermes_proof_mcp_status(), 200
    if action == "slice.dry_run":
        request_payload = payload if isinstance(payload, dict) else {}
        return dry_run_slice(request_payload), 200
    if action == "slice.export_preflight":
        request_payload = payload if isinstance(payload, dict) else {}
        return flsun_export_preflight(request_payload), 200
    if action == "slice.export_gcode":
        request_payload = payload if isinstance(payload, dict) else {}
        result = export_gcode(request_payload)
        return result, 200 if result["status"] in {"passed", "blocked"} else 500
    if action == "hermes_agent.tool_request":
        request_payload = payload if isinstance(payload, dict) else {}
        return hermes_agent_tool_request(request_payload, bind=bind, port=port), 200
    if action == "tts.speak":
        request_payload = payload if isinstance(payload, dict) else {}
        result = tts_speak(request_payload)
        return result, 200 if result["status"] in {"passed", "blocked"} else 400
    return {"status": "failed", "error": "unhandled action"}, 500


def hermes_agent_tool_request(body: dict[str, object], bind: str = DEFAULT_BIND, port: int = DEFAULT_PORT) -> dict[str, object]:
    message = str(body.get("message", "")).strip()
    agent = str(body.get("agent", "")).strip() or "orchestrator"
    requested_action = str(body.get("action", "")).strip()
    lower = message.lower()
    explicit_action = requested_action or _extract_explicit_action(message)
    if explicit_action:
        result, status = dispatch_action({"action": explicit_action, "payload": body.get("payload", {})}, bind=bind, port=port)
        return {
            "status": _normalized_tool_status(result, status),
            "reply": f"Hermes Agent routed tool `{explicit_action}`.",
            "agent": agent,
            "toolset": "hermes_agent",
            "requested_action": requested_action or message,
            "resolved_action": explicit_action,
            "result": result,
        }
    if "tool" in lower or "action" in lower or "what can" in lower:
        return {
            "status": "passed",
            "reply": "Hermes Agent tool registry is loaded. I can run safe local bridge, Orca, FLSUN, proof, and blocked export tools.",
            "agent": agent,
            "toolset": "hermes_agent",
            "requested_action": requested_action or message,
            "resolved_action": "bridge.actions",
            "result": {"actions": ALLOWED_ACTIONS},
        }
    if "mcp" in lower or "proof mcp" in lower or "hermes proof" in lower:
        result = hermes_proof_mcp_status()
        return {
            "status": _normalized_tool_status(result, 200),
            "reply": "I checked the local Hermes Proof MCP status artifact.",
            "agent": agent,
            "toolset": "hermes_agent",
            "requested_action": requested_action or message,
            "resolved_action": "hermes.proof_mcp",
            "result": result,
        }
    if "ledger" in lower or "evidence" in lower or "proof" in lower:
        return {
            "status": "passed",
            "reply": "I pulled the recent sanitized proof ledger events.",
            "agent": agent,
            "toolset": "hermes_agent",
            "requested_action": requested_action or message,
            "resolved_action": "proof.recent",
            "result": {"events": recent_events(25)},
        }
    if "agent" in lower or "voice" in lower:
        return {
            "status": "passed",
            "reply": "I listed the local Hermes Agent roles and voice assignments.",
            "agent": agent,
            "toolset": "hermes_agent",
            "requested_action": requested_action or message,
            "resolved_action": "agents.list",
            "result": {"agents": load_agents()},
        }
    if "health" in lower:
        return _tool_request_result(agent, requested_action or message, "bridge.health", "I ran the HermesSlicer bridge health tool.", health_payload(bind=bind, port=port))
    if "version" in lower or "orca" in lower:
        return _tool_request_result(agent, requested_action or message, "orca.version", "I ran the safe Orca executable probe tool.", orca_version_check())
    if "preflight" in lower:
        return _tool_request_result(agent, requested_action or message, "slice.export_preflight", "I ran FLSUN export preflight without writing G-code.", flsun_export_preflight({}))
    if "flsun" in lower or "t1" in lower or "v400" in lower or "s1" in lower:
        return _tool_request_result(agent, requested_action or message, "orca.flsun_inventory", "I checked local Orca FLSUN profile resources.", flsun_profile_inventory())
    if "profile" in lower:
        return _tool_request_result(agent, requested_action or message, "orca.profiles", "I checked installed Orca profile folders.", list_orca_profiles())
    if "dry" in lower or "slice" in lower:
        return _tool_request_result(agent, requested_action or message, "slice.dry_run", "I ran a dry slice validation tool without writing G-code.", dry_run_slice({}))
    if "export" in lower or "g-code" in lower or "gcode" in lower:
        return _tool_request_result(agent, requested_action or message, "slice.export_gcode", "I ran the export tool. V1 should block G-code export unless local export is explicitly enabled.", export_gcode({}))
    if any(marker in lower for marker in ("draft", "fast print", "strong part", "support", "stick", "adhesion", "setting", "preset")):
        return {
            "status": "blocked",
            "reply": "I am Hermes Agent's local tool router, not a settings auto-apply chatbot. I can run preflight, inventory, proof, and blocked export tools; V1 will not silently apply slicer setting changes.",
            "agent": agent,
            "toolset": "hermes_agent",
            "requested_action": requested_action or message,
            "resolved_action": None,
            "result": {"received": bool(message), "recommended_tool": "slice.export_preflight"},
        }
    return {
        "status": "blocked",
        "reply": "Hermes Agent tool bridge is online. Ask for tools, proof MCP, FLSUN preflight, Orca probe, proof ledger, agents, or blocked export.",
        "agent": agent,
        "toolset": "hermes_agent",
        "requested_action": requested_action or message,
        "resolved_action": None,
        "result": {"received": bool(message)},
    }


def _tool_request_result(agent: str, requested_action: str, resolved_action: str, reply: str, result: dict[str, object]) -> dict[str, object]:
    return {
        "status": _normalized_tool_status(result, 200),
        "reply": reply,
        "agent": agent,
        "toolset": "hermes_agent",
        "requested_action": requested_action,
        "resolved_action": resolved_action,
        "result": result,
    }


def _normalized_tool_status(result: dict[str, object], http_status: int) -> str:
    if http_status >= 400:
        return "failed"
    status = str(result.get("status", "passed"))
    if status == "ok":
        return "passed"
    if status == "partial":
        return "warning"
    if status in {"passed", "failed", "blocked", "warning"}:
        return status
    return "passed"


def _normalized_event_status(value: object) -> str:
    status = str(value)
    if status == "ok":
        return "passed"
    if status == "partial":
        return "warning"
    if status in {"started", "passed", "failed", "blocked", "warning"}:
        return status
    return "passed"


def _extract_explicit_action(message: str) -> str | None:
    normalized = message.strip().strip("`'\".,:; ")
    allowed = set(ACTION_ROUTES)
    if normalized in allowed:
        return normalized
    parts = [part.strip("`'\".,:; ") for part in message.split()]
    for part in parts:
        if part in allowed:
            return part
    return None


def _server_bind_port(server: object) -> tuple[str, int]:
    address = getattr(server, "server_address", (DEFAULT_BIND, DEFAULT_PORT))
    return str(address[0]), int(address[1])


def hermes_proof_mcp_status() -> dict[str, object]:
    proof_path = ROOT / "proof" / "runtime" / "hermes-proof-mcp.json"
    if not proof_path.exists():
        return {
            "status": "blocked",
            "reason": "Hermes Proof MCP status artifact has not been generated.",
            "proof_file": "proof/runtime/hermes-proof-mcp.json",
        }
    try:
        payload = json.loads(proof_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "status": "failed",
            "reason": "Hermes Proof MCP status artifact is not valid JSON.",
            "proof_file": "proof/runtime/hermes-proof-mcp.json",
        }
    status = str(payload.get("status", "unknown"))
    return {
        "status": status,
        "proof_file": "proof/runtime/hermes-proof-mcp.json",
        "proof_mcp": payload.get("proof_mcp", {}),
        "hermes_agent_bridge": payload.get("hermes_agent_bridge", {}),
        "as_user_session": payload.get("as_user_session", {}),
        "evidence_id": payload.get("evidence_id"),
    }


def tts_speak(body: dict[str, object]) -> dict[str, object]:
    text = str(body.get("text", "")).strip()
    voice = str(body.get("voice", "")).strip() or "en-US-JennyNeural"
    agent = str(body.get("agent", "")).strip() or "orchestrator"
    if not text:
        return {"status": "failed", "error": "text is required"}
    if len(text) > 280:
        return {"status": "failed", "error": "text must be 280 characters or less"}
    catalog = load_voice_catalog()
    allowed_voices = {item["short_name"] for item in catalog["voices"]}
    if voice not in allowed_voices:
        return {"status": "failed", "error": "voice is not in the English Azure catalog"}
    presence = secret_presence()
    env = presence.get("env", {})
    if not env.get("AZURE_SPEECH_KEY") or not env.get("AZURE_SPEECH_REGION"):
        return {
            "status": "blocked",
            "agent": agent,
            "voice": voice,
            "playback": "not_attempted",
            "reason": "Azure Speech credentials are not present in this shell.",
        }
    return {
        "status": "blocked",
        "agent": agent,
        "voice": voice,
        "playback": "not_attempted",
        "reason": "Live Azure playback adapter is not enabled in V1.",
    }


def run(host: str = DEFAULT_BIND, port: int = DEFAULT_PORT) -> None:
    if host != "127.0.0.1":
        raise SystemExit("V1 bridge may only bind to 127.0.0.1")
    server = ThreadingHTTPServer((host, port), BridgeHandler)
    print(f"HermesSlicer bridge running at http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="HermesSlicer local bridge")
    parser.add_argument("--host", default=DEFAULT_BIND)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
