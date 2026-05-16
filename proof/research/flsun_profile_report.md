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
- The endpoint reports profile names and relative sub-paths only; it does not copy profile files or expose private data.
- `scripts/write_flsun_profile_proof.py` writes `proof/runtime/flsun-profile-inventory.json` and `proof/runtime/flsun-profile-matrix.json`.

## Decision

Use local Orca FLSun profile inventory as the next truth source before attempting actual G-code export. V1 validates requests and proves Orca executable/profile discovery without copying or converting profile data.

## Risks

- FLSUN T1, V400, and S1 defaults need explicit profile extraction and comparison before any real G-code export.
- `export_gcode` remains intentionally blocked by default and still needs a profile resolver before real export is allowed.
