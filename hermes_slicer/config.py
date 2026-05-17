from __future__ import annotations

import json
import os
import shutil
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

HERMES_AGENT_PROVIDER_ENV_NAMES = ("DEEPSEEK_API_KEY", "MINIMAX_API_KEY", "SILICONFLOW_API_KEY")
HERMES_AGENT_LOCAL_BACKEND_ENV_NAMES = ("HERMES_AGENT_BASE_URL", "LM_STUDIO_BASE_URL", "OPENAI_BASE_URL")
HERMES_AGENT_LIVE_PROOF_ENV_NAMES = ("HERMES_AGENT_HEALTHCHECK_OK", "HERMES_AGENT_LIVE_PROOF")
HERMES_AGENT_HEALTH_URL_ENV = "HERMES_AGENT_HEALTH_URL"

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
        "description": "Validate a local TTS request and block playback until Azure Speech credentials are present.",
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
    try:
        parsed_body = json.loads(body) if body.strip() else {}
        if isinstance(parsed_body, dict):
            valid_json = True
            status = str(parsed_body.get("status", ""))
    except json.JSONDecodeError:
        status = ""
    passed = ok_http and valid_json and status in {"ok", "passed"}
    return {
        "configured": True,
        "passed": passed,
        "http_status": int(getattr(response, "status", 0)),
        "response_status": status or "not_reported",
        "valid_json": valid_json,
        "reason": "Hermes Agent health probe returned ok/passed." if passed else "Hermes Agent health probe did not return ok/passed.",
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
            "one provider key: DEEPSEEK_API_KEY, MINIMAX_API_KEY, or SILICONFLOW_API_KEY",
            "or one local backend endpoint: HERMES_AGENT_BASE_URL, LM_STUDIO_BASE_URL, or OPENAI_BASE_URL",
            "and live proof: HERMES_AGENT_HEALTH_URL pointing at Hermes Agent and returning ok/passed",
        ],
    }


def as_user_session_gate() -> dict[str, Any]:
    secret_present = bool(os.environ.get("HERMES_HUMAN_GRANT_SECRET"))
    return {
        "status": "blocked",
        "granted": False,
        "secret_present": secret_present,
        "reason": "No active AS_USER session is granted in V1 proof. HERMES_HUMAN_GRANT_SECRET is required before a bounded human grant can be requested.",
        "required": ["HERMES_HUMAN_GRANT_SECRET", "explicit scopes", "short TTL"],
    }


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
