from __future__ import annotations

import json
import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from integrations import hermes_agent_tool


ROOT = Path(__file__).resolve().parents[1]


class FakeHermesContext:
    def __init__(self) -> None:
        self.registrations: list[dict[str, object]] = []

    def register_tool(self, **kwargs: object) -> None:
        self.registrations.append(kwargs)


class HermesIntegrationTests(unittest.TestCase):
    def test_register_uses_upstream_hermes_tool_signature(self) -> None:
        ctx = FakeHermesContext()
        hermes_agent_tool.register(ctx)

        self.assertEqual(len(ctx.registrations), 1)
        registration = ctx.registrations[0]
        self.assertEqual(registration["name"], "slicer_bridge")
        self.assertEqual(registration["toolset"], "hermes_orca")
        self.assertIn("schema", registration)
        self.assertIn("handler", registration)
        schema = registration["schema"]
        self.assertIsInstance(schema, dict)
        self.assertEqual(schema["parameters"]["properties"]["action"]["enum"], sorted(hermes_agent_tool.ACTIONS))

    def test_handler_accepts_args_dict_and_returns_json(self) -> None:
        ctx = FakeHermesContext()
        hermes_agent_tool.register(ctx)
        handler = ctx.registrations[0]["handler"]

        with patch.object(hermes_agent_tool, "slicer_bridge", return_value={"status": "ok", "name": "test"}) as bridge:
            result = handler({"action": "health", "payload": {"sample": True}})

        self.assertEqual(json.loads(result), {"status": "ok", "name": "test"})
        bridge.assert_called_once_with("health", {"sample": True})

    def test_bridge_unavailable_returns_blocked_result(self) -> None:
        with (
            patch.object(hermes_agent_tool, "urlopen", side_effect=OSError("offline")),
            patch.object(hermes_agent_tool, "log_event"),
        ):
            result = hermes_agent_tool.slicer_bridge("health")
        self.assertEqual(result["status"], "blocked")
        self.assertIn("unavailable", result["reason"])

    def test_installable_plugin_wrapper_registers_tool(self) -> None:
        plugin_path = ROOT / "integrations" / "hermes-slicer" / "__init__.py"
        spec = importlib.util.spec_from_file_location("hermes_slicer_plugin_test", plugin_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, {"HERMES_SLICER_ROOT": str(ROOT)}, clear=False):
            spec.loader.exec_module(module)
            ctx = FakeHermesContext()
            module.register(ctx)
        self.assertEqual(ctx.registrations[0]["name"], "slicer_bridge")


if __name__ == "__main__":
    unittest.main()
