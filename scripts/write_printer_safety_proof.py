from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.proof import log_event, write_json  # noqa: E402
from hermes_slicer.safety import PrinterSafetyGate, hard_stop_proof, record_camera_frame_event, record_plate_classification_event, safety_state  # noqa: E402


class FixedClock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def build_report() -> dict[str, object]:
    clock = FixedClock()
    gate = PrinterSafetyGate(clock=clock)
    target_id = "flsun_t1_1"
    default_state = safety_state({"target_id": target_id}, gate)
    camera_event = record_camera_frame_event({"target_id": target_id, "camera_id": "proof-camera", "ts_unix": clock.now}, gate)
    clear_event = record_plate_classification_event(
        {
            "target_id": target_id,
            "camera_id": "proof-camera",
            "classification": "clear",
            "confidence": 0.99,
            "ts_unix": clock.now,
        },
        gate,
    )
    hard_stop = hard_stop_proof({"target_id": target_id, "reason": "V1 proof run: printer commands remain blocked."}, gate)
    obstruction_gate = PrinterSafetyGate(clock=clock)
    record_camera_frame_event({"target_id": target_id, "camera_id": "proof-camera", "ts_unix": clock.now}, obstruction_gate)
    obstruction_event = record_plate_classification_event(
        {
            "target_id": target_id,
            "camera_id": "proof-camera",
            "classification": "obstructed",
            "confidence": 0.99,
            "ts_unix": clock.now,
        },
        obstruction_gate,
    )
    checks = {
        "default_blocks": default_state["status"] == "blocked",
        "clear_gate_can_identify_safe_plate": clear_event["state"]["safe_to_start"] is True,
        "obstruction_blocks": obstruction_event["state"]["safe_to_start"] is False,
        "hard_stop_blocks_commands": hard_stop["status"] == "blocked"
        and hard_stop["safety"]["start_print"] == "blocked_in_v1"
        and hard_stop["safety"]["heater_or_motion_commands"] == "not_implemented",
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_pattern": "G:/Github/Hermes3D/03_implementation/src/hermes3d/services/printer_safety_gate.py",
        "target_id": target_id,
        "checks": checks,
        "default_state": default_state,
        "camera_event": camera_event,
        "clear_event": clear_event,
        "obstruction_event": obstruction_event,
        "hard_stop": hard_stop,
        "v1_boundary": hard_stop["safety"],
    }


def main() -> int:
    report = build_report()
    write_json(ROOT / "proof" / "runtime" / "printer-safety-gate.json", report)
    log_event(
        "proof",
        "printer.safety_gate",
        report["status"],
        outputs={"status": report["status"], "checks": report["checks"]},
        proof_files=["proof/runtime/printer-safety-gate.json"],
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
