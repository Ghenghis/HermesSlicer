# HermesSlicer

HermesSlicer V1 is a local sidecar for OrcaSlicer: a dark floating web panel, a localhost-only bridge, safe Orca/Prusa executable checks, Azure English voice assignment, and sanitized proof logs.

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

The bridge detects local Orca profile resources and exposes a safe inventory at:

```text
GET http://127.0.0.1:8765/api/orca/flsun
```

On this machine the inventory includes `FLSun T1`, `FLSun V400`, and `FLSun S1` machine/profile resources. It reports names and relative profile paths only.
