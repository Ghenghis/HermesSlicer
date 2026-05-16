from __future__ import annotations

import os
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable

from .config import SAMPLES_DIR, allowed_model_roots, allowed_output_roots, default_slice_request, discover_executables, discover_orca_profile_roots
from .security import is_private_path, sanitize_text


class ValidationError(ValueError):
    pass


FLSUN_TARGETS = ("FLSun T1", "FLSun V400", "FLSun S1")
FLSUN_PROFILE_LISTS = {
    "machine_model": "machine_model_list",
    "machine": "machine_list",
    "process": "process_list",
    "filament": "filament_list",
}
FLSUN_MODEL_ALIASES = {
    "t1": "FLSun T1",
    "flsunt1": "FLSun T1",
    "flsunt1safedefault": "FLSun T1",
    "v400": "FLSun V400",
    "flsunv400": "FLSun V400",
    "flsunv400safedefault": "FLSun V400",
    "s1": "FLSun S1",
    "flsuns1": "FLSun S1",
    "flsuns1safedefault": "FLSun S1",
}


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


def flsun_profile_inventory(
    targets: tuple[str, ...] = FLSUN_TARGETS,
    profile_roots: Iterable[Path] | None = None,
) -> dict[str, Any]:
    bundle = _load_flsun_bundle(profile_roots)
    if not bundle:
        return {"status": "blocked", "reason": "Local Orca FLSun profile manifest not found.", "targets": []}

    manifest = bundle["manifest"]
    machines = manifest.get("machine_model_list", [])
    machine_presets = manifest.get("machine_list", [])
    processes = manifest.get("process_list", [])
    filaments = manifest.get("filament_list", [])
    inventory = []
    for target in targets:
        model_entry = _find_named(machines, target)
        model_details = _read_manifest_profile(bundle, model_entry) if model_entry else {}
        default_materials = _split_profile_list(model_details.get("default_materials", ""))
        matching_machine_presets = _entries_matching(machine_presets, target)
        matching_processes = _entries_matching(processes, f"@{target}")
        matching_filaments = _entries_matching(filaments, target)
        default_filaments = [
            _entry_summary(bundle["entries"].get(material))
            for material in default_materials
            if bundle["entries"].get(material)
        ]
        nozzle_defaults = []
        for preset in matching_machine_presets:
            entry = bundle["entries"].get(preset["name"])
            details = _read_manifest_profile(bundle, entry) if entry else {}
            if details.get("default_print_profile"):
                nozzle_defaults.append(
                    {
                        "machine": preset["name"],
                        "default_print_profile": details["default_print_profile"],
                    }
                )
        default_preflight = _build_flsun_preflight(
            {
                "printer_profile": target,
                "material_profile": "PLA_safe_default",
                "quality_profile": "0.20mm_standard",
            },
            profile_roots=[bundle["profile_root"]],
            validate_paths=False,
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
                "default_filament_presets": default_filaments,
                "nozzle_defaults": nozzle_defaults,
                "default_preflight": _public_preflight(default_preflight),
            }
        )
    return {
        "status": "passed",
        "source": sanitize_text(bundle["manifest_path"]),
        "version": manifest.get("version"),
        "targets": inventory,
    }


def flsun_export_preflight(
    payload: dict[str, Any] | None,
    profile_roots: Iterable[Path] | None = None,
) -> dict[str, Any]:
    return _public_preflight(_build_flsun_preflight(payload, profile_roots=profile_roots))


