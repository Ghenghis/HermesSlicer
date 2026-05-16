from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .security import sanitize_obj, sanitize_text


ROOT = Path(__file__).resolve().parents[1]
PROOF_DIR = ROOT / "proof"
LEDGER_PATH = PROOF_DIR / "ledger.jsonl"
VALID_STATUSES = {"started", "passed", "failed", "blocked", "warning"}
REQUIRED_EVENT_KEYS = {"ts", "event_id", "actor", "action", "status", "redacted"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(
    actor: str,
    action: str,
    status: str,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    proof_files: list[str] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": utc_now(),
        "event_id": str(uuid.uuid4()),
        "actor": sanitize_text(actor, None),
        "action": sanitize_text(action, None),
        "status": status,
        "redacted": True,
    }
    if inputs is not None:
        event["inputs"] = sanitize_obj(inputs)
    if outputs is not None:
        event["outputs"] = sanitize_obj(outputs)
    if proof_files is not None:
        event["proof_files"] = [sanitize_text(p, None) for p in proof_files]
    if notes:
        event["notes"] = sanitize_text(notes)
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n")
    return event


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_obj(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def recent_events(limit: int = 20) -> list[dict[str, Any]]:
    if not LEDGER_PATH.exists():
        return []
    lines = LEDGER_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()
    events: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def validate_event(event: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_EVENT_KEYS.difference(event)
    if missing:
        errors.append(f"missing required keys: {', '.join(sorted(missing))}")
    if event.get("status") not in VALID_STATUSES:
        errors.append(f"invalid status: {event.get('status')!r}")
    if event.get("redacted") is not True:
        errors.append("redacted must be true")
    for key in ("ts", "event_id", "actor", "action"):
        if key in event and not isinstance(event[key], str):
            errors.append(f"{key} must be a string")
    return errors


def validate_ledger(path: Path = LEDGER_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"status": "blocked", "path": str(path), "events": 0, "errors": ["ledger does not exist"]}
    errors: list[dict[str, Any]] = []
    event_count = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        if not line.strip():
            continue
        event_count += 1
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_number, "errors": [f"invalid JSON: {exc.msg}"]})
            continue
        event_errors = validate_event(event)
        if event_errors:
            errors.append({"line": line_number, "errors": event_errors})
    return {
        "status": "passed" if not errors else "failed",
        "path": str(path),
        "events": event_count,
        "errors": errors,
    }
