# Upstream Bases

HermesSlicer uses upstream bases as pinned references, not copied source blobs.

## Layout

```text
upstream/
  OrcaSlicer/     OrcaSlicer/OrcaSlicer
  FlsunSlicer/    Flsun3d/FlsunSlicer
  JusPrin/        TheSpaghettiDetective/JusPrin
  PrusaSlicer/    prusa3d/PrusaSlicer
  hermes-agent/  NousResearch/hermes-agent
  mcp-python-sdk/ modelcontextprotocol/python-sdk
  moonraker/      Arksine/moonraker
  OctoPrint/      OctoPrint/OctoPrint
  klipper/        Klipper3d/klipper
```

All entries above are Git submodules. Clone with:

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
- Tag note: multiple historical release tags point at this commit through `2.0.6`; `describe` returns the nearest tag, not a release choice for HermesSlicer.
- Role: FLSUN slicer/profile/vendor behavior reference.
- License caution: AGPLv3. Treat as reference/pattern unless there is an explicit license decision.

`upstream/JusPrin`

- Remote: https://github.com/TheSpaghettiDetective/JusPrin
- Commit: `095fb665762ad4dbbb2bed155b3a728dd1a3bac2`
- Branch at clone time: `main`
- Role: Orca-derived GenAI slicing pattern source.
- License caution: AGPL-family slicer code. Treat as reference/pattern unless there is an explicit license decision.

`upstream/PrusaSlicer`

- Remote: https://github.com/prusa3d/PrusaSlicer
- Commit: `86d53b67c93472aa649ed58f1c01d3fdddcbf5ad`
- Branch at clone time: `master`
- Describe: `version_2.9.5-rc1`
- Role: PrusaSlicer ancestry and CLI/profile behavior reference.
- License caution: AGPLv3. Treat as reference/pattern unless there is an explicit license decision.

`upstream/hermes-agent`

- Remote: https://github.com/NousResearch/hermes-agent
- Commit: `a91a57fa5a13d516c38b07a141a9ce8a3daabeb0`
- Tag: `v2026.5.16`
- Package version: `0.14.0` from `upstream/hermes-agent/pyproject.toml` and `upstream/hermes-agent/hermes_cli/__init__.py`
- Role: Hermes tool/MCP/plugin base and orchestration reference.

`upstream/mcp-python-sdk`

- Remote: https://github.com/modelcontextprotocol/python-sdk
- Commit: `161834d4aee2633c42d3976c8f8751b6c4d947d5`
- Branch at clone time: `main`
- Describe: `161834d`
- Role: Official Model Context Protocol Python SDK reference.
- License note: MIT.

`upstream/moonraker`

- Remote: https://github.com/Arksine/moonraker
- Commit: `9008485843740c93e0154ccbdac1fc2b02b03aaa`
- Branch at clone time: `master`
- Describe: `9008485`
- Role: Klipper Web API server reference.
- License caution: GPLv3. Treat as reference/pattern unless there is an explicit license decision.

`upstream/OctoPrint`

- Remote: https://github.com/OctoPrint/OctoPrint
- Commit: `727fecb41473ec70d637718700658f76a6b99e81`
- Branch at clone time: `dev`
- Describe: `727fecb`
- Role: OctoPrint web UI and plugin/API reference.
- License caution: AGPLv3. Treat as reference/pattern unless there is an explicit license decision.

`upstream/klipper`

- Remote: https://github.com/Klipper3d/klipper
- Commit: `4cc47cf56542944fdaed633acd525f3b7b17c2bc`
- Branch at clone time: `master`
- Describe: `4cc47cf`
- Role: Klipper firmware and host protocol reference.
- License caution: GPLv3. Treat as reference/pattern unless there is an explicit license decision.

## Local Integration Layer

`hermes-agent-tooling` is not a separate upstream submodule in this repo. It is the local integration slice merged from the `integration/hermes-agent-tooling` branch:

- `integrations/hermes_agent_tool.py`
- `integrations/hermes-slicer/plugin.yaml`
- `integrations/hermes-slicer/__init__.py`
- `tests/test_hermes_integration.py`

Those files are backed by the real `upstream/hermes-agent` submodule pinned above.

## Validation

Run:

```powershell
python scripts\validate_submodules.py
```

The validator writes `proof/runtime/submodule-stack.json` and checks each upstream path, remote URL, commit shape, clean worktree state, and the Hermes Agent `v2026.5.16` / package `0.14.0` requirement.

## V1 Rule

Use upstream code as an inspected base and integration reference. Do not copy upstream implementation into `hermes_slicer/` without a proof note naming source file, license impact, and the local reason copying is necessary.

Printer-control repositories are included for complete stack research and design. V1 still does not upload G-code to a printer or start a print.
