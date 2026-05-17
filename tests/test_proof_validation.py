from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_proof import (
    validate_as_user_artifact,
    validate_computer_use_artifact,
    validate_printer_safety_artifact,
    validate_proof_mcp_artifact,
    validate_required_artifact,
    validate_tts_speak_artifact,
)


class ProofValidationTests(unittest.TestCase):
    def test_passed_mcp_artifact_requires_availability_and_workspace_scope(self) -> None:
        errors = validate_proof_mcp_artifact({"status": "passed", "proof_mcp": {"available": False}})

        self.assertTrue(any("available is not true" in error for error in errors))
        self.assertTrue(any("evidence_ledger_ok is not true" in error for error in errors))
        self.assertTrue(any("without workspace_root" in error for error in errors))

    def test_required_artifact_accepts_explicit_ok_status(self) -> None:
        errors = validate_required_artifact(
            "proof/runtime/hermes-tool-health.json",
            {"status": "ok", "actions": [], "hermes_agent_bridge": {"status": "blocked"}},
            ("actions", "hermes_agent_bridge"),
            {"ok"},
        )

        self.assertEqual(errors, [])

    def test_required_artifact_reports_missing_keys(self) -> None:
        errors = validate_required_artifact("proof/runtime/example.json", {"status": "passed"}, ("resolved",))

        self.assertTrue(any("missing required key 'resolved'" in error for error in errors))

    def test_as_user_artifact_rejects_false_passes(self) -> None:
        errors = validate_as_user_artifact({"status": "passed", "as_user_session": {"granted": False}})

        self.assertTrue(any("granted is not true" in error for error in errors))
        self.assertTrue(any("without explicit scopes" in error for error in errors))
        self.assertTrue(any("without grant_id_present=true" in error for error in errors))

    def test_as_user_artifact_rejects_blocked_granted_payload(self) -> None:
        errors = validate_as_user_artifact({"status": "blocked", "as_user_session": {"granted": True}})

        self.assertTrue(any("blocked but as_user_session.granted is true" in error for error in errors))

    def test_computer_use_artifact_rejects_false_passes(self) -> None:
        errors = validate_computer_use_artifact(
            {
                "status": "passed",
                "computer_use": {
                    "available": True,
                    "supported_platform": False,
                    "cua_driver_installed": False,
                    "as_user_session": {"granted": False},
                    "visual_proof": {"passed": False},
                },
            }
        )

        self.assertTrue(any("without supported_platform=true" in error for error in errors))
        self.assertTrue(any("without cua_driver_installed=true" in error for error in errors))
        self.assertTrue(any("without bounded AS_USER grant" in error for error in errors))
        self.assertTrue(any("without visual proof" in error for error in errors))

    def test_computer_use_artifact_rejects_blocked_available_payload(self) -> None:
        errors = validate_computer_use_artifact({"status": "blocked", "computer_use": {"available": True}})

        self.assertTrue(any("blocked but computer_use.available is true" in error for error in errors))

    def test_tts_speak_artifact_accepts_blocked_voice_gate(self) -> None:
        errors = validate_tts_speak_artifact(
            {
                "status": "blocked",
                "action": "tts.speak",
                "agent": "orchestrator",
                "voice": "en-US-JennyNeural",
                "playback": "not_attempted",
                "request": {
                    "text": "HermesSlicer TTS probe.",
                    "voice": "en-US-JennyNeural",
                    "agent": "orchestrator",
                },
                "result": {
                    "status": "blocked",
                    "agent": "orchestrator",
                    "voice": "en-US-JennyNeural",
                    "playback": "not_attempted",
                    "reason": "Azure Speech credentials are not present in this shell.",
                },
                "azure_gate": {
                    "azure_key_present": False,
                    "azure_region_present": False,
                    "tts_opt_in_present": False,
                },
            }
        )

        self.assertEqual(errors, [])

    def test_tts_speak_artifact_rejects_false_playback_pass(self) -> None:
        errors = validate_tts_speak_artifact(
            {
                "status": "passed",
                "action": "tts.speak",
                "agent": "orchestrator",
                "voice": "en-US-JennyNeural",
                "playback": "not_attempted",
                "request": {"text": "x", "voice": "en-US-JennyNeural", "agent": "orchestrator"},
                "result": {"status": "passed"},
                "azure_gate": {
                    "azure_key_present": True,
                    "azure_region_present": True,
                    "tts_opt_in_present": True,
                },
            }
        )

        self.assertTrue(any("playback was not attempted" in error for error in errors))

    def test_printer_safety_artifact_rejects_unblocked_hard_stop(self) -> None:
        errors = validate_printer_safety_artifact(
            {
                "status": "passed",
                "checks": {
                    "default_blocks": True,
                    "clear_gate_can_identify_safe_plate": True,
                    "obstruction_blocks": True,
                    "hard_stop_blocks_commands": False,
                },
                "hard_stop": {"status": "passed", "safety": {"start_print": "enabled"}},
            }
        )

        self.assertTrue(any("hard_stop_blocks_commands" in error for error in errors))
        self.assertTrue(any("hard_stop must be blocked" in error for error in errors))
        self.assertTrue(any("start_print is blocked_in_v1" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
