from __future__ import annotations

import json
import math
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from . import __version__


ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
CONFIG_DIR = ROOT / "config"
LOCAL_DIR = ROOT / "local"
PROOF_DIR = ROOT / "proof"
SAMPLES_DIR = ROOT / "samples"
DEFAULT_BIND = "127.0.0.1"
DEFAULT_PORT = 8765
ORCA_PROFILE_ROOTS_ENV = "ORCASLICER_PROFILE_ROOTS"
FLSUN_PROFILE_NAME_MARKERS = ("flsun", "v400")
MAX_PROFILE_DISCOVERY_ENTRIES = 5000
MAX_PROFILE_DISCOVERY_RESULTS = 200

DEFAULT_AGENTS = [
    {"id": "orchestrator", "display_name": "Hermes", "provider": "minimax", "voice": "en-GB-MaisieNeural"},
    {"id": "slicer", "display_name": "Slicer Agent", "provider": "minimax", "voice": "en-AU-CarlyNeural"},
    {"id": "proof", "display_name": "Proof Agent", "provider": "deepseek", "voice": "en-US-GuyNeural"},
    {"id": "security", "display_name": "Security Agent", "provider": "deepseek", "voice": "en-US-JennyNeural"},
]

HERMES_AGENT_PROVIDER_ENV_NAMES = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "DEEPSEEK_API_KEY",
    "MINIMAX_API_KEY",
    "SILICONFLOW_API_KEY",
)
HERMES_AGENT_LOCAL_BACKEND_ENV_NAMES = ("HERMES_AGENT_BASE_URL", "LM_STUDIO_BASE_URL", "OPENAI_BASE_URL")
HERMES_AGENT_LIVE_PROOF_ENV_NAMES = ("HERMES_AGENT_HEALTHCHECK_OK", "HERMES_AGENT_LIVE_PROOF")
HERMES_AGENT_HEALTH_URL_ENV = "HERMES_AGENT_HEALTH_URL"
EXPECTED_HERMES_AGENT_VERSION = "0.14.0"
EXPECTED_HERMES_AGENT_RELEASE = "v2026.5.16"
AS_USER_SCOPES_ENV = "HERMES_AS_USER_SCOPES"
AS_USER_EXPIRES_AT_ENV = "HERMES_AS_USER_EXPIRES_AT"
AS_USER_GRANT_ID_ENV = "HERMES_AS_USER_GRANT_ID"
AS_USER_MAX_TTL_SECONDS = 15 * 60

ALLOWED_ACTIONS = [
    {
        "id": "bridge.health",
        "method": "GET",
        "path": "/health",
        "description": "Return localhost bridge health without secrets.",
        "destructive": False,
    },
    {
        "id": "bridge.actions",
        "method": "GET",
        "path": "/api/actions",
        "description": "List whitelisted bridge actions.",
        "destructive": False,
    },
    {
        "id": "orca.version",
        "method": "POST",
        "path": "/api/orca/version",
        "description": "Run a non-destructive Orca executable check.",
        "destructive": False,
    },
    {
        "id": "orca.profiles",
        "method": "GET",
        "path": "/api/orca/profiles",
        "description": "List installed Orca profile vendor folders without reading private config.",
        "destructive": False,
    },
    {
        "id": "orca.flsun_inventory",
        "method": "GET",
        "path": "/api/orca/flsun",
        "description": "Summarize local Orca FLSun T1, V400, and S1 profile resources.",
        "destructive": False,
    },
    {
        "id": "printer.targets",
        "method": "GET",
        "path": "/api/printers/targets",
        "description": "List configured read-only local FLSUN printer observation targets.",
        "destructive": False,
    },
    {
        "id": "printer.observe",
        "method": "POST",
        "path": "/api/printers/observe",
        "description": "Probe local printer web UI, Moonraker, OctoPrint, and camera endpoints without write commands.",
        "destructive": False,
    },
    {
        "id": "printer.safety_state",
        "method": "POST",
        "path": "/api/printers/safety-state",
        "description": "Return the default-deny camera and plate-clear safety gate state without printer commands.",
        "destructive": False,
    },
    {
        "id": "printer.safety_event.camera_frame",
        "method": "POST",
        "path": "/api/printers/safety-events/camera-frame",
        "description": "Record proof-only camera frame freshness for the printer safety gate.",
        "destructive": False,
    },
    {
        "id": "printer.safety_event.plate_classification",
        "method": "POST",
        "path": "/api/printers/safety-events/plate-classification",
        "description": "Record proof-only build-plate classification for the printer safety gate.",
        "destructive": False,
    },
    {
        "id": "printer.hard_stop_proof",
        "method": "POST",
        "path": "/api/printers/hard-stop-proof",
        "description": "Emit a HARD STOP proof payload. V1 never sends heater, motion, upload, or start commands.",
        "destructive": False,
    },
    {
        "id": "agents.list",
        "method": "GET",
        "path": "/api/agents",
        "description": "List local Hermes Agent roles and voice assignments.",
        "destructive": False,
    },
    {
        "id": "proof.recent",
        "method": "GET",
        "path": "/api/proof/recent",
        "description": "Return recent sanitized proof ledger events.",
        "destructive": False,
    },
    {
        "id": "hermes.proof_mcp",
        "method": "GET",
        "path": "/api/hermes/proof-mcp",
        "description": "Return the latest local Hermes Proof MCP status artifact.",
        "destructive": False,
    },
    {
        "id": "slice.dry_run",
        "method": "POST",
        "path": "/api/slice/dry-run",
        "description": "Validate a slice request without writing G-code.",
        "destructive": False,
    },
    {
        "id": "slice.export_preflight",
        "method": "POST",
        "path": "/api/slice/export-preflight",
        "description": "Resolve and prove a compatible FLSUN machine/process/filament export tuple.",
        "destructive": False,
    },
    {
        "id": "slice.export_gcode",
        "method": "POST",
        "path": "/api/slice/export-gcode",
        "description": "Export G-code only when explicitly enabled.",
        "destructive": False,
        "enabled_by_default": False,
    },
    {
        "id": "hermes_agent.tool_request",
        "method": "POST",
        "path": "/api/hermes-agent/tool-request",
        "description": "Route a Hermes Agent tool request to a safe local bridge action.",
        "destructive": False,
    },
    {
        "id": "tts.speak",
        "method": "POST",
        "path": "/api/tts/speak",
        "description": "Validate a local TTS request and block playback until Azure Speech credentials and explicit operator opt-in are present.",
        "destructive": False,
    },
]


