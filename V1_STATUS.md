# HermesSlicer V1 Status

Date: 2026-05-17

## What Is Complete

- Local bridge bound to `127.0.0.1`.
- Hermes Slicer login artwork and Hermes Agent tool console.
- Login visual/geometry gate for `1366x768`, `1920x1080`, and mobile viewports.
- Whitelisted action dispatch at `/api/action`.
- Hermes Agent local tool wrapper: `hermes_agent_tools` in toolset `hermes_agent`.
- Orca executable/profile probes.
- FLSUN T1, V400, and S1 profile inventory and export preflight.
- G-code export blocked by default unless `HERMES_ENABLE_EXPORT_GCODE=1`.
- Proof ledger, proof validation, redaction scan, screenshots, and API drift tests.
- V1 release checklist output with proof summary, blocked external credentials, and tag-readiness notes.
- Clean-clone rehearsal against GitHub `main` with submodules.
- Root `LICENSE` and `NOTICE`.
- Active Hermes Agent CLI is pinned to `v0.14.0 (2026.5.16)` from `upstream/hermes-agent`.
- Active `hermes-slicer` plugin smoke passes with the plugin enabled in the user Hermes install.

## Remaining V1 Blockers

1. Hermes Proof MCP transport is not currently connected.
   - Current proof: `proof/runtime/hermes-proof-mcp.json` reports `blocked`.
   - Current tool call result in this Codex lead session: transport closed.
   - Agent audit also reported a live locks MCP scoped to `G:\Github\Hermes3D`; HermesSlicer must reject that until `workspace_root` equals `G:\Github\HermesSlicer`.
   - Required external environment: working Hermes Proof MCP transport with successful evidence verification for this workspace.

2. Live Hermes Agent provider bridge is not enabled.
   - Current proof: `/health` reports `live_connectivity_claimed=false`.
   - Required external environment: `HERMES_AGENT_ENABLED=1`, one provider/backend, and live proof via `HERMES_AGENT_HEALTH_URL` pointing at Hermes Agent `v0.14.0` / `v2026.5.16` and returning `ok`/`passed`.
   - Current provider/backend booleans show OpenAI, Anthropic, Gemini, and `OPENAI_BASE_URL` present, but no live Hermes Agent health URL is configured.

3. Bounded AS_USER grants are not enabled.
   - Current proof: no active AS_USER session.
   - Required external env: `HERMES_HUMAN_GRANT_SECRET`, `HERMES_AS_USER_GRANT_ID`, `HERMES_AS_USER_SCOPES`, and short `HERMES_AS_USER_EXPIRES_AT`.
   - Grants must use explicit scopes and max 15-minute TTLs. Do not grant all actions by default.

4. Hermes Agent computer-use visual control is not available on this Windows host.
   - Current proof: `proof/runtime/hermes-computer-use.json` reports `blocked`.
   - Required host/tooling: macOS with `cua-driver`, bounded AS_USER scope, and a visual proof run.

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
$env:HERMES_AGENT_HEALTH_URL = "http://127.0.0.1:<hermes-agent-health-port>/health"
```

External AS_USER grants:

```powershell
$env:HERMES_HUMAN_GRANT_SECRET = "<external secret>"
$env:HERMES_AS_USER_GRANT_ID = "<grant id>"
$env:HERMES_AS_USER_SCOPES = "visual.inspect,slice.preflight"
$env:HERMES_AS_USER_EXPIRES_AT = "<UTC timestamp within 15 minutes>"
```

Do not commit any provider or AS_USER secrets.

## Computer-Use Position

Hermes Agent upstream includes computer-use tooling under:

- `upstream/hermes-agent/tools/computer_use_tool.py`
- `upstream/hermes-agent/tools/computer_use/`

HermesSlicer V1 does not expose computer-use through the slicer bridge. It is powerful, platform-specific, and not required for the V1 proofable local sidecar. Future exposure must start read-only, require AS_USER scope, and preserve a proof trail.
The visible V1 mic/computer-use control now reports `blocked` instead of pretending to go live.

## Final Gate Command Set

```powershell
python -m unittest discover -s tests
python -m compileall hermes_slicer integrations scripts tests
python scripts\validate_submodules.py
powershell -ExecutionPolicy Bypass -File scripts\regenerate_proof.ps1
python scripts\verify_login_geometry.py
python scripts\write_v1_release_checklist.py
python scripts\redaction_scan.py .
powershell -ExecutionPolicy Bypass -File scripts\clean_clone_rehearsal.ps1
```
