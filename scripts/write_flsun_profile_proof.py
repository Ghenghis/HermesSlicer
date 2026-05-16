from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.proof import write_json  # noqa: E402
from hermes_slicer.slicer import flsun_export_preflight, flsun_profile_inventory  # noqa: E402


def build_matrix(inventory: dict) -> dict:
    matrix = []
    for target in inventory.get("targets", []):
        matrix.append(
            {
                "model": target.get("model"),
                "model_id": target.get("model_id"),
                "machine_presets": [entry.get("name") for entry in target.get("machine_presets", [])],
                "default_print_profiles": [
                    entry.get("default_print_profile") for entry in target.get("nozzle_defaults", [])
                ],
                "process_presets": [entry.get("name") for entry in target.get("process_presets", [])],
                "filament_presets": [entry.get("name") for entry in target.get("filament_presets", [])],
                "default_materials": target.get("default_materials", []),
            }
        )
    return {
        "status": inventory.get("status"),
        "source": inventory.get("source"),
        "version": inventory.get("version"),
        "matrix": matrix,
    }


def main() -> int:
    inventory = flsun_profile_inventory()
    preflight = flsun_export_preflight({})
    write_json(ROOT / "proof" / "runtime" / "flsun-profile-inventory.json", inventory)
    write_json(ROOT / "proof" / "runtime" / "flsun-profile-matrix.json", build_matrix(inventory))
    write_json(ROOT / "proof" / "runtime" / "flsun-export-preflight.json", preflight)
    print(
        json.dumps(
            {
                "status": inventory["status"],
                "preflight": preflight["status"],
                "targets": [item["model"] for item in inventory.get("targets", [])],
            },
            indent=2,
        )
    )
    return 0 if inventory["status"] == "passed" and preflight["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