def _candidate_executable(env_name: str, common_paths: list[str], which_names: list[str]) -> str | None:
    env_value = os.environ.get(env_name)
    if env_value and Path(env_value).exists():
        return env_value
    for name in which_names:
        found = shutil.which(name)
        if found:
            return found
    for raw_path in common_paths:
        path = Path(raw_path)
        if path.exists():
            return str(path)
    return None


def discover_executables() -> dict[str, str | None]:
    return {
        "orca": _candidate_executable(
            "ORCASLICER_PATH",
            [
                "C:/Program Files/OrcaSlicer/orca-slicer.exe",
                "C:/Program Files/OrcaSlicer/OrcaSlicer.exe",
            ],
            ["orca-slicer", "orca-slicer.exe", "OrcaSlicer", "OrcaSlicer.exe"],
        ),
        "prusa": _candidate_executable(
            "PRUSASLICER_PATH",
            [
                "C:/Program Files/Prusa3D/PrusaSlicer/prusa-slicer-console.exe",
                "C:/Program Files/Prusa3D/PrusaSlicer/prusa-slicer.exe",
            ],
            ["prusa-slicer-console", "prusa-slicer-console.exe", "prusa-slicer", "prusa-slicer.exe"],
        ),
    }


def discover_orca_profile_roots() -> list[Path]:
    executables = discover_executables()
    roots: list[Path] = []
    if executables.get("orca"):
        exe = Path(str(executables["orca"]))
        roots.append(exe.parent / "resources" / "profiles")
    for raw in os.environ.get(ORCA_PROFILE_ROOTS_ENV, "").split(os.pathsep):
        if raw.strip():
            roots.append(Path(raw.strip()))
    return roots


def allowed_model_roots() -> list[Path]:
    roots = [SAMPLES_DIR]
    for raw in os.environ.get("HERMES_MODEL_ROOTS", "").split(os.pathsep):
        if raw.strip():
            roots.append(Path(raw.strip()))
    return roots


def allowed_output_roots() -> list[Path]:
    roots = [PROOF_DIR / "output"]
    for raw in os.environ.get("HERMES_OUTPUT_ROOTS", "").split(os.pathsep):
        if raw.strip():
            roots.append(Path(raw.strip()))
    return roots


def default_slice_request() -> dict[str, Any]:
    return {
        "model_path": str(SAMPLES_DIR / "test_cube.stl"),
        "printer_profile": "FLSUN_T1_safe_default",
        "material_profile": "PLA_safe_default",
        "quality_profile": "0.20mm_standard",
        "output_dir": str(PROOF_DIR / "output"),
        "confirm_print": False,
    }


def load_agents() -> list[dict[str, Any]]:
    local_path = LOCAL_DIR / "agents.json"
    if local_path.exists():
        payload = json.loads(local_path.read_text(encoding="utf-8"))
        return payload.get("agents", DEFAULT_AGENTS)
    return DEFAULT_AGENTS


