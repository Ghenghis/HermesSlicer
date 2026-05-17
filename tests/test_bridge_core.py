from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hermes_slicer.bridge import ACTION_ROUTES, dispatch_action, run, tts_speak
from hermes_slicer.config import ALLOWED_ACTIONS, default_slice_request, hermes_agent_bridge_gate
from hermes_slicer.proof import validate_event
from hermes_slicer.security import sanitize_text
from hermes_slicer.slicer import ValidationError, dry_run_slice, export_gcode, flsun_export_preflight, flsun_profile_inventory, validate_slice_request


class BridgeCoreTests(unittest.TestCase):
    def test_actions_are_whitelisted(self) -> None:
        ids = {action["id"] for action in ALLOWED_ACTIONS}
        self.assertIn("bridge.health", ids)
        self.assertIn("orca.version", ids)
        self.assertIn("orca.profiles", ids)
        self.assertIn("orca.flsun_inventory", ids)
        self.assertIn("agents.list", ids)
        self.assertIn("proof.recent", ids)
        self.assertIn("hermes.proof_mcp", ids)
        self.assertIn("slice.dry_run", ids)
        self.assertIn("slice.export_preflight", ids)
        self.assertIn("tts.speak", ids)

    def test_every_whitelisted_action_is_dispatchable(self) -> None:
        ids = {action["id"] for action in ALLOWED_ACTIONS}
        self.assertEqual(ids, set(ACTION_ROUTES))

    def test_dry_run_default_sample(self) -> None:
        payload = dry_run_slice({})
        self.assertEqual(payload["status"], "passed")
        self.assertTrue(Path(payload["request"]["model_path"]).exists())
        self.assertFalse(payload["request"]["confirm_print"])

    def test_path_validation_blocks_private(self) -> None:
        request = default_slice_request()
        request["model_path"] = "G:/Private/model.stl"
        with self.assertRaises(ValidationError):
            validate_slice_request(request)

    def test_redaction_sanitizes_sensitive_text(self) -> None:
        sensitive_value = "abcd" + "efgh" + "ijkl" + "mnop"
        text = sanitize_text(f"Authorization: Bearer {sensitive_value}")
        self.assertNotIn(sensitive_value, text)
        self.assertIn("<REDACTED>", text)

    def test_invalid_action_returns_bad_request_payload(self) -> None:
        payload, status = dispatch_action({"action": "not.allowed"})
        self.assertEqual(status, 400)
        self.assertEqual(payload["status"], "failed")
        self.assertIn("allowed", payload)

    def test_dispatch_health(self) -> None:
        payload, status = dispatch_action({"action": "bridge.health"})
        self.assertEqual(status, 200)
        self.assertEqual(payload["bind"], "127.0.0.1")

    def test_dispatch_health_reports_runtime_port(self) -> None:
        empty_gate_env = {
            "HERMES_AGENT_ENABLED": "",
            "HERMES_AGENT_HEALTHCHECK_OK": "",
            "HERMES_AGENT_LIVE_PROOF": "",
            "HERMES_AGENT_HEALTH_URL": "",
            "DEEPSEEK_API_KEY": "",
            "MINIMAX_API_KEY": "",
            "SILICONFLOW_API_KEY": "",
            "HERMES_AGENT_BASE_URL": "",
            "LM_STUDIO_BASE_URL": "",
            "OPENAI_BASE_URL": "",
        }
        with patch.dict(os.environ, empty_gate_env, clear=False):
            payload, status = dispatch_action({"action": "bridge.health"}, bind="127.0.0.1", port=8766)
        self.assertEqual(status, 200)
        self.assertEqual(payload["port"], 8766)
        self.assertIn("hermes_agent_bridge", payload)
        self.assertFalse(payload["hermes_agent_bridge"]["live_connectivity_claimed"])

    def test_hermes_agent_live_gate_requires_enabled_and_backend(self) -> None:
        empty_gate_env = {
            "HERMES_AGENT_ENABLED": "",
            "HERMES_AGENT_HEALTHCHECK_OK": "",
            "HERMES_AGENT_LIVE_PROOF": "",
            "HERMES_AGENT_HEALTH_URL": "",
            "DEEPSEEK_API_KEY": "",
            "MINIMAX_API_KEY": "",
            "SILICONFLOW_API_KEY": "",
            "HERMES_AGENT_BASE_URL": "",
            "LM_STUDIO_BASE_URL": "",
            "OPENAI_BASE_URL": "",
        }
        with patch.dict(os.environ, empty_gate_env, clear=False):
            payload = hermes_agent_bridge_gate()
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["live_connectivity_claimed"])

        live_gate_env = {**empty_gate_env, "HERMES_AGENT_ENABLED": "1", "DEEPSEEK_API_KEY": "present"}
        with patch.dict(os.environ, live_gate_env, clear=False):
            payload = hermes_agent_bridge_gate()
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["live_connectivity_claimed"])
        self.assertTrue(payload["configured"])
        self.assertFalse(payload["live_proof_present"])

        attested_gate_env = {**live_gate_env, "HERMES_AGENT_HEALTHCHECK_OK": "1"}
        with patch.dict(os.environ, attested_gate_env, clear=False):
            payload = hermes_agent_bridge_gate()
        self.assertEqual(payload["status"], "blocked")
        self.assertTrue(payload["operator_attestation_env_present"]["HERMES_AGENT_HEALTHCHECK_OK"])

        proved_gate_env = {**live_gate_env, "HERMES_AGENT_HEALTH_URL": "http://127.0.0.1:9876/hermes-agent/health"}
        with patch.dict(os.environ, proved_gate_env, clear=False), patch("hermes_slicer.config.urlopen", return_value=FakeHealthResponse()):
            payload = hermes_agent_bridge_gate()
        self.assertEqual(payload["status"], "passed")
        self.assertTrue(payload["live_connectivity_claimed"])

        with patch.dict(os.environ, proved_gate_env, clear=False), patch("hermes_slicer.config.urlopen", return_value=FakeHealthResponse(body=b"<html>ok</html>")):
            payload = hermes_agent_bridge_gate()
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["live_connectivity_claimed"])

    def test_tool_request_health_reports_runtime_port(self) -> None:
        payload, status = dispatch_action({"action": "hermes_agent.tool_request", "payload": {"message": "health"}}, port=8766)
        self.assertEqual(status, 200)
        self.assertEqual(payload["result"]["port"], 8766)

    def test_flsun_inventory_shape(self) -> None:
        payload = flsun_profile_inventory()
        self.assertIn(payload["status"], {"passed", "blocked"})
        if payload["status"] == "passed":
            models = {entry["model"] for entry in payload["targets"]}
            self.assertTrue({"FLSun T1", "FLSun V400", "FLSun S1"}.issubset(models))

    def test_flsun_preflight_resolves_default_t1_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_flsun_fixture(Path(tmp))
            payload = flsun_export_preflight({}, profile_roots=[root])
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["resolved"]["model"], "FLSun T1")
        self.assertEqual(payload["resolved"]["machine"]["name"], "FLSun T1 0.4 nozzle")
        self.assertEqual(payload["resolved"]["process"]["name"], "0.20mm Standard @FLSun T1")
        self.assertEqual(payload["resolved"]["filament"]["name"], "FLSun T1 PLA Generic")
        self.assertTrue(payload["compatibility"]["process"])
        self.assertTrue(payload["compatibility"]["filament"])

    def test_flsun_preflight_resolves_v400_generic_default_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_flsun_fixture(Path(tmp))
            payload = flsun_export_preflight(
                {"printer_profile": "FLSun V400", "material_profile": "PLA_safe_default"},
                profile_roots=[root],
            )
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["resolved"]["model"], "FLSun V400")
        self.assertEqual(payload["resolved"]["filament"]["name"], "FLSun Generic PLA")

    def test_flsun_preflight_blocks_incompatible_filament_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_flsun_fixture(Path(tmp))
            payload = flsun_export_preflight(
                {"printer_profile": "FLSun S1", "material_profile": "FLSun Generic PLA"},
                profile_roots=[root],
            )
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["compatibility"]["filament"])

    def test_dispatch_export_preflight(self) -> None:
        with patch("hermes_slicer.bridge.flsun_export_preflight", return_value={"status": "passed"}):
            payload, status = dispatch_action({"action": "slice.export_preflight", "payload": {}})
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "passed")

    def test_dispatch_hermes_agent_tool_request(self) -> None:
        payload, status = dispatch_action({"action": "hermes_agent.tool_request", "payload": {"message": "health"}})
        self.assertEqual(status, 200)
        self.assertEqual(payload["resolved_action"], "bridge.health")
        self.assertEqual(payload["toolset"], "hermes_agent")

    def test_dispatch_chat_rejects_jusprin_style_setting_changes(self) -> None:
        payload, status = dispatch_action({"action": "hermes_agent.tool_request", "payload": {"message": "I want a fast draft print"}})
        self.assertEqual(status, 200)
        self.assertEqual(payload["resolved_action"], None)
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("Hermes Agent", payload["reply"])
        self.assertIn("will not silently apply", payload["reply"])

    def test_dispatch_hermes_proof_mcp_status(self) -> None:
        payload, status = dispatch_action({"action": "hermes.proof_mcp"})
        self.assertEqual(status, 200)
        self.assertIn(payload["status"], {"partial", "passed", "blocked", "failed"})

    def test_explicit_tool_id_request_routes_to_tool(self) -> None:
        payload, status = dispatch_action({"action": "hermes_agent.tool_request", "payload": {"message": "slice.export_preflight"}})
        self.assertEqual(status, 200)
        self.assertEqual(payload["resolved_action"], "slice.export_preflight")

    def test_export_stays_disabled_but_reports_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"HERMES_ENABLE_EXPORT_GCODE": ""}, clear=False):
            root = build_flsun_fixture(Path(tmp))
            payload = export_gcode({}, profile_roots=[root])
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["profile_preflight"]["status"], "passed")

    def test_export_blocks_with_env_when_preflight_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"HERMES_ENABLE_EXPORT_GCODE": "1"}, clear=False):
            root = build_flsun_fixture(Path(tmp))
            payload = export_gcode(
                {"printer_profile": "FLSun S1", "material_profile": "FLSun Generic PLA"},
                profile_roots=[root],
            )
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["profile_preflight"]["status"], "blocked")

    def test_tts_blocks_without_or_before_live_adapter(self) -> None:
        payload = tts_speak({"voice": "en-US-JennyNeural", "text": "Hermes voice smoke test."})
        self.assertIn(payload["status"], {"blocked", "passed"})
        self.assertNotIn("key", jsonish(payload).lower())

    def test_bridge_rejects_non_localhost_bind(self) -> None:
        with self.assertRaises(SystemExit):
            run("0.0.0.0", 8765)

    def test_validate_event_catches_missing_keys(self) -> None:
        errors = validate_event({"status": "passed"})
        self.assertTrue(errors)


