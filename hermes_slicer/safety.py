from __future__ import annotations

import time
from dataclasses import dataclass
from threading import RLock
from collections.abc import Callable
from typing import Any, Literal

from .printers import printer_targets


CAMERA_FRAME_FRESHNESS_SEC = 5.0
PLATE_CLEAR_FRESHNESS_SEC = 30.0
PLATE_CLEAR_MIN_CONFIDENCE = 0.85
PlateClassification = Literal["clear", "obstructed", "unknown"]


@dataclass(frozen=True)
class CameraFrameRecord:
    camera_id: str
    ts_unix: float


@dataclass(frozen=True)
class PlateClassificationRecord:
    camera_id: str
    classification: PlateClassification
    confidence: float
    ts_unix: float


@dataclass
class PrinterGateState:
    printer_id: str
    camera_id: str | None = None
    last_frame: CameraFrameRecord | None = None
    last_classification: PlateClassificationRecord | None = None


class PrinterSafetyGate:
    def __init__(
        self,
        *,
        camera_freshness_sec: float = CAMERA_FRAME_FRESHNESS_SEC,
        plate_freshness_sec: float = PLATE_CLEAR_FRESHNESS_SEC,
        plate_min_confidence: float = PLATE_CLEAR_MIN_CONFIDENCE,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._camera_freshness_sec = float(camera_freshness_sec)
        self._plate_freshness_sec = float(plate_freshness_sec)
        self._plate_min_confidence = float(plate_min_confidence)
        self._clock = clock or time.time
        self._lock = RLock()
        self._printers: dict[str, PrinterGateState] = {}
        self._camera_to_printers: dict[str, set[str]] = {}

    def bind_camera(self, printer_id: str, camera_id: str) -> None:
        printer_id = _non_empty(printer_id, "printer_id")
        camera_id = _non_empty(camera_id, "camera_id")
        with self._lock:
            state = self._printers.setdefault(printer_id, PrinterGateState(printer_id=printer_id))
            if state.camera_id and state.camera_id != camera_id:
                self._camera_to_printers.get(state.camera_id, set()).discard(printer_id)
            state.camera_id = camera_id
            self._camera_to_printers.setdefault(camera_id, set()).add(printer_id)

    def record_camera_frame(self, camera_id: str, ts_unix: float | None = None) -> None:
        camera_id = _non_empty(camera_id, "camera_id")
        timestamp = float(ts_unix if ts_unix is not None else self._clock())
        with self._lock:
            for printer_id in self._camera_to_printers.get(camera_id, set()):
                state = self._printers.setdefault(printer_id, PrinterGateState(printer_id=printer_id, camera_id=camera_id))
                if state.last_frame is None or timestamp >= state.last_frame.ts_unix:
                    state.last_frame = CameraFrameRecord(camera_id=camera_id, ts_unix=timestamp)

    def record_plate_classification(
        self,
        camera_id: str,
        classification: PlateClassification,
        confidence: float,
        ts_unix: float | None = None,
    ) -> None:
        camera_id = _non_empty(camera_id, "camera_id")
        if classification not in {"clear", "obstructed", "unknown"}:
            raise ValueError("classification must be clear, obstructed, or unknown")
        confidence = float(confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        timestamp = float(ts_unix if ts_unix is not None else self._clock())
        with self._lock:
            for printer_id in self._camera_to_printers.get(camera_id, set()):
                state = self._printers.setdefault(printer_id, PrinterGateState(printer_id=printer_id, camera_id=camera_id))
                previous = state.last_classification
                if previous is None or timestamp >= previous.ts_unix:
                    state.last_classification = PlateClassificationRecord(
                        camera_id=camera_id,
                        classification=classification,
                        confidence=confidence,
                        ts_unix=timestamp,
                    )

    def is_safe_to_start(self, printer_id: str) -> tuple[bool, list[str]]:
        printer_id = _non_empty(printer_id, "printer_id")
        with self._lock:
            now = self._clock()
            state = self._printers.get(printer_id)
            reasons: list[str] = []
            if state is None or not state.camera_id:
                reasons.append("no camera bound to printer")
            frame = state.last_frame if state else None
            if frame is None:
                reasons.append("no camera frame ever")
            elif now - frame.ts_unix > self._camera_freshness_sec:
                reasons.append(
                    f"camera stale: last frame {now - frame.ts_unix:.1f}s ago "
                    f"(freshness window {self._camera_freshness_sec:.1f}s)"
                )
            plate = state.last_classification if state else None
            if plate is None:
                reasons.append("no plate classification ever")
            else:
                age = now - plate.ts_unix
                if age > self._plate_freshness_sec:
                    reasons.append(
                        f"plate classification stale: {age:.1f}s ago "
                        f"(freshness window {self._plate_freshness_sec:.1f}s)"
                    )
                elif plate.classification != "clear":
                    reasons.append(f"plate not clear: classifier says '{plate.classification}' (confidence {plate.confidence:.2f})")
                elif plate.confidence < self._plate_min_confidence:
                    reasons.append(
                        f"plate-clear confidence too low: {plate.confidence:.2f} "
                        f"(min {self._plate_min_confidence:.2f})"
                    )
            return not reasons, reasons

    def safety_state(self, printer_id: str) -> dict[str, Any]:
        printer_id = _non_empty(printer_id, "printer_id")
        with self._lock:
            now = self._clock()
            state = self._printers.get(printer_id)
            frame = state.last_frame if state else None
            plate = state.last_classification if state else None
            allow, reasons = self.is_safe_to_start(printer_id)
            return {
                "printer_id": printer_id,
                "status": "passed" if allow else "blocked",
                "safe_to_start": allow,
                "blocked_by": reasons,
                "camera_id": state.camera_id if state else None,
                "camera_fresh": bool(frame and now - frame.ts_unix <= self._camera_freshness_sec),
                "camera_age_sec": round(now - frame.ts_unix, 3) if frame else None,
                "plate_classification": plate.classification if plate else None,
                "plate_confidence": plate.confidence if plate else None,
                "plate_age_sec": round(now - plate.ts_unix, 3) if plate else None,
                "thresholds": {
                    "camera_freshness_sec": self._camera_freshness_sec,
                    "plate_freshness_sec": self._plate_freshness_sec,
                    "plate_min_confidence": self._plate_min_confidence,
                },
                "v1_enforcement": v1_enforcement_payload(),
            }


_DEFAULT_GATE = PrinterSafetyGate()


def reset_default_gate() -> None:
    global _DEFAULT_GATE
    _DEFAULT_GATE = PrinterSafetyGate()


def default_gate() -> PrinterSafetyGate:
    return _DEFAULT_GATE


def safety_state(body: dict[str, Any] | None = None, gate: PrinterSafetyGate | None = None) -> dict[str, Any]:
    body = body or {}
    gate = gate or default_gate()
    target_ids = _target_ids(body)
    states = [gate.safety_state(target_id) for target_id in target_ids]
    safe = bool(states) and all(item["safe_to_start"] for item in states)
    return {
        "status": "passed" if safe else "blocked",
        "generated_at": _iso_like_now(),
        "targets": states,
        "safety": v1_enforcement_payload(),
    }


def record_camera_frame_event(body: dict[str, Any], gate: PrinterSafetyGate | None = None) -> dict[str, Any]:
    gate = gate or default_gate()
    target_id = _known_target_id(body)
    camera_id = str(body.get("camera_id") or target_id).strip()
    ts_unix = _optional_float(body.get("ts_unix"))
    gate.bind_camera(target_id, camera_id)
    gate.record_camera_frame(camera_id, ts_unix)
    state = gate.safety_state(target_id)
    return {
        "status": state["status"],
        "event": "camera_frame",
        "target_id": target_id,
        "camera_id": camera_id,
        "state": state,
        "safety": v1_enforcement_payload(),
    }


def record_plate_classification_event(body: dict[str, Any], gate: PrinterSafetyGate | None = None) -> dict[str, Any]:
    gate = gate or default_gate()
    target_id = _known_target_id(body)
    camera_id = str(body.get("camera_id") or target_id).strip()
    classification = str(body.get("classification", "unknown")).strip().lower()
    confidence = _required_float(body.get("confidence"), "confidence")
    ts_unix = _optional_float(body.get("ts_unix"))
    gate.bind_camera(target_id, camera_id)
    gate.record_plate_classification(camera_id, classification, confidence, ts_unix)  # type: ignore[arg-type]
    state = gate.safety_state(target_id)
    return {
        "status": state["status"],
        "event": "plate_classification",
        "target_id": target_id,
        "camera_id": camera_id,
        "classification": classification,
        "confidence": confidence,
        "state": state,
        "safety": v1_enforcement_payload(),
    }


def hard_stop_proof(body: dict[str, Any] | None = None, gate: PrinterSafetyGate | None = None) -> dict[str, Any]:
    body = body or {}
    gate = gate or default_gate()
    target_id = _known_target_id(body) if body.get("target_id") else _target_ids({})[0]
    reason = str(body.get("reason") or "Printer safety gate is default-deny until fresh camera and plate-clear proof exist.").strip()
    state = gate.safety_state(target_id)
    blocked_by = state["blocked_by"] or ["V1 blocks printer upload, start, heaters, motion, and raw G-code commands."]
    return {
        "status": "blocked",
        "alert_level": "hard_stop",
        "target_id": target_id,
        "reason": reason,
        "message": "STOP - Heaters stay off. Resolve the safety gate before any future print dispatch.",
        "state": state,
        "blocked_by": blocked_by,
        "safety": v1_enforcement_payload(),
    }


def v1_enforcement_payload() -> dict[str, Any]:
    return {
        "mode": "default_deny_proof_only",
        "upload_gcode": "blocked_in_v1",
        "start_print": "blocked_in_v1",
        "heater_or_motion_commands": "not_implemented",
        "raw_gcode": "not_implemented",
        "real_emergency_stop_transport": "blocked_in_v1",
        "allowed_probe_methods": ["GET", "proof-only local events"],
    }


def _target_ids(body: dict[str, Any]) -> list[str]:
    requested = str(body.get("target_id", "")).strip()
    targets = printer_targets().get("targets", [])
    ids = [str(target.get("id")) for target in targets if isinstance(target, dict) and target.get("id")]
    if requested:
        if requested not in ids:
            raise ValueError(f"unknown printer target_id: {requested}")
        return [requested]
    return ids or ["unconfigured-printer"]


def _known_target_id(body: dict[str, Any]) -> str:
    return _target_ids(body)[0]


def _non_empty(value: str, name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


def _required_float(value: Any, name: str) -> float:
    if value is None:
        raise ValueError(f"{name} is required")
    return float(value)


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _iso_like_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
