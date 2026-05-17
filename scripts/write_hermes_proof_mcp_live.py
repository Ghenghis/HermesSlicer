from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.config import as_user_session_gate, hermes_agent_bridge_gate  # noqa: E402
from hermes_slicer.proof import log_event, write_json  # noqa: E402


PROOF_PATH = ROOT / "proof" / "runtime" / "hermes-proof-mcp.json"
AS_USER_ARTIFACT_PATH = ROOT / "proof" / "runtime" / "as_user_session.json"
VERIFY_JSON_ENV = "HERMES_PROOF_MCP_VERIFY_JSON"
VERIFY_JSON_PATH_ENV = "HERMES_PROOF_MCP_VERIFY_JSON_PATH"
MCP_SERVER_NAME = "hermes-slicer-proof"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, f"{path} is missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, f"{path} is invalid JSON: {exc.msg}"
    if not isinstance(payload, dict):
        return {}, f"{path} must contain a JSON object"
    return payload, None


def _paths_equal(left: str | Path, right: str | Path) -> bool:
    try:
        return Path(left).resolve() == Path(right).resolve()
    except (OSError, RuntimeError):
        return False


def _load_verify_payload(env: Mapping[str, str] = os.environ) -> tuple[dict[str, Any], str | None]:
    raw_json = env.get(VERIFY_JSON_ENV, "").strip()
    raw_path = env.get(VERIFY_JSON_PATH_ENV, "").strip()
    if raw_json:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            return {}, f"{VERIFY_JSON_ENV} is invalid JSON: {exc.msg}"
        if not isinstance(payload, dict):
            return {}, f"{VERIFY_JSON_ENV} must contain a JSON object"
        return payload, None
    if raw_path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = ROOT / path
        return _load_json(path)
    return _auto_verify_payload()


def _truth_from_payload(payload: Mapping[str, Any], *keys: str) -> bool:
    return any(payload.get(key) is True for key in keys)


def hermes_mcp_transport_gate(
    workspace_root: Path = ROOT,
    verify_payload: Mapping[str, Any] | None = None,
    env: Mapping[str, str] = os.environ,
) -> dict[str, Any]:
    payload: Mapping[str, Any]
    load_error: str | None = None
    if verify_payload is None:
        loaded, load_error = _load_verify_payload(env)
        payload = loaded
    else:
        payload = verify_payload

    reported_workspace = str(
        payload.get("workspace_root")
        or payload.get("workspace")
        or payload.get("root")
        or env.get("HERMES_PROOF_MCP_WORKSPACE_ROOT", "")
    ).strip()
    transport_status = str(
        payload.get("transport_status")
        or payload.get("codex_mcp_transport_status")
        or env.get("HERMES_PROOF_MCP_TRANSPORT_STATUS", "not_available")
    ).strip()
    verify_tool = str(payload.get("tool") or payload.get("verified_by") or "").strip()
    verify_tool_ok = verify_tool == "hermes_verify_evidence"
    ok = _truth_from_payload(payload, "ok", "passed", "available") or str(payload.get("status", "")).lower() in {"ok", "passed"}
    evidence_ledger_ok = _truth_from_payload(payload, "evidence_ledger_ok", "ledger_ok", "hash_chain_ok")
    workspace_scope_ok = bool(reported_workspace) and _paths_equal(reported_workspace, workspace_root)
    transport_available = transport_status.lower() in {"available", "open", "connected", "ok", "passed", "workspace_scoped"}
    available = ok and verify_tool_ok and evidence_ledger_ok and workspace_scope_ok and transport_available

    if available:
        reason = "Hermes Proof MCP transport verified this workspace and evidence ledger."
    elif load_error:
        reason = load_error
    elif not ok:
        reason = "Hermes Proof MCP verification did not report ok/passed."
    elif not verify_tool_ok:
        reason = "Hermes Proof MCP verification was not produced by hermes_verify_evidence."
    elif not transport_available:
        reason = "Hermes Proof MCP transport is not reported available/open."
    elif not reported_workspace:
        reason = "Hermes Proof MCP verification did not include workspace_root."
    elif not workspace_scope_ok:
        reason = f"Hermes Proof MCP verification is scoped to {reported_workspace!r}, not {str(workspace_root)!r}."
    else:
        reason = "Hermes Proof MCP verification did not prove evidence_ledger_ok=true."

    return {
        "status": "passed" if available else "blocked",
        "available": available,
        "evidence_ledger_ok": evidence_ledger_ok,
        "reason": reason,
        "workspace_root": reported_workspace or None,
        "expected_workspace_root": str(workspace_root),
        "workspace_scope_ok": workspace_scope_ok,
        "codex_mcp_transport_status": transport_status or "not_available",
        "verify_status": payload.get("status", "not_supplied"),
        "verify_tool": verify_tool or "not_supplied",
    }