def jsonish(value: object) -> str:
    return str(value)


class FakeHealthResponse:
    def __init__(self, body: bytes = b'{"status":"passed"}', status: int = 200) -> None:
        self.body = body
        self.status = status

    def __enter__(self) -> "FakeHealthResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _limit: int = -1) -> bytes:
        return self.body


def build_flsun_fixture(base: Path) -> Path:
    root = base / "profiles"
    vendor = root / "FLSun"
    for folder in ("machine", "process", "filament"):
        (vendor / folder).mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": "test",
        "machine_model_list": [
            {"name": "FLSun T1", "sub_path": "machine/FLSun T1.json"},
            {"name": "FLSun V400", "sub_path": "machine/FLSun V400.json"},
            {"name": "FLSun S1", "sub_path": "machine/FLSun S1.json"},
        ],
        "machine_list": [
            {"name": "fdm_machine_common", "sub_path": "machine/fdm_machine_common.json"},
            {"name": "FLSun T1 0.4 nozzle", "sub_path": "machine/FLSun T1 0.4 nozzle.json"},
            {"name": "FLSun V400 0.4 nozzle", "sub_path": "machine/FLSun V400 0.4 nozzle.json"},
            {"name": "FLSun S1 0.4 nozzle", "sub_path": "machine/FLSun S1 0.4 nozzle.json"},
        ],
        "process_list": [
            {"name": "fdm_process_common", "sub_path": "process/fdm_process_common.json"},
            {"name": "0.20mm Standard @FLSun T1", "sub_path": "process/0.20mm Standard @FLSun T1.json"},
            {"name": "0.20mm Standard @FLSun V400", "sub_path": "process/0.20mm Standard @FLSun V400.json"},
            {"name": "0.20mm Standard @FLSun S1", "sub_path": "process/0.20mm Standard @FLSun S1.json"},
        ],
        "filament_list": [
            {"name": "fdm_filament_pla", "sub_path": "filament/fdm_filament_pla.json"},
            {"name": "FLSun Generic PLA", "sub_path": "filament/FLSun Generic PLA.json"},
            {"name": "FLSun T1 PLA Generic", "sub_path": "filament/FLSun T1 PLA Generic.json"},
            {"name": "FLSun S1 PLA Generic", "sub_path": "filament/FLSun S1 PLA Generic.json"},
        ],
    }
    write_json(root / "FLSun.json", manifest)
    write_json(vendor / "machine" / "fdm_machine_common.json", {"type": "machine", "name": "fdm_machine_common"})
    write_json(vendor / "process" / "fdm_process_common.json", {"type": "process", "name": "fdm_process_common"})
    write_json(vendor / "filament" / "fdm_filament_pla.json", {"type": "filament", "name": "fdm_filament_pla"})
    write_json(
        vendor / "machine" / "FLSun T1.json",
        {"type": "machine_model", "name": "FLSun T1", "model_id": "FLSun_T1", "default_materials": "FLSun T1 PLA Generic"},
    )
    write_json(
        vendor / "machine" / "FLSun V400.json",
        {"type": "machine_model", "name": "FLSun V400", "model_id": "FLSun_V400", "default_materials": "FLSun Generic PLA"},
    )
    write_json(
        vendor / "machine" / "FLSun S1.json",
        {"type": "machine_model", "name": "FLSun S1", "model_id": "FLSun_S1", "default_materials": "FLSun S1 PLA Generic"},
    )
    for model in ("FLSun T1", "FLSun V400", "FLSun S1"):
        write_json(
            vendor / "machine" / f"{model} 0.4 nozzle.json",
            {
                "type": "machine",
                "name": f"{model} 0.4 nozzle",
                "inherits": "fdm_machine_common",
                "printer_model": model,
                "default_print_profile": f"0.20mm Standard @{model}",
            },
        )
        write_json(
            vendor / "process" / f"0.20mm Standard @{model}.json",
            {
                "type": "process",
                "name": f"0.20mm Standard @{model}",
                "inherits": "fdm_process_common",
                "compatible_printers": [f"{model} 0.4 nozzle"],
            },
        )
    write_json(
        vendor / "filament" / "FLSun Generic PLA.json",
        {
            "type": "filament",
            "name": "FLSun Generic PLA",
            "inherits": "fdm_filament_pla",
            "compatible_printers": ["FLSun V400 0.4 nozzle"],
        },
    )
    write_json(
        vendor / "filament" / "FLSun T1 PLA Generic.json",
        {
            "type": "filament",
            "name": "FLSun T1 PLA Generic",
            "inherits": "FLSun Generic PLA",
            "compatible_printers": ["FLSun T1 0.4 nozzle"],
        },
    )
    write_json(
        vendor / "filament" / "FLSun S1 PLA Generic.json",
        {
            "type": "filament",
            "name": "FLSun S1 PLA Generic",
            "inherits": "FLSun Generic PLA",
            "compatible_printers": ["FLSun S1 0.4 nozzle"],
        },
    )
    return root


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