def _build_flsun_preflight(
    payload: dict[str, Any] | None,
    profile_roots: Iterable[Path] | None = None,
    validate_paths: bool = True,
) -> dict[str, Any]:
    request = validate_slice_request(payload) if validate_paths else _preview_slice_request(payload)
    bundle = _load_flsun_bundle(profile_roots)
    if not bundle:
        return {
            "status": "blocked",
            "reason": "Local Orca FLSun profile manifest not found.",
            "request": request,
        }

    try:
        resolved = _resolve_flsun_selection(bundle, request)
    except ValidationError as exc:
        return {
            "status": "blocked",
            "reason": str(exc),
            "source": sanitize_text(bundle["manifest_path"]),
            "version": bundle["manifest"].get("version"),
            "request": request,
        }

    machine_name = resolved["machine"]["name"]
    process_compatible = machine_name in _split_profile_list(resolved["process"]["config"].get("compatible_printers", []))
    filament_compatible = machine_name in _split_profile_list(resolved["filament"]["config"].get("compatible_printers", []))
    errors = []
    if not process_compatible:
        errors.append("Process preset is not compatible with selected machine preset.")
    if not filament_compatible:
        errors.append("Filament preset is not compatible with selected machine preset.")

    status = "passed" if not errors else "blocked"
    profile_args = {
        "load_settings": [resolved["machine"]["sub_path"], resolved["process"]["sub_path"]],
        "load_filaments": [resolved["filament"]["sub_path"]],
    }
    return {
        "status": status,
        "reason": "; ".join(errors) if errors else "FLSUN machine/process/filament tuple is compatible.",
        "source": sanitize_text(bundle["manifest_path"]),
        "version": bundle["manifest"].get("version"),
        "request": request,
        "resolved": {
            "model": resolved["model"],
            "model_id": resolved["model_config"].get("model_id"),
            "default_materials": resolved["default_materials"],
            "machine": _resolved_profile_summary(resolved["machine"]),
            "process": _resolved_profile_summary(resolved["process"]),
            "filament": _resolved_profile_summary(resolved["filament"]),
        },
        "compatibility": {
            "machine": machine_name,
            "process": process_compatible,
            "filament": filament_compatible,
            "errors": errors,
        },
        "cli": {
            "profile_args": profile_args,
            "args_preview": [
                "<SLICER>",
                "--load_settings",
                "<MACHINE_PROFILE>;<PROCESS_PROFILE>",
                "--load_filaments",
                "<FILAMENT_PROFILE>",
                "--slice",
                "0",
                "--outputdir",
                "<OUTPUT_DIR>",
                "<MODEL>",
            ],
        },
        "_internal": {
            "machine_path": resolved["machine"]["path"],
            "process_path": resolved["process"]["path"],
            "filament_path": resolved["filament"]["path"],
        },
    }


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


def _public_preflight(preflight: dict[str, Any]) -> dict[str, Any]:
    public = dict(preflight)
    public.pop("_internal", None)
    return public


def _preview_slice_request(payload: dict[str, Any] | None) -> dict[str, Any]:
    request = default_slice_request()
    if payload:
        request.update(payload)
    return {
        "model_path": str(request.get("model_path", "")),
        "printer_profile": str(request.get("printer_profile", "")),
        "material_profile": str(request.get("material_profile", "")),
        "quality_profile": str(request.get("quality_profile", "")),
        "output_dir": str(request.get("output_dir", "")),
        "confirm_print": False,
    }


def _load_flsun_bundle(profile_roots: Iterable[Path] | None = None) -> dict[str, Any] | None:
    roots = list(profile_roots) if profile_roots is not None else discover_orca_profile_roots()
    for profile_root in roots:
        root = Path(profile_root)
        manifest_path = root / "FLSun.json"
        vendor_dir = root / "FLSun"
        if not manifest_path.exists() or not vendor_dir.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8", errors="ignore"))
        except json.JSONDecodeError:
            continue
        entries: dict[str, dict[str, Any]] = {}
        for kind, list_key in FLSUN_PROFILE_LISTS.items():
            for entry in manifest.get(list_key, []):
                if entry.get("name"):
                    enriched = dict(entry)
                    enriched["kind"] = kind
                    entries[str(entry["name"])] = enriched
        return {
            "profile_root": root,
            "manifest_path": manifest_path,
            "vendor_dir": vendor_dir,
            "manifest": manifest,
            "entries": entries,
        }
    return None


