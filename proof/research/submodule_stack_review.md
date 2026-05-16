# Submodule Stack Review

Date: 2026-05-16

## Included

- `upstream/OrcaSlicer`: direct OrcaSlicer CLI/profile/UI behavior reference.
- `upstream/FlsunSlicer`: FLSUN vendor slicer/profile behavior reference.
- `upstream/JusPrin`: GenAI slicing pattern reference.
- `upstream/hermes-agent`: Hermes Agent tool/plugin/MCP orchestration reference, pinned to `v2026.5.16`.

## Hermes Agent Tooling

`hermes-agent-tooling` is not a separate upstream repository pinned as a submodule. It is the local integration slice that added:

- `integrations/hermes_agent_tool.py`
- `integrations/hermes-slicer/plugin.yaml`
- `integrations/hermes-slicer/__init__.py`
- `tests/test_hermes_integration.py`

Command run:

```powershell
gh search repos hermes-agent-tooling --limit 10 --json fullName,url,description,visibility
gh search repos "hermes agent tooling" --limit 10 --json fullName,url,description,visibility
```

Observed: no exact upstream `hermes-agent-tooling` repository from Nous Research or another authoritative owner. Do not add a random community repo under that name.

## Held Out

- `prusa3d/PrusaSlicer`: AGPLv3 ancestry for Orca/FLSUN, but not directly used by V1 runtime or proof gates.
- `modelcontextprotocol/python-sdk`: MIT official MCP SDK; use as a package dependency when adding a full MCP stdio server.
- `Moonraker`, `OctoPrint`, and `Klipper`: printer-control layer is outside V1 because upload/start is intentionally not implemented.
