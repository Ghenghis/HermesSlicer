from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from scripts.write_hermes_tool_tts_speak_proof import build_report


class TtsProofTests(unittest.TestCase):
    def test_tts_proof_records_blocked_azure_gate_without_secret_values(self) -> None:
        with patch.dict(
            os.environ,
            {
                "AZURE_SPEECH_KEY": "",
                "AZURE_SPEECH_REGION": "",
                "HERMES_ENABLE_TTS": "",
            },
            clear=False,
        ):
            report = build_report()

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["action"], "tts.speak")
        self.assertEqual(report["playback"], "not_attempted")
        self.assertFalse(report["azure_key_present"])
        self.assertFalse(report["azure_region_present"])
        self.assertFalse(report["tts_opt_in_present"])
        self.assertNotIn("AZURE_SPEECH_KEY=", str(report))

    def test_tts_proof_records_opt_in_gate_after_credentials(self) -> None:
        with patch.dict(
            os.environ,
            {
                "AZURE_SPEECH_KEY": "present",
                "AZURE_SPEECH_REGION": "eastus",
                "HERMES_ENABLE_TTS": "",
            },
            clear=False,
        ):
            report = build_report()

        self.assertEqual(report["status"], "blocked")
        self.assertTrue(report["azure_key_present"])
        self.assertTrue(report["azure_region_present"])
        self.assertFalse(report["tts_opt_in_present"])
        self.assertIn("HERMES_ENABLE_TTS=1", report["reason"])


if __name__ == "__main__":
    unittest.main()
