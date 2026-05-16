# Upstream Bases

HermesSlicer uses two upstream bases as pinned references, not copied source blobs.

## Layout

```text
upstream/
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

## V1 Rule

Use upstream code as an inspected base and integration reference. Do not copy upstream implementation into `hermes_slicer/` without a proof note naming source file, license impact, and the local reason copying is necessary.
