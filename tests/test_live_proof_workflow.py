from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import write_hermes_proof_mcp_live as live


PASSED_BRIDGE = {
    "status": "passed",
    "available": True,
    "live_connectivity_claimed": True,
    "live_proof_present": True,
    "reason": "ok",
}
PASSED_AS_USER = {
    "status": "passed",
    "granted": True,
    "grant_id_present": True,
    "scopes": ["visual.inspect"],
    "reason": "ok",
}
PASSED_AS_USER_ARTIFACT = {
    "status": "passed",
    "as_user_session": PASSED_AS_USER,
}


class LiveProofWorkflowTests(unittest.TestCase):
    def test_build_report_passes_only_when_all_live_gates_are_proven(self) -> None:
        verify_payload = {
            "status": "passed",
            "ok": True,
            "tool": "hermes_verify_evidence",
            "transport_status": "available",
            "workspace_root": str(ROOT),
            "evidence_ledger_ok": True,
        }

        with (
            patch.object(live, "hermes_agent_bridge_gate", return_value=PASSED_BRIDGE),
            patch.object(live, "as_user_session_gate", return_value=PASSED_AS_USER),
            patch.object(live, "_load_json", return_value=(PASSED_AS_USER_ARTIFACT, None)),
        ):
            report = live.build_report(verify_payload=verify_payload, now="2026-05-17T00:00:00+00:00")

        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["proof_mcp"]["available"])
        self.assertTrue(report["proof_mcp"]["workspace_scope_ok"])
        self.assertTrue(report["proof_mcp"]["evidence_ledger_ok"])

    def test_transport_gate_rejects_other_workspace_scope(self) -> None:
        gate = live.hermes_mcp_transport_gate(
            ROOT,
            {
                "status": "passed",
                "ok": True,
                "tool": "hermes_verify_evidence",
                "transport_status": "available",
                "workspace_root": "G:\\Github\\Hermes3D",
                "evidence_ledger_ok": True,
            },
        )

        self.assertEqual(gate["status"], "blocked")
        self.assertFalse(gate["workspace_scope_ok"])
        self.assertFalse(gate["available"])

    def test_transport_gate_rejects_unidentified_verifier(self) -> None:
        gate = live.hermes_mcp_transport_gate(
            ROOT,
            {
                "status": "passed",
                "ok": True,
                "transport_status": "available",
                "workspace_root": str(ROOT),
                "evidence_ledger_ok": True,
            },
        )

        self.assertEqual(gate["status"], "blocked")
        self.assertEqual(gate["verify_tool"], "not_supplied")
        self.assertFalse(gate["available"])

    def test_active_mcp_config_scope_requires_current_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            hermes_home = Path(temp_dir) / "hermes"
            hermes_home.mkdir()
            configured_root = Path(temp_dir) / "HermesSlicer"
            config_path = hermes_home / "config.yaml"
            config_path.write_text(
                f"mcp_servers:\n  hermes-slicer-proof:\n    args:\n    - {configured_root}\\scripts\\run_mcp_server.py\n",
                encoding="utf-8",
            )
            with patch.dict(live.os.environ, {"HERMES_HOME": str(hermes_home)}, clear=False), patch.object(live, "ROOT", configured_root):
                scope = live._active_mcp_config_scope()

            with patch.dict(live.os.environ, {"HERMES_HOME": str(hermes_home)}, clear=False), patch.object(live, "ROOT", Path(temp_dir) / "OtherClone"):
                wrong_scope = live._active_mcp_config_scope()

        self.assertTrue(scope["passed"])
        self.assertFalse(wrong_scope["passed"])
        self.assertFalse(wrong_scope["workspace_root_configured"])

    def test_build_report_keeps_mcp_available_when_other_live_gates_are_blocked(self) -> None:
        verify_payload = {
            "status": "passed",
            "ok": True,
            "tool": "hermes_verify_evidence",
            "transport_status": "available",
            "workspace_root": str(ROOT),
            "evidence_ledger_ok": True,
        }
        blocked_bridge = {**PASSED_BRIDGE, "status": "blocked", "live_connectivity_claimed": False, "reason": "bridge blocked"}
        blocked_as_user = {**PASSED_AS_USER, "status": "blocked", "granted": False, "reason": "as_user blocked"}

        with (
            patch.object(live, "hermes_agent_bridge_gate", return_value=blocked_bridge),
            patch.object(live, "as_user_session_gate", return_value=blocked_as_user),
            patch.object(live, "_load_json", return_value=({}, "as_user artifact blocked")),
        ):
            report = live.build_report(verify_payload=verify_payload, now="2026-05-17T00:00:00+00:00")

        self.assertEqual(report["status"], "blocked")
        self.assertTrue(report["proof_mcp"]["available"])
        self.assertTrue(report["proof_mcp"]["workspace_scope_ok"])
        self.assertTrue(report["proof_mcp"]["evidence_ledger_ok"])

    def test_main_does_not_write_blocked_report_by_default(self) -> None:
        blocked_bridge = {**PASSED_BRIDGE, "status": "blocked", "live_connectivity_claimed": False, "reason": "blocked"}
        verify_payload = {
            "status": "passed",
            "ok": True,
            "tool": "hermes_verify_evidence",
            "transport_status": "available",
            "workspace_root": str(ROOT),
            "evidence_ledger_ok": True,
        }

        with (
            patch.object(live, "hermes_agent_bridge_gate", return_value=blocked_bridge),
            patch.object(live, "as_user_session_gate", return_value=PASSED_AS_USER),
            patch.object(live, "_load_json", return_value=(PASSED_AS_USER_ARTIFACT, None)),
            patch.object(live, "_load_verify_payload", return_value=(verify_payload, None)),
            patch.object(live, "write_json") as write_json,
            patch.object(live, "log_event") as log_event,
            patch.object(live, "print"),
        ):
            code = live.main([])

        self.assertEqual(code, 1)
        write_json.assert_not_called()
        self.assertEqual(log_event.call_args.kwargs["proof_files"], [])

    def test_main_can_write_blocked_report_when_requested(self) -> None:
        with (
            patch.object(live, "hermes_agent_bridge_gate", return_value={**PASSED_BRIDGE, "status": "blocked", "live_connectivity_claimed": False}),
            patch.object(live, "as_user_session_gate", return_value=PASSED_AS_USER),
            patch.object(live, "_load_json", return_value=(PASSED_AS_USER_ARTIFACT, None)),
            patch.object(live, "_load_verify_payload", return_value=({}, "transport closed")),
            patch.object(live, "write_json") as write_json,
            patch.object(live, "log_event"),
            patch.object(live, "print"),
        ):
            code = live.main(["--write-blocked"])

        self.assertEqual(code, 1)
        write_json.assert_called_once()
        self.assertEqual(write_json.call_args.args[1]["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
