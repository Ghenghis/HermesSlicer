from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.proof import LEDGER_PATH, validate_ledger, write_json  # noqa: E402


VALID_ARTIFACT_STATUSES = {"passed", "ok", "partial", "blocked", "warning", "present"}


def load_json(path: str) -> tuple[dict[str, Any], list[str]]:
    full_path = ROOT / path
    if not full_path.exists():
        return {}, [f"{path} is missing"]
    try:
        payload = json.loads(full_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path} is invalid JSON: {exc.msg}"]
    if not isinstance(payload, dict):
        return {}, [f"{path} must contain a JSON object"]
    return payload, []


def status_of(payload: dict[str, Any]) -> str:
    return str(payload.get("status", "present"))


def status_errors(path: str, payload: dict[str, Any], allowed: set[str] = VALID_ARTIFACT_STATUSES) -> list[str]:
    status = status_of(payload)
    if status not in allowed:
        return [f"{path} has unexpected status {status!r}"]
    return []


def paths_equal(left: str, right: Path) -> bool:
    try:
        return Path(left).resolve() == right.resolve()
    except (OSError, RuntimeError):
        return False


def validate_proof_mcp_artifact(proof_mcp: dict[str, Any]) -> list[str]:
    errors = status_errors("proof/runtime/hermes-proof-mcp.json", proof_mcp, {"passed", "blocked", "partial"})
    artifact_status = status_of(proof_mcp)
    proof_payload = proof_mcp.get("proof_mcp", {})
    if not isinstance(proof_payload, dict):
        return [*errors, "proof/runtime/hermes-proof-mcp.json proof_mcp must be an object"]
    must_be_live = artifact_status == "passed" or bool(proof_payload.get("available"))
    if artifact_status == "passed":
        if proof_payload.get("available") is not True:
            errors.append("Hermes Proof MCP artifact is passed but proof_mcp.available is not true")
        if proof_payload.get("evidence_ledger_ok") is not True:
            errors.append("Hermes Proof MCP artifact is passed but evidence_ledger_ok is not true")
    if must_be_live:
        workspace_root = str(proof_payload.get("workspace_root") or proof_mcp.get("workspace_root") or "")
        if not workspace_root:
            errors.append("Hermes Proof MCP is marked available without workspace_root")
        elif not paths_equal(workspace_root, ROOT):
            errors.append(f"Hermes Proof MCP workspace_root {workspace_root!r} does not match {str(ROOT)!r}")
        if proof_payload.get("workspace_scope_ok") is not True:
            errors.append("Hermes Proof MCP is marked available without workspace_scope_ok=true")
    return errors


def validate_required_artifact(
    path: str,
    payload: dict[str, Any],
    required_keys: tuple[str, ...] = (),
    allowed_statuses: set[str] | None = None,
) -> list[str]:
    errors = status_errors(path, payload, allowed_statuses or {"passed"})
    for key in required_keys:
        if key not in payload:
            errors.append(f"{path} is missing required key {key!r}")
    return errors


def validate_as_user_artifact(as_user: dict[str, Any]) -> list[str]:
    errors = status_errors("proof/runtime/as_user_session.json", as_user, {"passed", "blocked"})
    payload = as_user.get("as_user_session", {})
    if not isinstance(payload, dict):
        return [*errors, "proof/runtime/as_user_session.json as_user_session must be an object"]
    if status_of(as_user) == "passed":
        if payload.get("granted") is not True:
            errors.append("AS_USER artifact is passed but as_user_session.granted is not true")
        if not payload.get("scopes"):
            errors.append("AS_USER artifact is passed without explicit scopes")
        if not payload.get("grant_id_present"):
            errors.append("AS_USER artifact is passed without grant_id_present=true")
    elif payload.get("granted") is True:
        errors.append("AS_USER artifact is blocked but as_user_session.granted is true")
    return errors


def validate_computer_use_artifact(computer_use: dict[str, Any]) -> list[str]:
    errors = status_errors("proof/runtime/hermes-computer-use.json", computer_use, {"passed", "blocked"})
    computer_payload = computer_use.get("computer_use", {})
    if not isinstance(computer_payload, dict):
        return [*errors, "proof/runtime/hermes-computer-use.json computer_use must be an object"]
    if status_of(computer_use) == "passed":
        if computer_payload.get("available") is not True:
            errors.append("Hermes computer-use artifact is passed but computer_use.available is not true")
        if computer_payload.get("supported_platform") is not True:
            errors.append("Hermes computer-use artifact is passed without supported_platform=true")
        if computer_payload.get("cua_driver_installed") is not True:
            errors.append("Hermes computer-use artifact is passed without cua_driver_installed=true")
        as_user = computer_payload.get("as_user_session", {})
        if not isinstance(as_user, dict) or as_user.get("granted") is not True:
            errors.append("Hermes computer-use artifact is passed without bounded AS_USER grant")
        visual_proof = computer_payload.get("visual_proof", {})
        if not isinstance(visual_proof, dict) or visual_proof.get("passed") is not True:
            errors.append("Hermes computer-use artifact is passed without visual proof")
    elif computer_payload.get("available") is True:
        errors.append("Hermes computer-use artifact is blocked but computer_use.available is true")
    return errors


