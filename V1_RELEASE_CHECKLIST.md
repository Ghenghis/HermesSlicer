# HermesSlicer V1 Release Checklist

Generated: 2026-05-17T13:18:03.978720+00:00

## Proof Summary

- Local proof files present: 13/13
- Missing proof files: none
- Failed/invalid proof files: none
- Clean-clone rehearsal: passed
- Active Hermes plugin smoke: blocked

## Blocked External Gates

- live_hermes_agent_provider_bridge: HERMES_AGENT_ENABLED=1 is required before claiming live Hermes Agent connectivity. Required: HERMES_AGENT_ENABLED=1, one provider key: DEEPSEEK_API_KEY, MINIMAX_API_KEY, or SILICONFLOW_API_KEY, or one local backend endpoint: HERMES_AGENT_BASE_URL, LM_STUDIO_BASE_URL, or OPENAI_BASE_URL, and live proof: HERMES_AGENT_HEALTH_URL pointing at Hermes Agent and returning ok/passed.
- bounded_as_user_grants: No active AS_USER session is granted in V1 proof. HERMES_HUMAN_GRANT_SECRET is required before a bounded human grant can be requested. Required: HERMES_HUMAN_GRANT_SECRET, explicit scopes, short TTL.
- hermes_proof_mcp_transport: Hermes Proof MCP transport is closed in the current Codex lead session; local proof ledger remains available. Agent audit reported a live locks MCP scoped to G:\Github\Hermes3D, so HermesSlicer must not accept it until workspace_root matches this repo. Required: working Hermes Proof MCP transport, successful evidence verification, workspace_root=G:\Github\HermesSlicer.
- active_hermes_plugin_smoke: Active Hermes CLI is v0.12.0 (2026.4.30); expected v2026.5.16 / package 0.14.0. Active Hermes plugins list does not include hermes-slicer. Required: v2026.5.16, HERMES_ENABLE_PROJECT_PLUGINS=1 for project plugin loading, hermes plugins enable hermes-slicer in the active Hermes install.

## Tag Readiness

- Ready to tag V1: no
- Local gates ready: yes
- Clean-clone rehearsal passed: yes
- Notes: Do not tag V1 until external live-agent, MCP, and plugin gates are proved or explicitly accepted as release-blocking owner decisions.
