from __future__ import annotations

import os
import json
import subprocess
from pathlib import Path
from typing import Any

from .config import SAMPLES_DIR, allowed_model_roots, allowed_output_roots, default_slice_request, discover_executables, discover_orca_profile_roots
from .security import is_private_path, sanitize_text


class ValidationError(ValueError):
    pass


def _resolve(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def _within(path: Path, roots: list[Path]) -> bool:
    normalized = os.path.normcase(str(path))
    for root in roots:
        root_path = _resolve(root)
        root_normalized = os.path.normcase(str(root_path))
        if normalized == root_normalized or normalized.startswith(root_normalized + os.sep):
            return True
    return False


def validate_slice_request(payload: dict[str, Any] | None) -> dict[str, Any]:
    request = default_slice_request()
    if payload:
        request.update(payload)

    model_path = _resolve(request["model_path"])
    output_dir = _resolve(request["output_dir"])

    if is_private_path(model_path) or is_private_path(output_dir):
        raise ValidationError("Private paths are not allowed for model or output locations.")
    if not _within(model_path, allowed_model_roots()):
        raise ValidationError("Model path is outside configured allowed model roots.")
    if not _within(output_dir, allowed_output_roots()):
        raise ValidationError("Output directory is outside configured allowed output roots.")
    if request.get("confirm_print") is True:
        raise ValidationError("Printing is not allowed through V1 slice endpoints.")
    if not model_path.exists():
        raise ValidationError("Model path does not exist.")

    return {
        "model_path": str(model_path),
        "printer_profile": str(request.get("printer_profile", "")),
        "material_profile": str(request.get("material_profile", "")),
        "quality_profile": str(request.get("quality_profile", "")),
        "output_dir": str(output_dir),
        "confirm_print": False,
    }


def run_command(args: list[str], timeout: int = 15) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False,
        )
        return {
            "returncode": completed.returncode,
            "stdout": sanitize_text(completed.stdout),
            "stderr": sanitize_text(completed.stderr),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "returncode": None,
            "stdout": sanitize_text(exc.stdout or ""),
            "stderr": sanitize_text(exc.stderr or ""),
            "timed_out": True,
        }


def orca_version_check() -> dict[str, Any]:
    executables = discover_executables()
    orca = executables.get("orca")
    if not orca:
        return {"status": "blocked", "reason": "OrcaSlicer executable not found.", "attempts": []}

    attempts = []
    commands = [
        ["--version"],
        ["--help"],
        ["--info", str(SAMPLES_DIR / "test_cube.stl")],
    ]
    for command in commands:
        result = run_command([orca, *command], timeout=15)
        display_args = [Path(orca).name, *["<SAMPLE_STL>" if arg.endswith("test_cube.stl") else arg for arg in command]]
        attempts.append({"args": display_args, **result})
    has_successful_probe = any(
        attempt["returncode"] == 0 and str(attempt.get("stdout", "")).strip()
        for attempt in attempts
    )
    return {
        "status": "passed" if has_successful_probe else "warning",
        "executable": sanitize_text(orca),
        "attempts": attempts,
    }


def list_orca_profiles() -> dict[str, Any]:
    roots = []
    vendors = []
    for root in discover_orca_profile_roots():
        if not root.exists():
            roots.append({"path": sanitize_text(root), "exists": False, "vendors": 0})
            continue
        names = sorted(path.name for path in root.iterdir() if path.is_dir() or path.suffix.lower() in {".json", ".ini"})
        roots.append({"path": sanitize_text(root), "exists": True, "vendors": len(names)})
        vendors.extend(names[:200])
    return {
        "status": "passed" if roots else "blocked",
        "roots": roots,
        "vendor_count": len(set(vendors)),
        "vendors": sorted(set(vendors)),
    }


