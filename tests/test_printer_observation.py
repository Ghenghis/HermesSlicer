from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hermes_slicer.bridge import dispatch_action, hermes_agent_tool_request
from hermes_slicer.printers import load_printer_config, observe_printers, probe_printer_target


class FakeHttpResponse:
    def __init__(self, body: bytes, status: int = 200, content_type: str = "application/json") -> None:
        self._body = body
        self.status = status
        self.headers = {"Content-Type": content_type}

    def read(self, _size: int = -1) -> bytes:
        return self._body

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class PrinterObservationTests(unittest.TestCase):
    def test_load_printer_config_contains_user_t1_targets(self) -> None:
        config = load_printer_config()
        hosts = {target["host"] for target in config["targets"]}

        self.assertIn("192.168.0.10", hosts)
        self.assertIn("192.168.0.11", hosts)
        self.assertFalse(config["enable_printer_upload"])
        self.assertFalse(config["enable_print_start"])

    def test_probe_rejects_public_ip_targets(self) -> None:
        result = probe_printer_target({"id": "bad", "name": "Bad", "host": "8.8.8.8"})

        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["local_network_gate"]["passed"])
        self.assertEqual(result["safety"]["start_print"], "not_attempted")

    def test_probe_detects_moonraker_and_web_ui_without_write_actions(self) -> None:
        def fake_urlopen(request: object, timeout: float) -> FakeHttpResponse:
            url = request.full_url  # type: ignore[attr-defined]
            if url.endswith(":7125/server/info"):
                return FakeHttpResponse(b'{"moonraker_version":"v0.9","klippy_state":"ready"}')
            if url.endswith("/api/version"):
                return FakeHttpResponse(b"{}", status=404, content_type="application/json")
            if "snapshot" in url:
                return FakeHttpResponse(b"\xff\xd8", content_type="image/jpeg")
            return FakeHttpResponse(b"<html><title>Mainsail</title></html>", content_type="text/html")

        with patch("hermes_slicer.printers.urlopen", side_effect=fake_urlopen):
            result = probe_printer_target({"id": "flsun_t1_1", "name": "FLSUN T1 #1", "host": "192.168.0.10"})

        self.assertEqual(result["status"], "passed")
        self.assertIn("mainsail", result["detected_interfaces"])
        self.assertIn("moonraker", result["detected_interfaces"])
        self.assertIn("camera", result["detected_interfaces"])
        self.assertEqual(result["safety"]["upload_gcode"], "not_attempted")
        self.assertEqual(result["safety"]["heater_or_motion_commands"], "not_implemented")

    def test_observe_unknown_target_fails_without_network_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "printers.json"
            path.write_text(
                json.dumps({"targets": [{"id": "known", "name": "Known", "host": "192.168.0.10"}]}),
                encoding="utf-8",
            )

            result = observe_printers({"target_id": "missing"}, config_path=path)

        self.assertEqual(result["status"], "failed")
        self.assertIn("known", result["known_targets"])

    def test_bridge_dispatch_exposes_read_only_printer_actions(self) -> None:
        with patch("hermes_slicer.bridge.observe_printers", return_value={"status": "blocked", "targets": [], "safety": {"mode": "read_only_observation"}}):
            payload, status = dispatch_action({"action": "printer.observe", "payload": {}})

        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "blocked")

    def test_hermes_agent_routes_camera_requests_to_printer_observation(self) -> None:
        with patch("hermes_slicer.bridge.observe_printers", return_value={"status": "passed", "targets": [], "safety": {"mode": "read_only_observation"}}):
            payload = hermes_agent_tool_request({"message": "check the printer cameras"})

        self.assertEqual(payload["resolved_action"], "printer.observe")
        self.assertIn("Uploads and print starts remain blocked", payload["reply"])


if __name__ == "__main__":
    unittest.main()
