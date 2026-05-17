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

## Current Codex MCP Check

Observed on 2026-05-16 through the Hermes Proof MCP tools available in this session:

- `hermes_verify_evidence`: passed with no hash-chain break.
- `hermes_agent_health`: blocked because the external Hermes Agent provider bridge reports `bridge disabled`.
- `hermes_user_grant_session`: blocked because external `HERMES_HUMAN_GRANT_SECRET` is not present.
- Evidence entry: `ev_cc7203be094d96f4`.

To make this gate live, the environment hosting the Hermes Proof/Agent MCP tools must set `HERMES_AGENT_ENABLED=1` and provide at least one healthy provider backend such as `DEEPSEEK_API_KEY`, `MINIMAX_API_KEY`, `SILICONFLOW_API_KEY`, or a local LM Studio-compatible endpoint. This is separate from the local HermesSlicer bridge at `http://127.0.0.1:8765`.

## Hermes Release Pin Note

`v2026.5.16` is an annotated tag. `git ls-remote` reports tag object `8487dfb57d2f2f7b310a2b3eb692b32674af22cd`; the checked-out submodule peels to commit `a91a57fa5a13d516c38b07a141a9ce8a3daabeb0`, where package metadata reports `0.14.0`.

## Decision

Use the plugin-style Hermes Agent tool router first because it is small, auditable, and calls only `http://127.0.0.1:8765`. Do not invent a user's private Hermes MCP endpoint. If a live Hermes MCP server is later identified, bind this bridge through that config with proof.

## Risks

- The exact installed Hermes variant on this machine has not been mutated.
- Plugin install location may differ between Hermes Agent builds; keep the shim import-light and directly executable for smoke testing.
- Hermes Agent upstream includes computer-use tooling, but HermesSlicer V1 intentionally does not expose computer-use through the slicer bridge. Future use must be read-only first and gated by scoped AS_USER grants.
