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

- `upstream/OrcaSlicer` from [OrcaSlicer/OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer)
- `upstream/FlsunSlicer` from [Flsun3d/FlsunSlicer](https://github.com/Flsun3d/FlsunSlicer)
- `upstream/JusPrin` from [TheSpaghettiDetective/JusPrin](https://github.com/TheSpaghettiDetective/JusPrin)
- `upstream/PrusaSlicer` from [prusa3d/PrusaSlicer](https://github.com/prusa3d/PrusaSlicer)
- `upstream/hermes-agent` from [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent), pinned to `v2026.5.16`
- `upstream/mcp-python-sdk` from [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)
- `upstream/moonraker` from [Arksine/moonraker](https://github.com/Arksine/moonraker)
- `upstream/OctoPrint` from [OctoPrint/OctoPrint](https://github.com/OctoPrint/OctoPrint)
- `upstream/klipper` from [Klipper3d/klipper](https://github.com/Klipper3d/klipper)

See `BASES.md` and `BRANCHES.md`.

## V1 Completion Track

Use `ROADMAP.md` and `ACTION_PLAN.md` as the source of truth for finishing V1. The current stack is proofable locally, but V1 should not be tagged until the P0 gates in `ROADMAP.md` pass or are explicitly accepted as release blockers.

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

See `integrations/README.md` for project-local plugin setup. Hermes does not start the bridge; start the bridge first, then use the `hermes_agent` toolset.

`hermes-agent-tooling` is the local integration branch/slice, not a separate upstream submodule. The source lives under `integrations/` and is tested against the pinned `upstream/hermes-agent` submodule. The visible panel starts with a Hermes Slicer local-session gate and then opens a Hermes Agent tool console, not a JusPrin-style slicer settings chatbot.

## Proof Bundle

- `proof/research/jusprin_file_map.md`
- `proof/research/hermes_agent_file_map.md`
- `proof/research/submodule_stack_review.md`
- `proof/runtime/flsun-export-preflight.json`
- `proof/runtime/flsun-profile-inventory.json`
- `proof/runtime/hermes-tool-export_preflight.json`
- `proof/runtime/proof-validation.json`
- `proof/runtime/submodule-stack.json`

Root license is still a project-owner decision. Until that is chosen, JusPrin stays as a pinned AGPL upstream reference and HermesSlicer does not copy JusPrin C++ code.
