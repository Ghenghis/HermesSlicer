# Hermes Integration

`hermes_agent_tool.py` exposes a small `slicer_bridge` tool for Hermes Agent and also works as a direct smoke script:

```powershell
python integrations\hermes_agent_tool.py health
python integrations\hermes_agent_tool.py orca_version
python integrations\hermes_agent_tool.py flsun_inventory
```

The tool calls only the local bridge at `http://127.0.0.1:8765` and supports `health`, `actions`, `profiles`, `flsun_inventory`, `orca_version`, and `dry_run`.

## Hermes Agent Plugin Shape

Upstream `hermes-agent` directory plugins require:

- `plugin.yaml`
- `__init__.py`
- a `register(ctx)` function

The installable plugin folder is:

```text
integrations/hermes-slicer/
```

For a project-local plugin, copy or link that folder to:

```text
.hermes/plugins/hermes-slicer/
```

Then run Hermes with project plugins enabled and the repo root explicit:

```powershell
$env:HERMES_ENABLE_PROJECT_PLUGINS = "1"
$env:HERMES_SLICER_ROOT = "G:\Github\HermesSlicer"
hermes plugins enable hermes-slicer
hermes -z "Check HermesSlicer bridge health" -t hermes_orca
```

Hermes does not start the bridge; start `scripts\start_bridge.ps1` first.