def _run_command(args: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "blocked", "args": args, "error_type": type(exc).__name__, "reason": str(exc)}
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "args": args,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _auto_verify_payload() -> tuple[dict[str, Any], str | None]:
    hermes_path = shutil.which("hermes") or shutil.which("hermes.exe")
    if not hermes_path:
        return {}, "No live Hermes Proof MCP verification payload was supplied and hermes CLI was not found."

    config_scope = _active_mcp_config_scope()
    if not config_scope["passed"]:
        return {
            "status": "blocked",
            "tool": "hermes_verify_evidence" if config_scope["server_configured"] else "not_supplied",
            "transport_status": "not_available",
            "workspace_root": str(ROOT),
            "evidence_ledger_ok": False,
            "active_mcp_config_scope": config_scope,
            "reason": config_scope["reason"],
        }, None

    test_result = _run_command([hermes_path, "mcp", "test", MCP_SERVER_NAME])
    connected = test_result.get("status") == "passed" and "Connected" in str(test_result.get("stdout", ""))
    tool_discovered = "hermes.verify_evidence" in str(test_result.get("stdout", ""))
    if not connected or not tool_discovered:
        return {
            "status": "blocked",
            "tool": "hermes_verify_evidence" if tool_discovered else "not_supplied",
            "transport_status": "not_available",
            "workspace_root": str(ROOT),
            "evidence_ledger_ok": False,
            "mcp_test_command": test_result,
        }, None

    try:
        from hermes_slicer.mcp_server import call_tool

        tool_result = call_tool({"name": "hermes.verify_evidence", "arguments": {"workspace_root": str(ROOT)}})
        structured = tool_result.get("structuredContent", {}) if isinstance(tool_result, dict) else {}
        proof_mcp = structured.get("proof_mcp", {}) if isinstance(structured.get("proof_mcp", {}), dict) else {}
    except Exception as exc:
        return {
            "status": "blocked",
            "tool": "hermes_verify_evidence",
            "transport_status": "available",
            "workspace_root": str(ROOT),
            "evidence_ledger_ok": False,
            "mcp_test_command": test_result,
            "reason": f"Local hermes.verify_evidence call failed: {type(exc).__name__}.",
        }, None

    evidence_ok = (
        structured.get("status") == "passed"
        and proof_mcp.get("evidence_ledger_ok") is True
        and proof_mcp.get("artifact_report_ok") is True
        and proof_mcp.get("workspace_scope_ok") is True
    )
    return {
        "status": "passed" if evidence_ok else "blocked",
        "ok": evidence_ok,
        "tool": "hermes_verify_evidence",
        "transport_status": "available",
        "workspace_root": proof_mcp.get("workspace_root", str(ROOT)),
        "evidence_ledger_ok": proof_mcp.get("evidence_ledger_ok") is True,
        "artifact_report_ok": proof_mcp.get("artifact_report_ok") is True,
        "workspace_scope_ok": proof_mcp.get("workspace_scope_ok") is True,
        "mcp_test_command": test_result,
        "active_mcp_config_scope": config_scope,
    }, None


def _active_mcp_config_scope(env: Mapping[str, str] = os.environ) -> dict[str, Any]:
    hermes_home = Path(env.get("HERMES_HOME") or (Path.home() / ".hermes"))
    config_path = hermes_home / "config.yaml"
    if not config_path.exists():
        return {
            "passed": False,
            "server_configured": False,
            "config_path": str(config_path),
            "reason": "Active Hermes config.yaml was not found.",
        }
    text = config_path.read_text(encoding="utf-8", errors="ignore")
    root_text = str(ROOT)
    server_configured = MCP_SERVER_NAME in text
    root_configured = root_text in text
    runner_configured = "run_mcp_server.py" in text
    passed = server_configured and root_configured and runner_configured
    return {
        "passed": passed,
        "server_configured": server_configured,
        "workspace_root_configured": root_configured,
        "runner_configured": runner_configured,
        "config_path": str(config_path),
        "reason": "Active Hermes MCP config is scoped to this workspace." if passed else "Active Hermes MCP config is not scoped to this workspace.",
    }


