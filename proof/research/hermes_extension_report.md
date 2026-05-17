# Hermes Extension Report

Date: 2026-05-16

## Sources

- https://hermes-agent.nousresearch.com/docs/user-guide/features/tools/
- https://hermes-agent.nousresearch.com/docs/developer-guide/tools-runtime
- https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/mcp/mcp-native-mcp
- https://github.com/NousResearch/hermes-agent/releases/tag/v2026.5.16
- `upstream/hermes-agent`

## Source State

Command run:

```powershell
git ls-remote https://github.com/NousResearch/hermes-agent.git HEAD refs/tags/v2026.5.16
```

Observed output:

```text
fb05f5d4b58d4fb20c3a4a98c2c150de3f729f3c	HEAD
fb05f5d4b58d4fb20c3a4a98c2c150de3f729f3c	refs/heads/main
8487dfb57d2f2f7b310a2b3eb692b32674af22cd	refs/tags/v2026.5.16
```

- License note from public repo page: MIT.
- `v2026.5.16` is an annotated tag object; the local submodule is checked out at the peeled release commit `a91a57fa5a13d516c38b07a141a9ce8a3daabeb0`.

## Observed

- Hermes organizes tools into toolsets and can include MCP server tools.
- MCP tools are discovered at startup from config and become named tools.
- Native tools/plugins can register handlers with schemas and availability checks.

## Local Implementation

- `integrations/hermes_agent_tool.py` exposes a small `hermes_agent_tools` helper with an optional plugin `register(ctx)` function.
- It calls only the local bridge.
- It can be smoked directly with `python integrations\hermes_agent_tool.py health` while the bridge is running.
- It exposes V1-safe Hermes Agent tool actions including `tool_request`, `export_preflight`, `tts_speak`, `proof_recent`, `hermes_proof_mcp`, and blocked-by-default `export_gcode`.

Command run:

```powershell
python integrations\hermes_agent_tool.py health
```

Observed output excerpt:

```text
"status": "ok"
"name": "HermesSlicer Local Bridge"
"bind": "127.0.0.1"
```

Proof file: `proof/runtime/hermes-tool-health.json`

## Local Base

Command run:

```powershell
git submodule add --depth 1 https://github.com/NousResearch/hermes-agent.git upstream/hermes-agent
git -C upstream\hermes-agent fetch --depth 1 origin tag v2026.5.16
git -C upstream\hermes-agent checkout v2026.5.16
git -C upstream\hermes-agent describe --tags --exact-match
```

Observed:

```text
v2026.5.16
```

- The pinned source reports Hermes Agent package version `0.14.0` in `pyproject.toml` and `hermes_cli/__init__.py`.
- GitHub exposes the pinned release as tag `v2026.5.16`; no separate `v0.14` tag was found during local tag checks.

## Decision

Ship the local bridge plus an upstream-compatible Hermes Agent directory plugin wrapper today. Defer full MCP stdio server until the user's active Hermes install and config path are identified with proof.

## Risks

- Multiple Hermes variants may exist locally; installation instructions need to be adjusted to the actual active install.
- Live Hermes Agent provider failover is still gated outside this repo by `HERMES_AGENT_ENABLED=1` and a healthy provider backend.
- Upstream computer-use tooling exists, but HermesSlicer V1 does not expose it through the bridge. Keep computer-use post-V1, read-only first, and AS_USER-scoped.
