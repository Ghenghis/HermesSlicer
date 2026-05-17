from __future__ import annotations

import ipaddress
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .config import CONFIG_DIR, ROOT


DEFAULT_PRINTERS_PATH = CONFIG_DIR / "printers.example.json"
LOCAL_PRINTERS_PATH = ROOT / "local" / "printers.json"
DEFAULT_TIMEOUT_SECONDS = float(os.environ.get("HERMES_PRINTER_PROBE_TIMEOUT", "2"))
MAX_RESPONSE_BYTES = 32768
MOONRAKER_PORT = 7125
MJPEG_PORT = 8080


def load_printer_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or (LOCAL_PRINTERS_PATH if LOCAL_PRINTERS_PATH.exists() else DEFAULT_PRINTERS_PATH)
    if not config_path.exists():
        return {"enable_printer_upload": False, "enable_print_start": False, "targets": [], "source": str(config_path)}
    payload = json.loads(config_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{config_path} must contain a JSON object")
    targets = payload.get("targets", [])
    if not isinstance(targets, list):
        raise ValueError(f"{config_path} targets must be a list")
    return {
        "enable_printer_upload": bool(payload.get("enable_printer_upload", False)),
        "enable_print_start": bool(payload.get("enable_print_start", False)),
        "targets": [_normalize_target(item) for item in targets if isinstance(item, dict)],
        "source": str(config_path),
    }


def printer_targets(path: Path | None = None) -> dict[str, Any]:
    config = load_printer_config(path)
    return {
        "status": "passed" if config["targets"] else "blocked",
        "targets": config["targets"],
        "count": len(config["targets"]),
        "source": config["source"],
        "safety": _safety_payload(config),
    }


def observe_printers(body: dict[str, Any] | None = None, config_path: Path | None = None) -> dict[str, Any]:
    body = body or {}
    config = load_printer_config(config_path)
    requested_id = str(body.get("target_id", "")).strip()
    targets = config["targets"]
    if requested_id:
        targets = [target for target in targets if target["id"] == requested_id]
    if requested_id and not targets:
        return {
            "status": "failed",
            "error": f"unknown printer target_id: {requested_id}",
            "known_targets": [target["id"] for target in config["targets"]],
            "safety": _safety_payload(config),
        }
    observations = [probe_printer_target(target) for target in targets]
    status = _combined_status([item["status"] for item in observations])
    return {
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "targets": observations,
        "source": config["source"],
        "safety": _safety_payload(config),
    }


def probe_printer_target(target: dict[str, Any], timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    host = str(target.get("host", "")).strip()
    local_gate = _local_host_gate(host)
    if not local_gate["passed"]:
        return {
            "status": "blocked",
            "target": target,
            "local_network_gate": local_gate,
            "interfaces": {},
            "camera_candidates": [],
            "reason": local_gate["reason"],
            "safety": _target_safety_payload(),
        }

    base_url = _http_base_url(host)
    web_ui = _probe_web_ui(base_url, timeout)
    moonraker = _probe_json(f"http://{local_gate['host']}:{MOONRAKER_PORT}/server/info", timeout)
    octoprint = _probe_json(f"{base_url}/api/version", timeout)
    camera_candidates = _probe_camera_candidates(local_gate["host"], timeout)
    detected = _detected_interfaces(web_ui, moonraker, octoprint, camera_candidates)
    status = "passed" if detected else "blocked"
    reason = (
        "Read-only printer observation interfaces were discovered."
        if detected
        else "No read-only printer web UI, Moonraker, OctoPrint, or camera endpoint responded."
    )
    return {
        "status": status,
        "target": target,
        "local_network_gate": local_gate,
        "interfaces": {
            "web_ui": web_ui,
            "moonraker": moonraker,
            "octoprint": octoprint,
        },
        "camera_candidates": camera_candidates,
        "detected_interfaces": detected,
        "reason": reason,
        "safety": _target_safety_payload(),
    }


def _normalize_target(item: dict[str, Any]) -> dict[str, Any]:
    host = str(item.get("host", "")).strip()
    return {
        "id": str(item.get("id", "")).strip(),
        "name": str(item.get("name", "")).strip(),
        "model": str(item.get("model", "")).strip() or "FLSun T1",
        "host": host,
        "base_url": _http_base_url(host) if host else "",
        "role": str(item.get("role", "observation")).strip(),
        "notes": str(item.get("notes", "")).strip(),
    }


def _local_host_gate(host_or_url: str) -> dict[str, Any]:
    parsed = urlparse(host_or_url if "://" in host_or_url else f"http://{host_or_url}")
    host = parsed.hostname or host_or_url
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return {
            "passed": False,
            "host": host,
            "reason": "Printer observation targets must be literal local IP addresses.",
        }
    allowed = address.is_private or address.is_loopback or address.is_link_local
    return {
        "passed": allowed,
        "host": str(address),
        "reason": "Host is local/private." if allowed else "Host is not a local/private address.",
    }


def _http_base_url(host_or_url: str) -> str:
    if host_or_url.startswith(("http://", "https://")):
        parsed = urlparse(host_or_url)
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return f"http://{host_or_url}".rstrip("/")


def _probe_web_ui(base_url: str, timeout: float) -> dict[str, Any]:
    result = _fetch(base_url, timeout)
    body = str(result.get("body_preview", "")).lower()
    http_status = int(result.get("http_status") or 0)
    detected = []
    for marker in ("mainsail", "fluidd", "octoprint"):
        if marker in body:
            detected.append(marker)
    if result["reachable"] and http_status in {401, 403} and not detected:
        detected.append("protected_web_ui")
    elif result["reachable"] and 200 <= http_status < 400 and not detected:
        detected.append("unknown_web_ui")
    return {**result, "detected": detected}


def _probe_json(url: str, timeout: float) -> dict[str, Any]:
    result = _fetch(url, timeout, accept="application/json")
    parsed: dict[str, Any] = {}
    body = str(result.get("body_preview", ""))
    try:
        raw = json.loads(body) if body else {}
        parsed = raw if isinstance(raw, dict) else {}
    except json.JSONDecodeError:
        parsed = {}
    detected = bool(parsed) or result.get("http_status") in {401, 403}
    return {
        **result,
        "detected": detected,
        "auth_required": result.get("http_status") in {401, 403},
        "json_keys": sorted(parsed)[:20],
    }


def _probe_camera_candidates(host: str, timeout: float) -> list[dict[str, Any]]:
    urls = [
        f"http://{host}/webcam/?action=snapshot",
        f"http://{host}/webcam/snapshot",
        f"http://{host}/snapshot",
        f"http://{host}:{MJPEG_PORT}/?action=snapshot",
    ]
    return [_camera_result(url, timeout) for url in urls]


def _camera_result(url: str, timeout: float) -> dict[str, Any]:
    result = _fetch(url, timeout, accept="image/*")
    content_type = str(result.get("content_type", ""))
    detected = result["reachable"] and (content_type.startswith("image/") or result.get("http_status") in {401, 403})
    return {
        "url": url,
        "reachable": result["reachable"],
        "detected": detected,
        "http_status": result.get("http_status"),
        "content_type": content_type,
        "auth_required": result.get("http_status") in {401, 403},
        "reason": result.get("reason"),
    }


def _fetch(url: str, timeout: float, accept: str = "text/html,application/json,*/*") -> dict[str, Any]:
    request = Request(url, method="GET", headers={"Accept": accept, "User-Agent": "HermesSlicer-readonly-probe/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(MAX_RESPONSE_BYTES)
            status = int(getattr(response, "status", 200))
            content_type = str(response.headers.get("Content-Type", ""))
    except HTTPError as exc:
        body = exc.read(MAX_RESPONSE_BYTES)
        status = int(exc.code)
        content_type = str(exc.headers.get("Content-Type", ""))
        return {
            "url": url,
            "reachable": True,
            "http_status": status,
            "content_type": content_type,
            "body_preview": _decode_preview(body, content_type),
            "reason": f"HTTP {status}",
        }
    except (OSError, TimeoutError, URLError) as exc:
        return {
            "url": url,
            "reachable": False,
            "http_status": None,
            "content_type": "",
            "body_preview": "",
            "reason": type(exc).__name__,
        }
    return {
        "url": url,
        "reachable": 200 <= status < 500,
        "http_status": status,
        "content_type": content_type,
        "body_preview": _decode_preview(body, content_type),
        "reason": "reachable" if 200 <= status < 500 else f"HTTP {status}",
    }


def _decode_preview(body: bytes, content_type: str) -> str:
    if content_type.startswith("image/"):
        return ""
    return body.decode("utf-8", errors="replace")[:4000]


def _detected_interfaces(
    web_ui: dict[str, Any],
    moonraker: dict[str, Any],
    octoprint: dict[str, Any],
    camera_candidates: list[dict[str, Any]],
) -> list[str]:
    detected: list[str] = []
    detected.extend(str(item) for item in web_ui.get("detected", []) if item)
    if moonraker.get("detected"):
        detected.append("moonraker")
    if octoprint.get("detected"):
        detected.append("octoprint")
    if any(item.get("detected") for item in camera_candidates):
        detected.append("camera")
    return sorted(set(detected))


def _combined_status(statuses: list[str]) -> str:
    if not statuses:
        return "blocked"
    if all(status == "passed" for status in statuses):
        return "passed"
    if any(status == "passed" for status in statuses):
        return "partial"
    return "blocked"


def _safety_payload(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "read_only_observation",
        "upload_gcode_enabled": bool(config.get("enable_printer_upload")) and False,
        "print_start_enabled": bool(config.get("enable_print_start")) and False,
        "upload_gcode": "blocked_in_v1",
        "start_print": "blocked_in_v1",
        "allowed_probe_methods": ["GET"],
    }


def _target_safety_payload() -> dict[str, Any]:
    return {
        "upload_gcode": "not_attempted",
        "start_print": "not_attempted",
        "heater_or_motion_commands": "not_implemented",
    }
