from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from hermes_slicer import mcp_server


ROOT = Path(__file__).resolve().parents[1]


class McpServerTests(unittest.TestCase):
    def test_initialize_reports_workspace_scoped_server(self) -> None:
        response = mcp_server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})

        assert response is not None
        result = response["result"]
        self.assertEqual(result["serverInfo"]["name"], "hermes-slicer-proof")
        self.assertTrue(result["workspace"]["workspace_scope_ok"])
        self.assertEqual(Path(result["workspace"]["expected_workspace_root"]), ROOT.resolve())

    def test_tools_list_exposes_bridge_and_proof_tools(self) -> None:
        response = mcp_server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})

        assert response is not None
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertIn("bridge.health", names)
        self.assertIn("hermes.proof_mcp", names)
        self.assertIn("slice.export_preflight", names)
        self.assertIn("hermes.verify_evidence", names)

    def test_tool_call_dispatches_bridge_health_without_secrets(self) -> None:
        secret = "sk-test-secret-value-123456"
        with patch.dict(os.environ, {"OPENAI_API_KEY": secret}, clear=False):
            response = mcp_server.handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "bridge.health",
                        "arguments": {"workspace_root": str(ROOT)},
                    },
                }
            )

        assert response is not None
        result = response["result"]
        self.assertFalse(result["isError"])
        payload = result["structuredContent"]
        self.assertTrue(payload["workspace_scope_ok"])
        self.assertEqual(payload["result"]["status"], "ok")
        self.assertNotIn(secret, json.dumps(response))

    def test_mcp_sanitizer_redacts_secret_key_values(self) -> None:
        payload = mcp_server._tool_result({"api_key": "plain-secret-value", "secret_present": True})

        rendered = json.dumps(payload)
        self.assertNotIn("plain-secret-value", rendered)
        self.assertIn("<REDACTED>", rendered)
        self.assertTrue(payload["structuredContent"]["secret_present"])

    def test_tool_call_rejects_wrong_workspace_root(self) -> None:
        response = mcp_server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "bridge.health",
                    "arguments": {"workspace_root": "G:/Github/Hermes3D"},
                },
            }
        )

        assert response is not None
        result = response["result"]
        self.assertTrue(result["isError"])
        payload = result["structuredContent"]
        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["workspace_scope_ok"])
        self.assertEqual(Path(payload["expected_workspace_root"]), ROOT.resolve())

    def test_verify_evidence_is_testable_without_live_transport(self) -> None:
        response = mcp_server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "hermes.verify_evidence",
                    "arguments": {"workspace_root": str(ROOT)},
                },
            }
        )

        assert response is not None
        payload = response["result"]["structuredContent"]
        self.assertTrue(payload["proof_mcp"]["workspace_scope_ok"])
        self.assertIn(payload["status"], {"passed", "blocked"})
        self.assertIn("ledger", payload)

    def test_stdio_round_trip(self) -> None:
        stdin = io.StringIO(json.dumps({"jsonrpc": "2.0", "id": 6, "method": "tools/list"}) + "\n")
        stdout = io.StringIO()

        mcp_server.run_stdio(stdin=stdin, stdout=stdout)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["id"], 6)
        self.assertIn("tools", payload["result"])

    def test_module_self_test_exits_zero(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "hermes_slicer.mcp_server", "--test"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "passed")
        self.assertTrue(payload["workspace"]["workspace_scope_ok"])


if __name__ == "__main__":
    unittest.main()
