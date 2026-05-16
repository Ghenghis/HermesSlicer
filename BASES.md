# Upstream Bases

HermesSlicer uses upstream bases as pinned references, not copied source blobs.

## Layout

```text
upstream/
  OrcaSlicer/     OrcaSlicer/OrcaSlicer
  FlsunSlicer/    Flsun3d/FlsunSlicer
  JusPrin/        TheSpaghettiDetective/JusPrin
  hermes-agent/  NousResearch/hermes-agent
```

Both are Git submodules. Clone with:

```powershell
git clone --recurse-submodules https://github.com/Ghenghis/HermesSlicer.git
```

Or update after clone:

```powershell
git submodule update --init --recursive
```

## Pins

`upstream/OrcaSlicer`

- Remote: https://github.com/OrcaSlicer/OrcaSlicer
- Commit: `b3fe733bf2c8fa7d3c5bf78e93608ca1cd295a7b`
- Branch at clone time: `main`
- Describe: `nightly-builds`
- Role: Direct OrcaSlicer CLI, profile, and UI behavior reference.
- License caution: AGPLv3. Treat as reference/pattern unless there is an explicit license decision.

`upstream/FlsunSlicer`

- Remote: https://github.com/Flsun3d/FlsunSlicer
- Commit: `fb02854cb01411a5ed6bd7353ef744854e6d4ead`
- Branch at clone time: `main`
- Describe: `1.1.3`
- Role: FLSUN slicer/profile/vendor behavior reference.
- License caution: AGPLv3. Treat as reference/pattern unless there is an explicit license decision.

`upstream/JusPrin`

- Remote: https://github.com/TheSpaghettiDetective/JusPrin
- Commit: `095fb665762ad4dbbb2bed155b3a728dd1a3bac2`
- Branch at clone time: `main`
- Role: Orca-derived GenAI slicing pattern source.
- License caution: AGPL-family slicer code. Treat as reference/pattern unless there is an explicit license decision.

`upstream/hermes-agent`

- Remote: https://github.com/NousResearch/hermes-agent
- Commit: `a91a57fa5a13d516c38b07a141a9ce8a3daabeb0`
- Tag: `v2026.5.16`
- Package version: `0.14.0` from `upstream/hermes-agent/pyproject.toml` and `upstream/hermes-agent/hermes_cli/__init__.py`
- Role: Hermes tool/MCP/plugin base and orchestration reference.

## Local Integration Layer

`hermes-agent-tooling` is not a separate upstream submodule in this repo. It is the local integration slice merged from the `integration/hermes-agent-tooling` branch:

- `integrations/hermes_agent_tool.py`
- `integrations/hermes-slicer/plugin.yaml`
- `integrations/hermes-slicer/__init__.py`
- `tests/test_hermes_integration.py`

Those files are backed by the real `upstream/hermes-agent` submodule pinned above.

## Not Submodules Yet

- `prusa3d/PrusaSlicer`: important upstream ancestry for Orca/FLSUN, but not directly used by V1 runtime or proof gates yet.
- `modelcontextprotocol/python-sdk`: should be a package dependency when we add a full MCP stdio server, not a source submodule today.
- `Moonraker`, `OctoPrint`, and `Klipper`: printer-control integrations are outside the V1 safety scope because upload/start is intentionally not implemented.

## V1 Rule

Use upstream code as an inspected base and integration reference. Do not copy upstream implementation into `hermes_slicer/` without a proof note naming source file, license impact, and the local reason copying is necessary.
