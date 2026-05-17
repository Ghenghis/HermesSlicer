from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.smoke_hermes_plugin import parse_hermes_version


class ParseHermesVersionTests(unittest.TestCase):
    def test_accepts_exact_v014_release(self) -> None:
        parsed = parse_hermes_version("Hermes Agent v0.14.0 (2026.5.16)")

        self.assertEqual(parsed["version"], "0.14.0")
        self.assertTrue(parsed["matches_expected"])

    def test_rejects_stale_v012_release(self) -> None:
        parsed = parse_hermes_version("Hermes Agent v0.12.0 (2026.1.1)")

        self.assertEqual(parsed["version"], "0.12.0")
        self.assertFalse(parsed["matches_expected"])

    def test_rejects_non_exact_patch_version(self) -> None:
        parsed = parse_hermes_version("Hermes Agent v0.14.1 (2026.5.16)")

        self.assertEqual(parsed["version"], "0.14.1")
        self.assertFalse(parsed["matches_expected"])

    def test_rejects_malformed_version(self) -> None:
        parsed = parse_hermes_version("Hermes Agent current")

        self.assertEqual(parsed["version"], "")
        self.assertFalse(parsed["matches_expected"])


if __name__ == "__main__":
    unittest.main()
