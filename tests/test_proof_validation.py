from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_proof import validate_proof_mcp_artifact


class ProofValidationTests(unittest.TestCase):
    def test_passed_mcp_artifact_requires_availability_and_workspace_scope(self) -> None:
        errors = validate_proof_mcp_artifact({"status": "passed", "proof_mcp": {"available": False}})

        self.assertTrue(any("available is not true" in error for error in errors))
        self.assertTrue(any("evidence_ledger_ok is not true" in error for error in errors))
        self.assertTrue(any("without workspace_root" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
