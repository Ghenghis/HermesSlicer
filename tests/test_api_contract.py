from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.bridge import ACTION_ROUTES


CONTRACT = ROOT / "api_contract.openapi.yaml"
BRIDGE = ROOT / "hermes_slicer" / "bridge.py"


class ApiContractTests(unittest.TestCase):
    def test_openapi_lists_all_bridge_routes(self) -> None:
        contract = CONTRACT.read_text(encoding="utf-8")
        routes = {
            "/health",
            "/api/actions",
            "/api/voices/azure/en",
            "/api/orca/profiles",
            "/api/orca/flsun",
            "/api/agents",
            "/api/proof/recent",
            "/api/action",
            "/api/orca/version",
            "/api/slice/dry-run",
            "/api/slice/export-preflight",
            "/api/slice/export-gcode",
            "/api/chat/message",
            "/api/tts/speak",
        }
        for route in sorted(routes):
            self.assertRegex(contract, rf"(?m)^  {re.escape(route)}:")

    def test_action_routes_stay_in_contract(self) -> None:
        contract = CONTRACT.read_text(encoding="utf-8")
        for _method, route in ACTION_ROUTES.values():
            self.assertRegex(contract, rf"(?m)^  {re.escape(route)}:")

    def test_bridge_static_route_literals_stay_in_contract(self) -> None:
        tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
        ignored = {"/", "", "/api/action"}
        routes = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.startswith("/")
            and node.value not in ignored
            and not node.value.startswith("//")
        }
        contract = CONTRACT.read_text(encoding="utf-8")
        for route in sorted(routes):
            self.assertRegex(contract, rf"(?m)^  {re.escape(route)}:")


if __name__ == "__main__":
    unittest.main()
