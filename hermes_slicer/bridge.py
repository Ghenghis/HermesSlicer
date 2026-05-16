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
    "slice.dry_run": ("POST", "/api/slice/dry-run"),
    "slice.export_preflight": ("POST", "/api/slice/export-preflight"),
    "slice.export_gcode": ("POST", "/api/slice/export-gcode"),
    "chat.message": ("POST", "/api/chat/message"),
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
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8765")
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
            payload = health_payload()
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
        self.serve_static(route)

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        try:
            body = self.read_json_body()
            if route == "/api/action":
                payload, status = dispatch_action(body)
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
            if route == "/api/chat/message":
                payload = chat_message(body)
                log_event("panel", "chat.message", "passed", inputs=body, outputs=payload)
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
        return chat_message(body)

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


def dispatch_action(body: dict[str, object]) -> tuple[dict[str, object], int]:
    action = str(body.get("action", "")).strip()
    payload = body.get("payload", {})
    if not action:
        return {"status": "failed", "error": "action is required", "allowed": sorted(ACTION_ROUTES)}, 400
    if action not in ACTION_ROUTES:
        return {"status": "failed", "error": f"invalid action: {action}", "allowed": sorted(ACTION_ROUTES)}, 400
    if action == "bridge.health":
        return health_payload(), 200
    if action == "bridge.actions":
        return {"actions": ALLOWED_ACTIONS}, 200
    if action == "orca.version":
        result = orca_version_check()
        return result, 200 if result["status"] != "failed" else 500
    if action == "orca.profiles":
        return list_orca_profiles(), 200
    if action == "orca.flsun_inventory":
        return flsun_profile_inventory(), 200
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
    if action == "chat.message":
        request_payload = payload if isinstance(payload, dict) else {}
        return chat_message(request_payload), 200
    if action == "tts.speak":
        request_payload = payload if isinstance(payload, dict) else {}
        result = tts_speak(request_payload)
        return result, 200 if result["status"] in {"passed", "blocked"} else 400
    return {"status": "failed", "error": "unhandled action"}, 500


def chat_message(body: dict[str, object]) -> dict[str, object]:
    message = str(body.get("message", "")).strip()
    lower = message.lower()
    if "health" in lower:
        return {"reply": "Bridge health is ok.", "action": "bridge.health", "result": health_payload()}
    if "version" in lower or "orca" in lower:
        return {"reply": "I ran the safe Orca executable check.", "action": "orca.version", "result": orca_version_check()}
    if "preflight" in lower:
        return {"reply": "I resolved the default FLSUN export tuple without writing G-code.", "action": "slice.export_preflight", "result": flsun_export_preflight({})}
    if "flsun" in lower or "t1" in lower or "v400" in lower or "s1" in lower:
        return {"reply": "I checked local Orca FLSun profile resources.", "action": "orca.flsun_inventory", "result": flsun_profile_inventory()}
    if "profile" in lower:
        return {"reply": "I checked installed Orca profile folders.", "action": "orca.profiles", "result": list_orca_profiles()}
    if "dry" in lower or "slice" in lower:
        return {"reply": "The default sample slice request validates without writing G-code.", "action": "slice.dry_run", "result": dry_run_slice({})}
    return {
        "reply": "Hermes local bridge is online. Try Health, Orca Version, or Dry Slice.",
        "action": "chat.message",
        "result": {"received": bool(message)},
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