def _as_user_artifact_passed(payload: Mapping[str, Any]) -> bool:
    gate = payload.get("as_user_session", {})
    return (
        payload.get("status") == "passed"
        and isinstance(gate, Mapping)
        and gate.get("granted") is True
        and bool(gate.get("grant_id_present"))
        and bool(gate.get("scopes"))
    )


def _evidence_id(seed: Mapping[str, Any]) -> str:
    encoded = json.dumps(seed, sort_keys=True, default=str)
    return "ev_" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def build_report(
    verify_payload: Mapping[str, Any] | None = None,
    env: Mapping[str, str] = os.environ,
    now: str | None = None,
) -> dict[str, Any]:
    generated_at = now or _utc_now()
    bridge_gate = hermes_agent_bridge_gate()
    as_user_gate = as_user_session_gate()
    as_user_artifact, as_user_artifact_error = _load_json(AS_USER_ARTIFACT_PATH)
    proof_mcp_gate = hermes_mcp_transport_gate(ROOT, verify_payload, env)

    checks = {
        "hermes_agent_bridge_passed": bridge_gate.get("status") == "passed" and bridge_gate.get("live_connectivity_claimed") is True,
        "as_user_gate_passed": as_user_gate.get("status") == "passed" and as_user_gate.get("granted") is True,
        "as_user_artifact_passed": _as_user_artifact_passed(as_user_artifact),
        "proof_mcp_transport_passed": proof_mcp_gate.get("status") == "passed",
    }
    blockers: list[str] = []
    if not checks["hermes_agent_bridge_passed"]:
        blockers.append(str(bridge_gate.get("reason", "Hermes Agent bridge gate did not pass.")))
    if not checks["as_user_gate_passed"]:
        blockers.append(str(as_user_gate.get("reason", "AS_USER environment gate did not pass.")))
    if not checks["as_user_artifact_passed"]:
        blockers.append(as_user_artifact_error or "proof/runtime/as_user_session.json does not prove a passed bounded AS_USER grant.")
    if not checks["proof_mcp_transport_passed"]:
        blockers.append(str(proof_mcp_gate.get("reason", "Hermes Proof MCP transport gate did not pass.")))

    passed = all(checks.values())
    proof_transport_passed = proof_mcp_gate.get("status") == "passed"
    proof_mcp_payload = {
        **proof_mcp_gate,
        "available": proof_transport_passed,
        "evidence_ledger_ok": proof_mcp_gate.get("evidence_ledger_ok") is True,
        "workspace_scope_ok": proof_mcp_gate.get("workspace_scope_ok") is True,
        "reason": "Hermes Proof MCP transport and evidence verification passed." if proof_transport_passed else str(proof_mcp_gate.get("reason", "Hermes Proof MCP transport gate did not pass.")),
    }
    report = {
        "status": "passed" if passed else "blocked",
        "generated_at": generated_at,
        "date": generated_at[:10],
        "proof_mcp": proof_mcp_payload,
        "hermes_agent_bridge": bridge_gate,
        "as_user_session": as_user_gate,
        "as_user_artifact": as_user_artifact.get("as_user_session", {}),
        "live_gate_checks": checks,
        "blockers": blockers,
    }
    report["evidence_id"] = _evidence_id(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a live Hermes Proof MCP artifact only after all live gates are proven.")
    parser.add_argument("--write-blocked", action="store_true", help="write a blocked artifact when live gates are not proven")
    args = parser.parse_args(argv)

    report = build_report()
    should_write = report["status"] == "passed" or args.write_blocked
    if should_write:
        write_json(PROOF_PATH, report)
        proof_files = ["proof/runtime/hermes-proof-mcp.json"]
    else:
        proof_files = []
    log_event(
        "proof",
        "hermes.proof_mcp_live",
        str(report["status"]),
        outputs={
            "status": report["status"],
            "written": should_write,
            "available": report["proof_mcp"]["available"],
            "workspace_scope_ok": report["proof_mcp"]["workspace_scope_ok"],
        },
        proof_files=proof_files,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
