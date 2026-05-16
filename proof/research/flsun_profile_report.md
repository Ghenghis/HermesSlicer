# FLSUN Profile Report

Date: 2026-05-16

## Sources

- https://github.com/Flsun3d/FlsunSlicer
- https://github.com/martona/flsun-prusaslicer-profiles
- Local Orca profile root: `C:\Program Files\OrcaSlicer\resources\profiles`

## Observed

- Local Orca profile root exists and contains FLSun profile resources.
- `FLSun.json` version is `02.03.02.60`.
- Local Orca includes machine model entries for `FLSun T1`, `FLSun V400`, and `FLSun S1`.
- Local Orca includes nozzle machine presets for `FLSun T1 0.4 nozzle`, `FLSun V400 0.4 nozzle`, and `FLSun S1 0.4 nozzle`.
- Local Orca includes `0.20mm Standard` process presets for T1, V400, and S1.
- T1 and S1 include dedicated FLSun material presets; V400 uses generic FLSun material presets from the manifest.

## Implementation

- `/api/orca/flsun` returns a sanitized inventory for `FLSun T1`, `FLSun V400`, and `FLSun S1`.
- `/api/slice/export-preflight` resolves a canonical FLSUN machine, process, and filament tuple before any G-code export is allowed.
- The endpoint reports profile names and relative sub-paths only; it does not copy profile files or expose private data.
- `scripts/write_flsun_profile_proof.py` writes `proof/runtime/flsun-profile-inventory.json`, `proof/runtime/flsun-profile-matrix.json`, and `proof/runtime/flsun-export-preflight.json`.

## Decision

Use local Orca FLSun profile inventory as the truth source for export preflight. V1 validates requests, proves Orca executable/profile discovery, resolves inherited profile data, and checks process/filament compatibility without copying or converting profile data.

## Risks

- Real G-code export remains intentionally blocked by default unless `HERMES_ENABLE_EXPORT_GCODE=1`.
- Even with export enabled, `export_gcode` refuses to run unless preflight proves a compatible machine/process/filament tuple.
