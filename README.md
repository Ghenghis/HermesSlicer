# HermesSlicer

HermesSlicer V1 is a local sidecar for OrcaSlicer: a dark floating web panel, a localhost-only bridge, safe Orca/Prusa executable checks, FLSUN profile preflight, Hermes Agent tooling, Azure English voice assignment, and sanitized proof logs.

## Run

```powershell
python -m hermes_slicer.bridge
```

Open:

```text
http://127.0.0.1:8765
```

Smoke check:

```powershell
python scripts\smoke_bridge.py
```

Full proof regeneration:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\regenerate_proof.ps1
```

Redaction scan:

```powershell
python scripts\redaction_scan.py .
```

## Upstream Bases

The upstream base repos are included as submodules:

- `upstream/JusPrin` from [TheSpaghettiDetective/JusPrin](https://github.com/TheSpaghettiDetective/JusPrin)
- `upstream/hermes-agent` from [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent), pinned to `v2026.5.16`

See `BASES.md` and `BRANCHES.md`.

## V1 Safety Defaults

- Binds to `127.0.0.1` only.
- No arbitrary shell commands.
- Slicer commands use subprocess argument arrays.
- G-code export is disabled unless `HERMES_ENABLE_EXPORT_GCODE=1`.
- Printer upload/start is not implemented in V1.
- Secret values are never returned by `/health`; only present/missing flags are reported.
- The private drive path named in the contract is treated as read-only and excluded from outputs.

## Current Orca/FLSun Proof

The bridge detects local Orca profile resources and exposes a safe inventory plus export preflight:

```text
GET http://127.0.0.1:8765/api/orca/flsun
POST http://127.0.0.1:8765/api/slice/export-preflight
```

On this machine the inventory includes `FLSun T1`, `FLSun V400`, and `FLSun S1` machine/profile resources. Export preflight resolves a compatible machine, process, and filament tuple before G-code export can run. It reports names and relative profile paths only.

## Hermes Agent

The installable Hermes Agent plugin wrapper lives at:

```text
integrations/hermes-slicer
```

See `integrations/README.md` for project-local plugin setup. Hermes does not start the bridge; start the bridge first, then use the `hermes_orca` toolset.

## Proof Bundle

- `proof/research/jusprin_file_map.md`
- `proof/research/hermes_agent_file_map.md`
- `proof/runtime/flsun-export-preflight.json`
- `proof/runtime/flsun-profile-inventory.json`
- `proof/runtime/proof-validation.json`

Root license is still a project-owner decision. Until that is chosen, JusPrin stays as a pinned AGPL upstream reference and HermesSlicer does not copy JusPrin C++ code.
