from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.config import as_user_session_gate, hermes_agent_bridge_gate  # noqa: E402
from hermes_slicer.proof import log_event, write_json  # noqa: E402


def run_command(args: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
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


def build_report() -> dict[str, Any]:
    hermes_path = shutil.which("hermes") or shutil.which("hermes.exe")
    mcp_list = run_command([hermes_path, "mcp", "list"]) if hermes_path else {"status": "blocked", "reason": "hermes CLI not found"}
    output = f"{mcp_list.get('stdout', '')}\n{mcp_list.get('stderr', '')}".lower()
    configured = bool(hermes_path and mcp_list.get("status") == "passed" and "no mcp servers configured" not in output)
    transport_status = os.environ.get("HERMES_PROOF_MCP_TRANSPORT_STATUS", "not_available").strip() or "not_available"
    reason = (
        "No workspace-scoped Hermes Proof MCP evidence is available. "
        "Active Hermes v0.14 CLI also reports no configured MCP servers."
        if not configured
        else "Active Hermes CLI has MCP configuration, but no workspace-scoped proof evidence was supplied to this script."
    )
    proof_mcp = {
        "available": False,
        "evidence_ledger_ok": False,
        "reason": reason,
        "workspace_root": None,
        "expected_workspace_root": str(ROOT),
        "workspace_scope_ok": False,
        "codex_mcp_transport_status": transport_status,
        "active_hermes_mcp_configured": configured,
        "active_hermes_mcp_list": mcp_list,
    }
    evidence_seed = json.dumps(proof_mcp, sort_keys=True) + datetime.now(timezone.utc).isoformat()
    return {
        "status": "blocked",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now(timezone.utc).date().isoformat(),
        "proof_mcp": proof_mcp,
        "hermes_agent_bridge": hermes_agent_bridge_gate(),
        "as_user_session": as_user_session_gate(),
        "evidence_id": "ev_" + hashlib.sha256(evidence_seed.encode("utf-8")).hexdigest()[:16],
    }


def main() -> int:
    report = build_report()
    write_json(ROOT / "proof" / "runtime" / "hermes-proof-mcp.json", report)
    log_event(
        "proof",
        "hermes.proof_mcp_status",
        report["status"],
        outputs={
            "status": report["status"],
            "available": report["proof_mcp"]["available"],
            "workspace_scope_ok": report["proof_mcp"]["workspace_scope_ok"],
        },
        proof_files=["proof/runtime/hermes-proof-mcp.json"],
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
