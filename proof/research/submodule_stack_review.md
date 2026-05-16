# Submodule Stack Review

Date: 2026-05-16

## Included

- `upstream/OrcaSlicer`: direct OrcaSlicer CLI/profile/UI behavior reference.
- `upstream/FlsunSlicer`: FLSUN vendor slicer/profile behavior reference.
- `upstream/JusPrin`: GenAI slicing pattern reference.
- `upstream/PrusaSlicer`: PrusaSlicer ancestry and CLI/profile behavior reference.
- `upstream/hermes-agent`: Hermes Agent tool/plugin/MCP orchestration reference, pinned to `v2026.5.16`.
- `upstream/mcp-python-sdk`: official Model Context Protocol Python SDK reference.
- `upstream/moonraker`: Klipper Web API server reference.
- `upstream/OctoPrint`: OctoPrint web UI and plugin/API reference.
- `upstream/klipper`: Klipper firmware and host protocol reference.

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

## Validation

Command run:

```powershell
python scripts\validate_submodules.py
```

Proof file: `proof/runtime/submodule-stack.json`

## Safety Boundary

All nine upstreams are pinned as source/reference submodules for complete stack research and design. V1 runtime still does not upload G-code to a printer or start a print. Any future Moonraker, OctoPrint, or Klipper execution path needs its own proof gate, explicit user confirmation path, and license note before being enabled.