def save_agents(agents: list[dict[str, Any]]) -> None:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    (LOCAL_DIR / "agents.json").write_text(json.dumps({"agents": agents}, indent=2) + "\n", encoding="utf-8")


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "passed", "ok"}


def _flatten_json_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten_json_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_json_text(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _hermes_agent_identity_from_health(payload: dict[str, Any]) -> dict[str, Any]:
    identity_text = _flatten_json_text(
        {
            "name": payload.get("name"),
            "service": payload.get("service"),
            "product": payload.get("product"),
            "app": payload.get("app"),
            "agent": payload.get("agent"),
            "kind": payload.get("kind"),
        }
    ).lower()
    identity_ok = "hermes agent" in identity_text or "hermes-agent" in identity_text
    version_text = _flatten_json_text(
        {
            "version": payload.get("version"),
            "hermes_version": payload.get("hermes_version"),
            "hermes_agent_version": payload.get("hermes_agent_version"),
            "agent_version": payload.get("agent_version"),
            "build": payload.get("build"),
            "release": payload.get("release"),
            "tag": payload.get("tag"),
        }
    )
    version_ok = EXPECTED_HERMES_AGENT_VERSION in version_text
    release_ok = EXPECTED_HERMES_AGENT_RELEASE in version_text or EXPECTED_HERMES_AGENT_RELEASE.lstrip("v") in version_text
    return {
        "identity_ok": identity_ok,
        "version_ok": version_ok,
        "release_ok": release_ok,
        "expected_version": EXPECTED_HERMES_AGENT_VERSION,
        "expected_release": EXPECTED_HERMES_AGENT_RELEASE,
    }


def _probe_hermes_agent_health() -> dict[str, Any]:
    url = os.environ.get(HERMES_AGENT_HEALTH_URL_ENV, "").strip()
    if not url:
        return {"configured": False, "passed": False, "reason": f"{HERMES_AGENT_HEALTH_URL_ENV} is not set."}
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return {"configured": True, "passed": False, "reason": f"{HERMES_AGENT_HEALTH_URL_ENV} must be an http(s) URL."}
    bridge_health_url = os.environ.get("HERMES_SLICER_BRIDGE_URL", f"http://127.0.0.1:{DEFAULT_PORT}").rstrip("/") + "/health"
    if url.rstrip("/") == bridge_health_url:
        return {
            "configured": True,
            "passed": False,
            "reason": f"{HERMES_AGENT_HEALTH_URL_ENV} must point at Hermes Agent, not the HermesSlicer bridge.",
        }
    request = Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=2) as response:
            body = response.read(8192).decode("utf-8", errors="replace")
    except (OSError, TimeoutError, URLError) as exc:
        return {
            "configured": True,
            "passed": False,
            "reason": f"Hermes Agent health probe failed: {type(exc).__name__}.",
        }
    ok_http = 200 <= int(getattr(response, "status", 0)) < 300
    status = ""
    valid_json = False
    parsed_body: dict[str, Any] = {}
    try:
        raw_body = json.loads(body) if body.strip() else {}
        parsed_body = raw_body if isinstance(raw_body, dict) else {}
        if isinstance(parsed_body, dict):
            valid_json = True
            status = str(parsed_body.get("status", ""))
    except json.JSONDecodeError:
        status = ""
    identity = _hermes_agent_identity_from_health(parsed_body) if valid_json else {
        "identity_ok": False,
        "version_ok": False,
        "release_ok": False,
        "expected_version": EXPECTED_HERMES_AGENT_VERSION,
        "expected_release": EXPECTED_HERMES_AGENT_RELEASE,
    }
    passed = (
        ok_http
        and valid_json
        and status in {"ok", "passed"}
        and identity["identity_ok"]
        and identity["version_ok"]
        and identity["release_ok"]
    )
    if passed:
        reason = "Hermes Agent health probe returned ok/passed with required v0.14 identity."
    elif ok_http and valid_json and status in {"ok", "passed"}:
        reason = "Hermes Agent health probe did not prove Hermes Agent v0.14.0 / v2026.5.16 identity."
    else:
        reason = "Hermes Agent health probe did not return ok/passed."
    return {
        "configured": True,
        "passed": passed,
        "http_status": int(getattr(response, "status", 0)),
        "response_status": status or "not_reported",
        "valid_json": valid_json,
        **identity,
        "reason": reason,
    }


