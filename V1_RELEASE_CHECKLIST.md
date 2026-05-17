# HermesSlicer V1 Release Checklist

Generated: 2026-05-17T16:35:41.358271+00:00

## Proof Summary

- Local proof files present: 15/15
- Missing proof files: none
- Failed/invalid proof files: none
- Clean-clone rehearsal: passed
- Active Hermes plugin smoke: passed

## Blocked External Gates

- live_hermes_agent_provider_bridge: HERMES_AGENT_ENABLED=1 is required before claiming live Hermes Agent connectivity. Required: HERMES_AGENT_ENABLED=1, one provider key: OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, GOOGLE_API_KEY, DEEPSEEK_API_KEY, MINIMAX_API_KEY, or SILICONFLOW_API_KEY, or one local backend endpoint: HERMES_AGENT_BASE_URL, LM_STUDIO_BASE_URL, or OPENAI_BASE_URL, and live proof: HERMES_AGENT_HEALTH_URL pointing at Hermes Agent v0.14.0 / v2026.5.16 and returning ok/passed.
- bounded_as_user_grants: HERMES_HUMAN_GRANT_SECRET is not present. HERMES_AS_USER_SCOPES must include at least one explicit scope. HERMES_AS_USER_GRANT_ID is required. HERMES_AS_USER_EXPIRES_AT must be an ISO-8601 UTC timestamp. Required: HERMES_HUMAN_GRANT_SECRET, HERMES_AS_USER_GRANT_ID, HERMES_AS_USER_SCOPES, HERMES_AS_USER_EXPIRES_AT, short TTL.
- hermes_proof_mcp_transport: No workspace-scoped Hermes Proof MCP evidence is available. Active Hermes v0.14 CLI also reports no configured MCP servers. Required: working Hermes Proof MCP transport, successful evidence verification, workspace_root=G:\Github\HermesSlicer.
- hermes_agent_computer_use_visual_control: Hermes Agent v0.14 computer-use backend is macOS-only; current platform is Windows. Required: macOS host, cua-driver installed, bounded AS_USER grant, visual proof run.

## Tag Readiness

- Ready to tag V1: no
- Local gates ready: yes
- Clean-clone rehearsal passed: yes
- Notes: Do not tag full V1 until external live-agent, AS_USER, MCP, and computer-use gates are proved. A separate scoped local-sidecar tag would need explicit owner approval documenting excluded/deferred live gates.