def _resolve_flsun_selection(bundle: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    machine = _resolve_machine_profile(bundle, request.get("printer_profile", ""))
    model = str(machine["config"].get("printer_model") or _infer_model_from_machine(machine["name"]))
    model_profile = _resolve_profile(bundle, model, "machine_model")
    default_materials = _split_profile_list(model_profile["config"].get("default_materials", ""))
    process = _resolve_process_profile(bundle, request.get("quality_profile", ""), machine, model)
    filament = _resolve_filament_profile(bundle, request.get("material_profile", ""), default_materials)
    return {
        "model": model,
        "model_config": model_profile["config"],
        "default_materials": default_materials,
        "machine": machine,
        "process": process,
        "filament": filament,
    }


def _resolve_machine_profile(bundle: dict[str, Any], requested: Any) -> dict[str, Any]:
    requested_name = str(requested or "").strip()
    if requested_name in bundle["entries"] and bundle["entries"][requested_name].get("kind") == "machine":
        return _resolve_profile(bundle, requested_name, "machine")
    model = _normalize_flsun_model(requested_name)
    if not model:
        raise ValidationError(f"Unsupported FLSUN printer profile: {requested_name or '<empty>'}.")
    machine_name = f"{model} 0.4 nozzle"
    return _resolve_profile(bundle, machine_name, "machine")


def _resolve_process_profile(bundle: dict[str, Any], requested: Any, machine: dict[str, Any], model: str) -> dict[str, Any]:
    requested_name = str(requested or "").strip()
    if requested_name in bundle["entries"] and bundle["entries"][requested_name].get("kind") == "process":
        return _resolve_profile(bundle, requested_name, "process")
    default_process = str(machine["config"].get("default_print_profile", "")).strip()
    quality_label = _normalize_quality_label(requested_name)
    if quality_label:
        candidate = f"{quality_label} @{model}"
        if candidate in bundle["entries"]:
            return _resolve_profile(bundle, candidate, "process")
    if default_process:
        return _resolve_profile(bundle, default_process, "process")
    raise ValidationError(f"No process preset found for {machine['name']}.")


def _resolve_filament_profile(
    bundle: dict[str, Any],
    requested: Any,
    default_materials: list[str],
) -> dict[str, Any]:
    requested_name = str(requested or "").strip()
    if requested_name in bundle["entries"] and bundle["entries"][requested_name].get("kind") == "filament":
        return _resolve_profile(bundle, requested_name, "filament")
    material_kind = _normalize_material_kind(requested_name)
    candidate = _pick_default_material(default_materials, material_kind)
    if candidate:
        return _resolve_profile(bundle, candidate, "filament")
    raise ValidationError(f"No filament preset found for material request: {requested_name or '<empty>'}.")


def _resolve_profile(
    bundle: dict[str, Any],
    name: str,
    expected_kind: str,
    visited: tuple[str, ...] = (),
) -> dict[str, Any]:
    if name in visited:
        raise ValidationError(f"Cyclic FLSUN profile inheritance detected at {name}.")
    entry = bundle["entries"].get(name)
    if not entry or entry.get("kind") != expected_kind:
        raise ValidationError(f"FLSUN {expected_kind} profile not found: {name}.")
    path = _safe_vendor_profile_path(bundle["vendor_dir"], str(entry.get("sub_path", "")))
    config = _read_profile_json(path)
    if not config:
        raise ValidationError(f"FLSUN profile file could not be read: {entry.get('sub_path')}.")
    inherited: dict[str, Any] = {}
    inheritance_chain: list[str] = []
    for parent_name in _split_profile_list(config.get("inherits", "")):
        parent = _resolve_profile(bundle, parent_name, expected_kind, (*visited, name))
        inherited.update(parent["config"])
        inheritance_chain.extend(parent["inheritance"])
        inheritance_chain.append(parent["name"])
    merged = dict(inherited)
    merged.update(config)
    return {
        "name": str(config.get("name") or name),
        "kind": expected_kind,
        "sub_path": str(entry.get("sub_path", "")),
        "path": path,
        "config": merged,
        "inheritance": inheritance_chain,
    }


def _read_manifest_profile(bundle: dict[str, Any], entry: dict[str, Any] | None) -> dict[str, Any]:
    if not entry:
        return {}
    return _read_profile_json(_safe_vendor_profile_path(bundle["vendor_dir"], str(entry.get("sub_path", ""))))


def _safe_vendor_profile_path(vendor_dir: Path, sub_path: str) -> Path:
    candidate = (vendor_dir / sub_path).resolve()
    vendor_root = vendor_dir.resolve()
    if not _within(candidate, [vendor_root]):
        raise ValidationError("FLSUN profile manifest points outside the vendor profile folder.")
    return candidate


def _entry_summary(entry: dict[str, Any] | None) -> dict[str, str] | None:
    if not entry:
        return None
    return {"name": str(entry.get("name", "")), "sub_path": str(entry.get("sub_path", ""))}


def _resolved_profile_summary(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": profile["name"],
        "kind": profile["kind"],
        "sub_path": profile["sub_path"],
        "inherits": profile["inheritance"],
        "resolved_key_count": len(profile["config"]),
    }


def _normalize_key(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _normalize_flsun_model(value: str) -> str | None:
    key = _normalize_key(value)
    if key in FLSUN_MODEL_ALIASES:
        return FLSUN_MODEL_ALIASES[key]
    for marker, model in (("v400", "FLSun V400"), ("t1", "FLSun T1"), ("s1", "FLSun S1")):
        if marker in key:
            return model
    return None


def _infer_model_from_machine(machine_name: str) -> str:
    for model in FLSUN_TARGETS:
        if machine_name.startswith(model):
            return model
    return machine_name.rsplit(" 0.", 1)[0]


def _normalize_quality_label(value: str) -> str | None:
    key = _normalize_key(value)
    if not key or key in {"020mmstandard", "020standard", "standard", "safequalitydefault"}:
        return "0.20mm Standard"
    if "020" in key and "standard" in key:
        return "0.20mm Standard"
    return None


def _normalize_material_kind(value: str) -> str | None:
    key = _normalize_key(value)
    for material_kind in ("pla", "petg", "tpu", "abs", "asa", "pc", "pva", "pa"):
        if material_kind in key:
            return material_kind
    return None


def _pick_default_material(default_materials: list[str], material_kind: str | None) -> str | None:
    if not default_materials:
        return None
    if material_kind:
        matches = [material for material in default_materials if material_kind in _normalize_key(material)]
        if matches and material_kind == "pla":
            generic = [material for material in matches if "generic" in _normalize_key(material)]
            if generic:
                return generic[0]
        if matches:
            return matches[0]
    return default_materials[0]


def dry_run_slice(payload: dict[str, Any] | None, profile_roots: Iterable[Path] | None = None) -> dict[str, Any]:
    request = validate_slice_request(payload)
    preflight = flsun_export_preflight(request, profile_roots=profile_roots)
    executables = discover_executables()
    return {
        "status": "passed",
        "request": request,
        "profile_preflight": preflight,
        "export_safe": preflight.get("status") == "passed",
        "slicer_available": bool(executables.get("orca") or executables.get("prusa")),
        "would_execute": False,
    }


def export_gcode(payload: dict[str, Any] | None, profile_roots: Iterable[Path] | None = None) -> dict[str, Any]:
    preflight = _build_flsun_preflight(payload, profile_roots=profile_roots)
    if os.environ.get("HERMES_ENABLE_EXPORT_GCODE") != "1":
        return {
            "status": "blocked",
            "reason": "G-code export is disabled by default. Set HERMES_ENABLE_EXPORT_GCODE=1 after reviewing the profile path.",
            "profile_preflight": _public_preflight(preflight),
        }
    if preflight.get("status") != "passed":
        return {
            "status": "blocked",
            "reason": "G-code export requires a compatible FLSUN machine/process/filament tuple.",
            "profile_preflight": _public_preflight(preflight),
        }
    request = preflight["request"]
    executables = discover_executables()
    slicer = executables.get("orca") or executables.get("prusa")
    if not slicer:
        return {"status": "blocked", "reason": "No supported slicer executable found."}
    output_dir = Path(request["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    internal = preflight["_internal"]
    args = [
        slicer,
        "--load_settings",
        f"{internal['machine_path']};{internal['process_path']}",
        "--load_filaments",
        str(internal["filament_path"]),
        "--slice",
        "0",
        "--outputdir",
        str(output_dir),
        request["model_path"],
    ]
    result = run_command(args, timeout=120)
    return {
        "status": "passed" if result["returncode"] == 0 else "failed",
        "profile_preflight": _public_preflight(preflight),
        "args": preflight["cli"]["args_preview"],
        "slicer": Path(slicer).name,
        "result": result,
    }
