from __future__ import annotations

import configparser
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED = {
    "upstream/OrcaSlicer": "https://github.com/OrcaSlicer/OrcaSlicer.git",
    "upstream/FlsunSlicer": "https://github.com/Flsun3d/FlsunSlicer.git",
    "upstream/JusPrin": "https://github.com/TheSpaghettiDetective/JusPrin.git",
    "upstream/PrusaSlicer": "https://github.com/prusa3d/PrusaSlicer.git",
    "upstream/hermes-agent": "https://github.com/NousResearch/hermes-agent.git",
    "upstream/mcp-python-sdk": "https://github.com/modelcontextprotocol/python-sdk.git",
    "upstream/moonraker": "https://github.com/Arksine/moonraker.git",
    "upstream/OctoPrint": "https://github.com/OctoPrint/OctoPrint.git",
    "upstream/klipper": "https://github.com/Klipper3d/klipper.git",
}


class SubmoduleStackTests(unittest.TestCase):
    def test_gitmodules_declares_complete_e2e_stack(self) -> None:
        parser = configparser.ConfigParser()
        parser.read(ROOT / ".gitmodules", encoding="utf-8")

        found = {parser[section]["path"]: parser[section]["url"] for section in parser.sections()}
        self.assertEqual(found, EXPECTED)


if __name__ == "__main__":
    unittest.main()
