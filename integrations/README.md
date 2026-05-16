# Hermes Integration

`hermes_agent_tool.py` exposes a small `slicer_bridge` tool for Hermes-style plugin registration and also works as a direct smoke script:

```powershell
python integrations\hermes_agent_tool.py health
python integrations\hermes_agent_tool.py orca_version
```

The tool calls only the local bridge at `http://127.0.0.1:8765` and supports `health`, `actions`, `orca_version`, and `dry_run`.
