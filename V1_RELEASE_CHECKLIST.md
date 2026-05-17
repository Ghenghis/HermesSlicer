# HermesSlicer V1 Release Checklist

Generated: 2026-05-17T05:34:42.075015+00:00

## Proof Summary

- Local proof files present: 12/12
- Missing proof files: none
- Failed/invalid proof files: none
- Clean-clone rehearsal: passed
- Active Hermes plugin smoke: missing

## Blocked External Gates

- live_hermes_agent_provider_bridge: HERMES_AGENT_ENABLED=1 is required before claiming live Hermes Agent connectivity. Required: HERMES_AGENT_ENABLED=1, one provider key: DEEPSEEK_API_KEY, MINIMAX_API_KEY, or SILICONFLOW_API_KEY, or one local backend endpoint: HERMES_AGENT_BASE_URL, LM_STUDIO_BASE_URL, or OPENAI_BASE_URL.
- bounded_as_user_grants: No active AS_USER session is granted in V1 proof. HERMES_HUMAN_GRANT_SECRET is required before a bounded human grant can be requested. Required: HERMES_HUMAN_GRANT_SECRET, explicit scopes, short TTL.
- hermes_proof_mcp_transport: Hermes Proof MCP transport is closed in the current Codex session; local proof ledger remains available. Required: working Hermes Proof MCP transport, successful evidence verification.
- active_hermes_plugin_smoke: No proof artifact exists for an active Hermes install loading integrations/hermes-slicer. Required: HERMES_ENABLE_PROJECT_PLUGINS=1, active hermes CLI/install.

## Tag Readiness

- Ready to tag V1: no
- Local gates ready: yes
- Clean-clone rehearsal passed: yes
- Notes: Do not tag V1 until external live-agent, MCP, and plugin gates are proved or explicitly accepted as release-blocking owner decisions.
