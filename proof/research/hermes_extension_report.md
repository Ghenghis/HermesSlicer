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
a91a57fa5a13d516c38b07a141a9ce8a3daabeb0	HEAD
8487dfb57d2f2f7b310a2b3eb692b32674af22cd	refs/tags/v2026.5.16
```

- License note from public repo page: MIT.

## Observed

- Hermes organizes tools into toolsets and can include MCP server tools.
- MCP tools are discovered at startup from config and become named tools.
- Native tools/plugins can register handlers with schemas and availability checks.

## Local Implementation

- `integrations/hermes_agent_tool.py` exposes a small `slicer_bridge` helper with an optional plugin `register(ctx)` function.
- It calls only the local bridge.
- It can be smoked directly with `python integrations\hermes_agent_tool.py health` while the bridge is running.

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

## Decision

Ship the local bridge plus plugin-style shim today. Defer full MCP stdio server until the user's active Hermes install and config path are identified with proof.

## Risks

- Multiple Hermes variants may exist locally; installation instructions need to be adjusted to the actual active install.