def flsun_profile_inventory(targets: tuple[str, ...] = ("FLSun T1", "FLSun V400", "FLSun S1")) -> dict[str, Any]:
    for profile_root in discover_orca_profile_roots():
        manifest_path = profile_root / "FLSun.json"
        vendor_dir = profile_root / "FLSun"
        if not manifest_path.exists() or not vendor_dir.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8", errors="ignore"))
        machines = manifest.get("machine_model_list", [])
        machine_presets = manifest.get("machine_list", [])
        processes = manifest.get("process_list", [])
        filaments = manifest.get("filament_list", [])
        inventory = []
        for target in targets:
            model_entry = _find_named(machines, target)
            model_details = _read_profile_json(vendor_dir / model_entry.get("sub_path", "")) if model_entry else {}
            default_materials = _split_profile_list(model_details.get("default_materials", ""))
            matching_machine_presets = _entries_matching(machine_presets, target)
            matching_processes = _entries_matching(processes, f"@{target}")
            matching_filaments = _entries_matching(filaments, target)
            nozzle_defaults = []
            for preset in matching_machine_presets:
                details = _read_profile_json(vendor_dir / preset.get("sub_path", ""))
                if details.get("default_print_profile"):
                    nozzle_defaults.append(
                        {
                            "machine": preset["name"],
                            "default_print_profile": details["default_print_profile"],
                        }
                    )
            inventory.append(
                {
                    "model": target,
                    "model_present": bool(model_entry),
                    "model_file": model_entry.get("sub_path") if model_entry else None,
                    "model_id": model_details.get("model_id"),
                    "default_materials": default_materials,
                    "machine_presets": matching_machine_presets,
                    "process_presets": matching_processes,
                    "filament_presets": matching_filaments,
                    "nozzle_defaults": nozzle_defaults,
                }
            )
        return {
            "status": "passed",
            "source": sanitize_text(manifest_path),
            "version": manifest.get("version"),
            "targets": inventory,
        }
    return {"status": "blocked", "reason": "Local Orca FLSun profile manifest not found.", "targets": []}


def _find_named(entries: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    return next((entry for entry in entries if entry.get("name") == name), None)


def _entries_matching(entries: list[dict[str, Any]], needle: str) -> list[dict[str, str]]:
    return [
        {"name": str(entry.get("name", "")), "sub_path": str(entry.get("sub_path", ""))}
        for entry in entries
        if needle.lower() in str(entry.get("name", "")).lower()
    ]


def _read_profile_json(path: Path) -> dict[str, Any]:
    if not path.exists() or path.suffix.lower() != ".json":
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return {}


def _split_profile_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [part.strip() for part in value.split(";") if part.strip()]
    if isinstance(value, list):
        return [str(part) for part in value]
    return []


def dry_run_slice(payload: dict[str, Any] | None) -> dict[str, Any]:
    request = validate_slice_request(payload)
    executables = discover_executables()
    return {
        "status": "passed",
        "request": request,
        "slicer_available": bool(executables.get("orca") or executables.get("prusa")),
        "would_execute": False,
    }


def export_gcode(payload: dict[str, Any] | None) -> dict[str, Any]:
    if os.environ.get("HERMES_ENABLE_EXPORT_GCODE") != "1":
        return {
            "status": "blocked",
            "reason": "G-code export is disabled by default. Set HERMES_ENABLE_EXPORT_GCODE=1 after reviewing the profile path.",
        }
    request = validate_slice_request(payload)
    executables = discover_executables()
    slicer = executables.get("orca") or executables.get("prusa")
    if not slicer:
        return {"status": "blocked", "reason": "No supported slicer executable found."}
    output_dir = Path(request["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / (Path(request["model_path"]).stem + ".gcode")
    args = [slicer, "--export-gcode", request["model_path"], "--output", str(output_file)]
    result = run_command(args, timeout=120)
    return {"status": "passed" if result["returncode"] == 0 else "failed", "args": [Path(slicer).name, "--export-gcode", "<MODEL>", "--output", "<OUTPUT>"], "result": result}
