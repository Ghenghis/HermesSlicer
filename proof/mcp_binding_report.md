# Hermes MCP / Tool Binding Report

Date: 2026-05-16

## Sources Checked

- https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/mcp/mcp-native-mcp
- https://hermes-agent.nousresearch.com/docs/developer-guide/tools-runtime
- https://github.com/NousResearch/hermes-agent/releases/tag/v2026.5.16
- `G:\Github\Hermes_OrcaSlicer_Codex_Contract_Kit\research\SOURCES_STARTING_POINTS.md`

## Observed

- Hermes Agent has a built-in MCP client that reads `mcp_servers` from its config and exposes discovered tools with an `mcp_<server>_<tool>` naming pattern.
- Hermes tools can also be registered through plugin/tool registration paths.
- Release tag `v2026.5.16` exists at commit `8487dfb57d2f2f7b310a2b3eb692b32674af22cd`.

## Implemented Binding

This repo includes `integrations/hermes_agent_tool.py` and `integrations/hermes_plugin.yaml`. The tool exposes `hermes_agent_tools` actions:

- `health`
- `actions`
- `profiles`
- `orca_version`
- `dry_run`
- `export_preflight`
- `export_gcode`
- `tool_request`
- `tts_speak`
- `proof_recent`
- `hermes_proof_mcp`
- `agents`

## Current Runtime MCP Check

Observed on 2026-05-17 for the active HermesSlicer workspace:

- Active `hermes version`: `Hermes Agent v0.14.0 (2026.5.16)` from `G:\Github\HermesSlicer\upstream\hermes-agent`.
- Active plugin state: `hermes-slicer` is enabled in the user Hermes plugin directory.
- `hermes mcp list`: no MCP servers configured.
- Codex Hermes locks MCP transport: closed in this lead session.
- Runtime artifact: `proof/runtime/hermes-proof-mcp.json` is `blocked` because no workspace-scoped Hermes Proof MCP evidence is currently available.

To make this gate live, the environment hosting the Hermes Proof/Agent MCP tools must expose a working Hermes Proof MCP transport, verify evidence for `G:\Github\HermesSlicer`, set `HERMES_AGENT_ENABLED=1`, and provide a live Hermes Agent v0.14.0 / `v2026.5.16` health endpoint. This is separate from the local HermesSlicer bridge at `http://127.0.0.1:8765`.

## Hermes Release Pin Note

`v2026.5.16` is an annotated tag. `git ls-remote` reports tag object `8487dfb57d2f2f7b310a2b3eb692b32674af22cd`; the checked-out submodule peels to commit `a91a57fa5a13d516c38b07a141a9ce8a3daabeb0`, where package metadata reports `0.14.0`.

## Decision

Use the plugin-style Hermes Agent tool router first because it is small, auditable, and calls only `http://127.0.0.1:8765`. Do not invent a user's private Hermes MCP endpoint. If a live Hermes MCP server is later identified, bind this bridge through that config with proof.

## Risks

- Plugin install location may differ between Hermes Agent builds; keep the shim import-light and directly executable for smoke testing.
- Hermes Agent upstream includes computer-use tooling, but HermesSlicer V1 does not expose it through the slicer bridge unless macOS `cua-driver`, bounded AS_USER, and visual proof are all present.
