from __future__ import annotations

import threading
import unittest

from hermes_slicer.safety import (
    PLATE_CLEAR_MIN_CONFIDENCE,
    PrinterSafetyGate,
    hard_stop_proof,
    record_camera_frame_event,
    record_plate_classification_event,
    safety_state,
)


class Clock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


class SafetyGateTests(unittest.TestCase):
    def test_default_deny_without_camera_or_plate_proof(self) -> None:
        gate = PrinterSafetyGate(clock=Clock())

        allow, reasons = gate.is_safe_to_start("flsun_t1_1")

        self.assertFalse(allow)
        self.assertIn("no camera bound to printer", reasons)
        self.assertIn("no camera frame ever", reasons)
        self.assertIn("no plate classification ever", reasons)

    def test_camera_frame_without_plate_clear_stays_blocked(self) -> None:
        clock = Clock()
        gate = PrinterSafetyGate(clock=clock)
        gate.bind_camera("flsun_t1_1", "cam-a")
        gate.record_camera_frame("cam-a")

        state = gate.safety_state("flsun_t1_1")

        self.assertFalse(state["safe_to_start"])
        self.assertTrue(state["camera_fresh"])
        self.assertIn("no plate classification ever", state["blocked_by"])

    def test_clear_plate_with_confidence_passes_gate(self) -> None:
        clock = Clock()
        gate = PrinterSafetyGate(clock=clock)
        gate.bind_camera("flsun_t1_1", "cam-a")
        gate.record_camera_frame("cam-a")
        gate.record_plate_classification("cam-a", "clear", PLATE_CLEAR_MIN_CONFIDENCE)

        state = gate.safety_state("flsun_t1_1")

        self.assertTrue(state["safe_to_start"])
        self.assertEqual(state["blocked_by"], [])

    def test_obstructed_low_confidence_or_stale_input_blocks(self) -> None:
        clock = Clock()
        gate = PrinterSafetyGate(clock=clock)
        gate.bind_camera("flsun_t1_1", "cam-a")
        gate.record_camera_frame("cam-a")
        gate.record_plate_classification("cam-a", "obstructed", 0.99)
        self.assertFalse(gate.safety_state("flsun_t1_1")["safe_to_start"])

        gate.record_plate_classification("cam-a", "clear", 0.2, ts_unix=clock.now + 1)
        self.assertFalse(gate.safety_state("flsun_t1_1")["safe_to_start"])

        gate.record_plate_classification("cam-a", "clear", 0.99, ts_unix=clock.now + 2)
        clock.now += 40
        state = gate.safety_state("flsun_t1_1")
        self.assertFalse(state["safe_to_start"])
        self.assertTrue(any("camera stale" in reason or "plate classification stale" in reason for reason in state["blocked_by"]))

    def test_bridge_payloads_are_proof_only_and_do_not_enable_printing(self) -> None:
        clock = Clock()
        gate = PrinterSafetyGate(clock=clock)
        frame = record_camera_frame_event({"target_id": "flsun_t1_1", "camera_id": "cam-a"}, gate)
        plate = record_plate_classification_event(
            {"target_id": "flsun_t1_1", "camera_id": "cam-a", "classification": "clear", "confidence": 0.99},
            gate,
        )
        hard_stop = hard_stop_proof({"target_id": "flsun_t1_1"}, gate)

        self.assertEqual(frame["safety"]["start_print"], "blocked_in_v1")
        self.assertEqual(plate["safety"]["heater_or_motion_commands"], "not_implemented")
        self.assertEqual(hard_stop["status"], "blocked")
        self.assertEqual(hard_stop["alert_level"], "hard_stop")

    def test_safety_state_action_accepts_injected_gate(self) -> None:
        gate = PrinterSafetyGate(clock=Clock())
        payload = safety_state({"target_id": "flsun_t1_1"}, gate)

        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["targets"][0]["printer_id"], "flsun_t1_1")

    def test_concurrent_events_do_not_leak_between_printers(self) -> None:
        gate = PrinterSafetyGate(clock=Clock())

        def bind_and_record(printer_id: str, camera_id: str) -> None:
            gate.bind_camera(printer_id, camera_id)
            gate.record_camera_frame(camera_id)
            gate.record_plate_classification(camera_id, "clear", 0.99)

        threads = [
            threading.Thread(target=bind_and_record, args=("flsun_t1_1", "cam-a")),
            threading.Thread(target=bind_and_record, args=("flsun_t1_2", "cam-b")),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertTrue(gate.safety_state("flsun_t1_1")["safe_to_start"])
        self.assertTrue(gate.safety_state("flsun_t1_2")["safe_to_start"])
        self.assertEqual(gate.safety_state("flsun_t1_1")["camera_id"], "cam-a")
        self.assertEqual(gate.safety_state("flsun_t1_2")["camera_id"], "cam-b")


if __name__ == "__main__":
    unittest.main()