def hermes_agent_bridge_gate() -> dict[str, Any]:
    providers = {name: bool(os.environ.get(name)) for name in HERMES_AGENT_PROVIDER_ENV_NAMES}
    local_backends = {name: bool(os.environ.get(name)) for name in HERMES_AGENT_LOCAL_BACKEND_ENV_NAMES}
    enabled = os.environ.get("HERMES_AGENT_ENABLED") == "1"
    backend_present = any(providers.values()) or any(local_backends.values())
    operator_attestations = {name: _truthy_env(name) for name in HERMES_AGENT_LIVE_PROOF_ENV_NAMES}
    health_probe = _probe_hermes_agent_health()
    live_proof_present = bool(health_probe["passed"])
    configured = enabled and backend_present
    available = configured and live_proof_present
    if available:
        reason = "HERMES_AGENT_ENABLED=1, a provider/backend is present, and live Hermes Agent health proof passed."
    elif not enabled:
        reason = "HERMES_AGENT_ENABLED=1 is required before claiming live Hermes Agent connectivity."
    elif not backend_present:
        reason = "A provider key or local backend endpoint is required before claiming live Hermes Agent connectivity."
    else:
        reason = "Live Hermes Agent health proof is required before claiming live Hermes Agent connectivity."
    return {
        "status": "passed" if available else "blocked",
        "available": available,
        "live_connectivity_claimed": available,
        "configured": configured,
        "enabled": enabled,
        "providers_present": providers,
        "local_backends_present": local_backends,
        "backend_present": backend_present,
        "live_proof_present": live_proof_present,
        "operator_attestation_env_present": operator_attestations,
        "health_probe": health_probe,
        "reason": reason,
        "required": [
            "HERMES_AGENT_ENABLED=1",
            "one provider key: OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, GOOGLE_API_KEY, DEEPSEEK_API_KEY, MINIMAX_API_KEY, or SILICONFLOW_API_KEY",
            "or one local backend endpoint: HERMES_AGENT_BASE_URL, LM_STUDIO_BASE_URL, or OPENAI_BASE_URL",
            "and live proof: HERMES_AGENT_HEALTH_URL pointing at Hermes Agent v0.14.0 / v2026.5.16 and returning ok/passed",
        ],
    }


def as_user_session_gate() -> dict[str, Any]:
    secret_present = bool(os.environ.get("HERMES_HUMAN_GRANT_SECRET"))
    raw_scopes = os.environ.get(AS_USER_SCOPES_ENV, "")
    scopes = [scope.strip() for scope in raw_scopes.replace(";", ",").split(",") if scope.strip()]
    grant_id = os.environ.get(AS_USER_GRANT_ID_ENV, "").strip()
    expires_at = os.environ.get(AS_USER_EXPIRES_AT_ENV, "").strip()
    expiry = _parse_utc_datetime(expires_at)
    now = datetime.now(timezone.utc)
    ttl_total_seconds = (expiry - now).total_seconds() if expiry else None
    ttl_seconds = math.ceil(ttl_total_seconds) if ttl_total_seconds is not None else None
    errors: list[str] = []
    if not secret_present:
        errors.append("HERMES_HUMAN_GRANT_SECRET is not present.")
    if not scopes:
        errors.append(f"{AS_USER_SCOPES_ENV} must include at least one explicit scope.")
    if not grant_id:
        errors.append(f"{AS_USER_GRANT_ID_ENV} is required.")
    if expiry is None:
        errors.append(f"{AS_USER_EXPIRES_AT_ENV} must be an ISO-8601 UTC timestamp.")
    elif ttl_total_seconds is None or ttl_total_seconds <= 0:
        errors.append("AS_USER grant is expired.")
    elif ttl_total_seconds > AS_USER_MAX_TTL_SECONDS:
        errors.append(f"AS_USER grant TTL must be {AS_USER_MAX_TTL_SECONDS} seconds or less.")
    granted = not errors
    return {
        "status": "passed" if granted else "blocked",
        "granted": granted,
        "secret_present": secret_present,
        "grant_id_present": bool(grant_id),
        "scopes": scopes,
        "expires_at": expires_at,
        "ttl_seconds": ttl_seconds,
        "max_ttl_seconds": AS_USER_MAX_TTL_SECONDS,
        "reason": "Bounded AS_USER grant is active." if granted else " ".join(errors),
        "required": ["HERMES_HUMAN_GRANT_SECRET", AS_USER_GRANT_ID_ENV, AS_USER_SCOPES_ENV, AS_USER_EXPIRES_AT_ENV, "short TTL"],
    }


def _parse_utc_datetime(value: str) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def health_payload(bind: str = DEFAULT_BIND, port: int = DEFAULT_PORT) -> dict[str, Any]:
    executables = discover_executables()
    return {
        "status": "ok",
        "name": "HermesSlicer Local Bridge",
        "version": __version__,
        "bind": bind,
        "port": port,
        "executables": {name: bool(path) for name, path in executables.items()},
        "actions": [action["id"] for action in ALLOWED_ACTIONS],
        "hermes_agent_bridge": hermes_agent_bridge_gate(),
        "proof_ledger": "proof/ledger.jsonl",
    }
