# HermesSlicer V1 Status

Date: 2026-05-16

## What Is Complete

- Local bridge bound to `127.0.0.1`.
- Hermes Slicer login artwork and Hermes Agent tool console.
- Whitelisted action dispatch at `/api/action`.
- Hermes Agent local tool wrapper: `hermes_agent_tools` in toolset `hermes_agent`.
- Orca executable/profile probes.
- FLSUN T1, V400, and S1 profile inventory and export preflight.
- G-code export blocked by default unless `HERMES_ENABLE_EXPORT_GCODE=1`.
- Proof ledger, proof validation, redaction scan, screenshots, and API drift tests.
- Root `LICENSE` and `NOTICE`.

## Remaining V1 Blockers

1. Live Hermes Agent provider bridge is not enabled.
   - Current proof: `hermes_agent_health` reports `bridge disabled`.
   - Required external environment: `HERMES_AGENT_ENABLED=1`.
   - Required provider backend: at least one of `DEEPSEEK_API_KEY`, `MINIMAX_API_KEY`, `SILICONFLOW_API_KEY`, or a local LM Studio-compatible endpoint.

2. Bounded AS_USER grants are not enabled.
   - Current proof: no active AS_USER session.
   - Required external secret: `HERMES_HUMAN_GRANT_SECRET`.
   - Grants must use explicit scopes and short TTLs. Do not grant all actions by default.

3. Clean-clone rehearsal still needs final pass.
   - Script: `scripts/clean_clone_rehearsal.ps1`.

4. Active Hermes plugin smoke still needs final pass against the user's Hermes install.
   - Plugin path: `integrations/hermes-slicer`.

## Environment Gates

Local HermesSlicer bridge:

```powershell
python -m hermes_slicer.bridge
```

Optional local bridge overrides:

```powershell
$env:HERMES_SLICER_ROOT = "G:\Github\HermesSlicer"
$env:HERMES_SLICER_BRIDGE_URL = "http://127.0.0.1:8765"
```

Hermes project plugin loading:

```powershell
$env:HERMES_ENABLE_PROJECT_PLUGINS = "1"
```

External Hermes Agent provider bridge:

```powershell
$env:HERMES_AGENT_ENABLED = "1"
$env:DEEPSEEK_API_KEY = "<external secret>"
# or MINIMAX_API_KEY / SILICONFLOW_API_KEY / local LM Studio backend
```

External AS_USER grants:

```powershell
$env:HERMES_HUMAN_GRANT_SECRET = "<external secret>"
```

Do not commit any provider or AS_USER secrets.

## Computer-Use Position

Hermes Agent upstream includes computer-use tooling under:

- `upstream/hermes-agent/tools/computer_use_tool.py`
- `upstream/hermes-agent/tools/computer_use/`

HermesSlicer V1 does not expose computer-use through the slicer bridge. It is powerful, platform-specific, and not required for the V1 proofable local sidecar. Future exposure must start read-only, require AS_USER scope, and preserve a proof trail.

## Final Gate Command Set

```powershell
python -m unittest discover -s tests
python -m compileall hermes_slicer integrations scripts tests
python scripts\validate_submodules.py
powershell -ExecutionPolicy Bypass -File scripts\regenerate_proof.ps1
python scripts\redaction_scan.py .
powershell -ExecutionPolicy Bypass -File scripts\clean_clone_rehearsal.ps1
```
