# Hermes Integration

`hermes_agent_tool.py` exposes a small `hermes_agent_tools` tool for Hermes Agent and also works as a direct smoke script:

```powershell
python integrations\hermes_agent_tool.py health
python integrations\hermes_agent_tool.py orca_version
python integrations\hermes_agent_tool.py printer_observe
python integrations\hermes_agent_tool.py export_preflight
```

The tool calls only the local bridge at `http://127.0.0.1:8765` and supports safe Hermes Agent tool requests such as `actions`, `flsun_inventory`, `printer_targets`, `printer_observe`, `orca_version`, `dry_run`, `export_preflight`, `proof_recent`, `hermes_proof_mcp`, `tool_request`, and blocked-by-default `export_gcode`.

## Hermes Agent Plugin Shape

Upstream `hermes-agent` directory plugins require:

- `plugin.yaml`
- `__init__.py`
- a `register(ctx)` function

The integration plugin folder is:

```text
integrations/hermes-slicer/
```

The committed project-local plugin wrapper is:

```text
.hermes/plugins/hermes-slicer/
```

`integrations/hermes_plugin.yaml` is a legacy manifest record only; it is not a complete installable Hermes Agent plugin folder. Use one of the two plugin folders above for active Hermes loading.

Run Hermes with the pinned V1 upstream agent (`v2026.5.16`, package `0.14.0`), project plugins enabled, and the repo root explicit:

```powershell
$env:HERMES_ENABLE_PROJECT_PLUGINS = "1"
$env:HERMES_SLICER_ROOT = "G:\Github\HermesSlicer"
hermes version
hermes plugins enable hermes-slicer
hermes plugins list
hermes -z "Check HermesSlicer bridge health" -t hermes_agent
```

Hermes does not start the bridge; start `scripts\start_bridge.ps1` first.
The current V1 proof must stay blocked unless `hermes version` reports `v2026.5.16` / package `0.14.0` and `hermes plugins list` shows `hermes-slicer` as enabled in the active Hermes install.

The repeatable local proof command is:

```powershell
python scripts\smoke_hermes_plugin.py
```
