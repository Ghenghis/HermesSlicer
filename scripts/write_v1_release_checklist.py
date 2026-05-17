from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.config import as_user_session_gate, hermes_agent_bridge_gate  # noqa: E402
from hermes_slicer.proof import log_event, write_json  # noqa: E402


LOCAL_PROOF_FILES = (
    "proof/runtime/bridge-health.json",
    "proof/runtime/smoke-report.md",
    "proof/runtime/proof-validation.json",
    "proof/runtime/screenshot-format.json",
    "proof/runtime/login-geometry.json",
    "proof/runtime/hermes-proof-mcp.json",
    "proof/runtime/submodule-stack.json",
    "proof/runtime/flsun-export-preflight.json",
    "proof/runtime/hermes-tool-health.json",
    "proof/runtime/hermes-tool-export_preflight.json",
    "proof/runtime/hermes-tool-tool_request.json",
    "proof/security/redaction-report.md",
)


def file_status(path: str) -> dict[str, Any]:
    full_path = ROOT / path
    return {"file": path, "exists": full_path.exists(), "bytes": full_path.stat().st_size if full_path.exists() else 0}


def load_status(path: str) -> str:
    full_path = ROOT / path
    if not full_path.exists() or full_path.suffix.lower() != ".json":
        return "missing" if not full_path.exists() else "present"
    try:
        payload = json.loads(full_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return "invalid_json"
    return str(payload.get("status", "present"))


def load_json(path: str) -> dict[str, Any]:
    full_path = ROOT / path
    if not full_path.exists() or full_path.suffix.lower() != ".json":
        return {}
    try:
        return json.loads(full_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def build_report() -> dict[str, Any]:
    proof_files = [file_status(path) for path in LOCAL_PROOF_FILES]
    missing = [item["file"] for item in proof_files if not item["exists"]]
    failed = [
        path
        for path in LOCAL_PROOF_FILES
        if path.endswith(".json") and load_status(path) not in {"passed", "ok", "partial", "blocked", "present"}
    ]
    hermes_agent = hermes_agent_bridge_gate()
    as_user = as_user_session_gate()
    clean_clone = file_status("proof/runtime/clean-clone-rehearsal.json")
    plugin_smoke = file_status("proof/runtime/hermes-plugin-smoke.json")
    proof_mcp = load_json("proof/runtime/hermes-proof-mcp.json")
    blocked_external = []
    if hermes_agent["status"] != "passed":
        blocked_external.append(
            {
                "gate": "live_hermes_agent_provider_bridge",
                "reason": hermes_agent["reason"],
                "required": hermes_agent["required"],
            }
        )
    if as_user["status"] != "passed":
        blocked_external.append(
            {
                "gate": "bounded_as_user_grants",
                "reason": as_user["reason"],
                "required": as_user["required"],
            }
        )
    if not proof_mcp.get("proof_mcp", {}).get("available"):
        blocked_external.append(
            {
                "gate": "hermes_proof_mcp_transport",
                "reason": proof_mcp.get("proof_mcp", {}).get("reason", "Hermes Proof MCP is not available in the current session."),
                "required": ["working Hermes Proof MCP transport", "successful evidence verification"],
            }
        )
    if not plugin_smoke["exists"]:
        blocked_external.append(
            {
                "gate": "active_hermes_plugin_smoke",
                "reason": "No proof artifact exists for an active Hermes install loading integrations/hermes-slicer.",
                "required": ["HERMES_ENABLE_PROJECT_PLUGINS=1", "active hermes CLI/install"],
            }
        )

    local_ready = not missing and not failed
    clean_clone_passed = clean_clone["exists"] and load_status(clean_clone["file"]) == "passed"
    tag_ready = local_ready and clean_clone_passed and not blocked_external
    readiness_note = (
        "Do not tag V1 until external live-agent, MCP, and plugin gates are proved or explicitly accepted as release-blocking owner decisions."
        if clean_clone_passed
        else "Do not tag V1 until clean-clone rehearsal passes and external live-agent/plugin gates are proved or explicitly accepted as release-blocking owner decisions."
    )
    return {
        "status": "passed" if tag_ready else "blocked",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "proof_summary": {
            "local_proof_files": proof_files,
            "missing": missing,
            "failed": failed,
            "clean_clone_rehearsal": clean_clone,
            "plugin_smoke": plugin_smoke,
        },
        "external_gates": {
            "proof_mcp": proof_mcp.get("proof_mcp", {}),
            "hermes_agent_bridge": hermes_agent,
            "as_user_session": as_user,
            "blocked": blocked_external,
        },
        "tag_readiness": {
            "ready": tag_ready,
            "local_gates_ready": local_ready,
            "clean_clone_rehearsal_passed": clean_clone_passed,
            "notes": readiness_note,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    proof = report["proof_summary"]
    blocked = report["external_gates"]["blocked"]
    tag = report["tag_readiness"]
    lines = [
        "# HermesSlicer V1 Release Checklist",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Proof Summary",
        "",
        f"- Local proof files present: {len(proof['local_proof_files']) - len(proof['missing'])}/{len(proof['local_proof_files'])}",
        f"- Missing proof files: {', '.join(proof['missing']) if proof['missing'] else 'none'}",
        f"- Failed/invalid proof files: {', '.join(proof['failed']) if proof['failed'] else 'none'}",
        f"- Clean-clone rehearsal: {load_status('proof/runtime/clean-clone-rehearsal.json') if proof['clean_clone_rehearsal']['exists'] else 'missing'}",
        f"- Active Hermes plugin smoke: {load_status('proof/runtime/hermes-plugin-smoke.json') if proof['plugin_smoke']['exists'] else 'missing'}",
        "",
        "## Blocked External Gates",
        "",
    ]
    if blocked:
        for item in blocked:
            required = ", ".join(item["required"])
            lines.append(f"- {item['gate']}: {item['reason']} Required: {required}.")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Tag Readiness",
            "",
            f"- Ready to tag V1: {'yes' if tag['ready'] else 'no'}",
            f"- Local gates ready: {'yes' if tag['local_gates_ready'] else 'no'}",
            f"- Clean-clone rehearsal passed: {'yes' if tag['clean_clone_rehearsal_passed'] else 'no'}",
            f"- Notes: {tag['notes']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    write_json(ROOT / "proof" / "runtime" / "v1-release-checklist.json", report)
    (ROOT / "V1_RELEASE_CHECKLIST.md").write_text(render_markdown(report), encoding="utf-8")
    log_event(
        "proof",
        "v1.release_checklist",
        report["status"],
        outputs={
            "tag_ready": report["tag_readiness"]["ready"],
            "blocked_external_gates": [item["gate"] for item in report["external_gates"]["blocked"]],
        },
        proof_files=["proof/runtime/v1-release-checklist.json", "V1_RELEASE_CHECKLIST.md"],
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