def validate_artifacts() -> dict[str, Any]:
    errors: list[str] = []
    artifacts: dict[str, Any] = {}

    bridge, bridge_errors = load_json("proof/runtime/bridge-health.json")
    errors.extend(bridge_errors)
    if bridge:
        artifacts["bridge-health.json"] = status_of(bridge)
        errors.extend(status_errors("proof/runtime/bridge-health.json", bridge, {"ok"}))
        if "hermes_agent_bridge" not in bridge:
            errors.append("proof/runtime/bridge-health.json is stale: missing hermes_agent_bridge")
        else:
            bridge_gate = bridge["hermes_agent_bridge"]
            if bridge_gate.get("live_connectivity_claimed") and not bridge_gate.get("live_proof_present"):
                errors.append("bridge health claims live Hermes Agent connectivity without live_proof_present")
            health_probe = bridge_gate.get("health_probe", {})
            if bridge_gate.get("live_connectivity_claimed"):
                if not isinstance(health_probe, dict):
                    errors.append("bridge health claims live Hermes Agent connectivity without a health_probe object")
                else:
                    for key in ("identity_ok", "version_ok", "release_ok"):
                        if health_probe.get(key) is not True:
                            errors.append(f"bridge health claims live Hermes Agent connectivity without {key}=true")

    proof_mcp, proof_mcp_errors = load_json("proof/runtime/hermes-proof-mcp.json")
    errors.extend(proof_mcp_errors)
    if proof_mcp:
        artifacts["hermes-proof-mcp.json"] = status_of(proof_mcp)
        errors.extend(validate_proof_mcp_artifact(proof_mcp))

    plugin, plugin_errors = load_json("proof/runtime/hermes-plugin-smoke.json")
    errors.extend(plugin_errors)
    if plugin:
        artifacts["hermes-plugin-smoke.json"] = status_of(plugin)
        errors.extend(status_errors("proof/runtime/hermes-plugin-smoke.json", plugin, {"passed", "blocked"}))
        for section in ("committed_project_plugin", "integration_plugin", "isolated_active_project_plugin_harness"):
            section_payload = plugin.get(section, {})
            if not isinstance(section_payload, dict) or section_payload.get("status") != "passed":
                errors.append(f"proof/runtime/hermes-plugin-smoke.json {section} must be passed")
        cwd_fallback = plugin.get("committed_project_plugin_cwd_fallback", {})
        if not isinstance(cwd_fallback, dict) or cwd_fallback.get("status") != "passed":
            errors.append("proof/runtime/hermes-plugin-smoke.json committed_project_plugin_cwd_fallback must be passed")

    computer_use, computer_use_errors = load_json("proof/runtime/hermes-computer-use.json")
    errors.extend(computer_use_errors)
    if computer_use:
        artifacts["hermes-computer-use.json"] = status_of(computer_use)
        errors.extend(validate_computer_use_artifact(computer_use))

    as_user, as_user_errors = load_json("proof/runtime/as_user_session.json")
    errors.extend(as_user_errors)
    if as_user:
        artifacts["as_user_session.json"] = status_of(as_user)
        errors.extend(validate_as_user_artifact(as_user))

    tool_health, tool_health_errors = load_json("proof/runtime/hermes-tool-health.json")
    errors.extend(tool_health_errors)
    if tool_health:
        artifacts["hermes-tool-health.json"] = status_of(tool_health)
        errors.extend(
            validate_required_artifact(
                "proof/runtime/hermes-tool-health.json",
                tool_health,
                ("actions", "hermes_agent_bridge"),
                {"ok"},
            )
        )

    tool_export, tool_export_errors = load_json("proof/runtime/hermes-tool-export_preflight.json")
    errors.extend(tool_export_errors)
    if tool_export:
        artifacts["hermes-tool-export_preflight.json"] = status_of(tool_export)
        errors.extend(validate_required_artifact("proof/runtime/hermes-tool-export_preflight.json", tool_export, ("resolved", "compatibility")))

    tool_request, tool_request_errors = load_json("proof/runtime/hermes-tool-tool_request.json")
    errors.extend(tool_request_errors)
    if tool_request:
        artifacts["hermes-tool-tool_request.json"] = status_of(tool_request)
        errors.extend(validate_required_artifact("proof/runtime/hermes-tool-tool_request.json", tool_request, ("resolved_action", "result")))

    flsun_inventory, flsun_inventory_errors = load_json("proof/runtime/flsun-profile-inventory.json")
    errors.extend(flsun_inventory_errors)
    if flsun_inventory:
        artifacts["flsun-profile-inventory.json"] = status_of(flsun_inventory)
        errors.extend(validate_required_artifact("proof/runtime/flsun-profile-inventory.json", flsun_inventory, ("targets",)))
        targets = flsun_inventory.get("targets", [])
        if not isinstance(targets, list) or len(targets) < 3:
            errors.append("proof/runtime/flsun-profile-inventory.json must include FLSUN target profiles")

    flsun_preflight, flsun_preflight_errors = load_json("proof/runtime/flsun-export-preflight.json")
    errors.extend(flsun_preflight_errors)
    if flsun_preflight:
        artifacts["flsun-export-preflight.json"] = status_of(flsun_preflight)
        errors.extend(validate_required_artifact("proof/runtime/flsun-export-preflight.json", flsun_preflight, ("resolved", "compatibility")))

    flsun_matrix, flsun_matrix_errors = load_json("proof/runtime/flsun-profile-matrix.json")
    errors.extend(flsun_matrix_errors)
    if flsun_matrix:
        artifacts["flsun-profile-matrix.json"] = status_of(flsun_matrix)
        errors.extend(validate_required_artifact("proof/runtime/flsun-profile-matrix.json", flsun_matrix, ("matrix",)))

    printer_observation, printer_observation_errors = load_json("proof/runtime/printer-observation.json")
    errors.extend(printer_observation_errors)
    if printer_observation:
        artifacts["printer-observation.json"] = status_of(printer_observation)
        errors.extend(validate_required_artifact("proof/runtime/printer-observation.json", printer_observation, ("targets", "safety"), {"passed", "partial", "blocked"}))
        safety = printer_observation.get("safety", {})
        if not isinstance(safety, dict) or safety.get("mode") != "read_only_observation":
            errors.append("proof/runtime/printer-observation.json must be read_only_observation mode")
        for target in printer_observation.get("targets", []):
            if isinstance(target, dict) and target.get("safety", {}).get("start_print") != "not_attempted":
                errors.append(f"printer observation target {target.get('target', {}).get('id')} attempted a print start")

    clean_clone, clean_errors = load_json("proof/runtime/clean-clone-rehearsal.json")
    errors.extend(clean_errors)
    if clean_clone:
        artifacts["clean-clone-rehearsal.json"] = status_of(clean_clone)
        errors.extend(status_errors("proof/runtime/clean-clone-rehearsal.json", clean_clone, {"passed"}))
        for step in clean_clone.get("steps", []):
            if isinstance(step, dict) and step.get("status") != "passed":
                errors.append(f"clean clone step {step.get('name')!r} did not pass")

    login_geometry, login_errors = load_json("proof/runtime/login-geometry.json")
    errors.extend(login_errors)
    if login_geometry:
        artifacts["login-geometry.json"] = status_of(login_geometry)
        errors.extend(status_errors("proof/runtime/login-geometry.json", login_geometry, {"passed"}))
        for viewport, payload in login_geometry.get("viewports", {}).items():
            if isinstance(payload, dict) and payload.get("full_card_visible") is not True:
                errors.append(f"login viewport {viewport} is not fully visible")

    screenshots, screenshot_errors = load_json("proof/runtime/screenshot-format.json")
    errors.extend(screenshot_errors)
    if screenshots:
        artifacts["screenshot-format.json"] = status_of(screenshots)
        errors.extend(status_errors("proof/runtime/screenshot-format.json", screenshots, {"passed"}))
        for shot in screenshots.get("screenshots", []):
            if isinstance(shot, dict) and (not shot.get("exists") or not shot.get("image_signature")):
                errors.append(f"screenshot proof failed for {shot.get('file')}")

    v1_checklist, checklist_errors = load_json("proof/runtime/v1-release-checklist.json")
    errors.extend(checklist_errors)
    if v1_checklist:
        artifacts["v1-release-checklist.json"] = status_of(v1_checklist)
        blocked = v1_checklist.get("external_gates", {}).get("blocked", [])
        tag_ready = v1_checklist.get("tag_readiness", {}).get("ready")
        if tag_ready and blocked:
            errors.append("V1 checklist is tag-ready while external gates are blocked")

    return {
        "status": "passed" if not errors else "failed",
        "artifacts": artifacts,
        "errors": errors,
        "hash_chain": {
            "status": "not_applicable",
            "reason": "Local proof/ledger.jsonl events are append-only JSONL without prev_hash fields; Hermes locks MCP hash-chain must be verified separately and workspace-scoped.",
        },
    }


def main() -> int:
    ledger = validate_ledger(LEDGER_PATH)
    artifact_report = validate_artifacts()
    errors = []
    if ledger["status"] != "passed":
        errors.append({"ledger": ledger["errors"]})
    if artifact_report["status"] != "passed":
        errors.append({"artifacts": artifact_report["errors"]})
    report = {
        "status": "passed" if not errors else "failed",
        "ledger": ledger,
        "artifact_report": artifact_report,
        "errors": errors,
    }
    write_json(ROOT / "proof" / "runtime" / "proof-validation.json", report)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
