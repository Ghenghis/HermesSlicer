from __future__ import annotations

import unittest
from pathlib import Path

from hermes_slicer.bridge import dispatch_action, run, tts_speak
from hermes_slicer.config import ALLOWED_ACTIONS, default_slice_request
from hermes_slicer.proof import validate_event
from hermes_slicer.security import sanitize_text
from hermes_slicer.slicer import ValidationError, dry_run_slice, flsun_profile_inventory, validate_slice_request


class BridgeCoreTests(unittest.TestCase):
    def test_actions_are_whitelisted(self) -> None:
        ids = {action["id"] for action in ALLOWED_ACTIONS}
        self.assertIn("bridge.health", ids)
        self.assertIn("orca.version", ids)
        self.assertIn("orca.profiles", ids)
        self.assertIn("orca.flsun_inventory", ids)
        self.assertIn("slice.dry_run", ids)
        self.assertIn("tts.speak", ids)

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

    def test_flsun_inventory_shape(self) -> None:
        payload = flsun_profile_inventory()
        self.assertIn(payload["status"], {"passed", "blocked"})
        if payload["status"] == "passed":
            models = {entry["model"] for entry in payload["targets"]}
            self.assertTrue({"FLSun T1", "FLSun V400", "FLSun S1"}.issubset(models))

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


if __name__ == "__main__":
    unittest.main()
