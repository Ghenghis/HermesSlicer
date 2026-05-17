from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import write_hermes_computer_use_proof as computer_use


class ComputerUseProofTests(unittest.TestCase):
    def test_visual_proof_gate_blocks_when_env_is_missing(self) -> None:
        with patch.dict(computer_use.os.environ, {}, clear=True):
            gate = computer_use.visual_proof_gate()

        self.assertFalse(gate["configured"])
        self.assertFalse(gate["passed"])

    def test_visual_proof_gate_rejects_paths_outside_proof_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            outside = Path(temp_dir) / "visual-proof.txt"
            outside.write_text("visual proof", encoding="utf-8")
            with patch.dict(computer_use.os.environ, {computer_use.VISUAL_PROOF_PATH_ENV: str(outside)}, clear=False):
                gate = computer_use.visual_proof_gate()

        self.assertTrue(gate["configured"])
        self.assertFalse(gate["passed"])
        self.assertIn("proof", gate["reason"])

    def test_visual_proof_gate_rejects_missing_file_under_proof_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            fake_root = Path(temp_root)
            missing = fake_root / "proof" / "missing.txt"
            with (
                patch.object(computer_use, "ROOT", fake_root),
                patch.dict(computer_use.os.environ, {computer_use.VISUAL_PROOF_PATH_ENV: str(missing)}, clear=False),
            ):
                gate = computer_use.visual_proof_gate()

        self.assertTrue(gate["configured"])
        self.assertFalse(gate["passed"])
        self.assertIn("does not exist", gate["reason"])

    def test_visual_proof_gate_accepts_existing_file_under_proof_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_root:
            fake_root = Path(temp_root)
            proof_file = fake_root / "proof" / "visual.txt"
            proof_file.parent.mkdir(parents=True)
            proof_file.write_text("visual proof", encoding="utf-8")
            with (
                patch.object(computer_use, "ROOT", fake_root),
                patch.dict(computer_use.os.environ, {computer_use.VISUAL_PROOF_PATH_ENV: str(proof_file)}, clear=False),
            ):
                gate = computer_use.visual_proof_gate()

        self.assertTrue(gate["passed"])
        self.assertEqual(Path(gate["path"]), proof_file)

    def test_build_report_blocks_on_windows_even_with_other_gates_present(self) -> None:
        with (
            patch.object(computer_use.sys, "platform", "win32"),
            patch.object(computer_use.platform, "system", return_value="Windows"),
            patch.object(computer_use.shutil, "which", side_effect=lambda name: f"C:/bin/{name}.exe"),
            patch.object(computer_use, "run_command", return_value={"status": "passed"}),
            patch.object(computer_use, "as_user_session_gate", return_value={"status": "passed", "granted": True}),
            patch.object(computer_use, "visual_proof_gate", return_value={"configured": True, "passed": True}),
        ):
            report = computer_use.build_report()

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["computer_use"]["available"])
        self.assertFalse(report["computer_use"]["supported_platform"])

    def test_build_report_passes_only_on_macos_with_all_gates_present(self) -> None:
        with (
            patch.object(computer_use.sys, "platform", "darwin"),
            patch.object(computer_use.platform, "system", return_value="Darwin"),
            patch.object(computer_use.shutil, "which", side_effect=lambda name: f"/usr/local/bin/{name}"),
            patch.object(computer_use, "run_command", return_value={"status": "passed"}),
            patch.object(computer_use, "as_user_session_gate", return_value={"status": "passed", "granted": True}),
            patch.object(computer_use, "visual_proof_gate", return_value={"configured": True, "passed": True}),
        ):
            report = computer_use.build_report()

        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["computer_use"]["available"])
        self.assertTrue(report["computer_use"]["supported_platform"])


if __name__ == "__main__":
    unittest.main()
