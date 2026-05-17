# HermesSlicer V1 — Executive Summary
Date: 2026-05-17
Lead Auditor: Claude (claude-sonnet-4-6)
Audit Contract: `CLAUDE_AUDIT_CONTRACT.md`
Agent Reports: `proof/claude_audits/agents/`

---

## Truth Checklist

| Question | Answer | Evidence |
|---|---|---|
| Does active Hermes prove `v0.14.0 (2026.5.16)`? | **YES** | `proof/runtime/hermes-plugin-smoke.json` → `version.matches_expected: true`, `stdout: "Hermes Agent v0.14.0 (2026.5.16)"` |
| Is any project-owned path still relying on Hermes v0.12? | **NO** | Zero v0.12 references in `hermes_slicer/`, `integrations/`, `scripts/`, `tests/`, `.hermes/`, `config/`, `proof/` |
| Is `hermes-slicer` enabled and smoke-proved? | **YES** | All 3 wrappers pass; isolated harness: `tools: 1`, `source: project`, `status: "passed"` |
| Does live Hermes Agent connectivity pass, or is it blocked? | **BLOCKED** | `HERMES_AGENT_ENABLED=1` not set; `live_connectivity_claimed: false` |
| Does Hermes Proof MCP pass for this workspace, or is transport/evidence blocked? | **BLOCKED** | `codex_mcp_transport_status: "transport_closed"`; `workspace_scope_ok: false`; `hermes mcp list` = no servers |
| Does AS_USER pass with bounded grant, or is it blocked? | **BLOCKED** | All 4 required env vars absent; `as_user_session.granted: false` |
| Does computer-use pass with visual proof, or is it blocked? | **BLOCKED** | Platform is Windows; macOS-only gate; `cua_driver_installed: false` |
| Does a clean clone from GitHub `main` pass? | **YES** | `proof/runtime/clean-clone-rehearsal.json` → `status: "passed"`, all 6 steps |
| Is V1 tag-ready right now? | **NO** | `tag_readiness.ready: false`; 4 external gates blocked; no owner decision record |

---

## Local Gates — All Passed

| Gate | Status | Proof Artifact |
|---|---|---|
| Hermes Agent v0.14.0 (2026.5.16) version | passed | `proof/runtime/hermes-plugin-smoke.json` |
| hermes-slicer plugin smoke (3 wrappers) | passed | `proof/runtime/hermes-plugin-smoke.json` |
| Bridge bind localhost-only (127.0.0.1) | passed | `tests/test_bridge_core.py` |
| All 13 actions whitelisted and routed | passed | `hermes_slicer/bridge.py`, `tests/test_bridge_core.py` |
| G-code export blocked by default | passed | `hermes_slicer/slicer.py`, `HERMES_ENABLE_EXPORT_GCODE` gate |
| Login geometry (3 viewports) | passed | `proof/runtime/login-geometry.json` |
| All 5 screenshots present and valid | passed | `proof/runtime/screenshot-format.json` |
| JusPrin reframe — web surface clean | passed | `tests/test_ui_static.py` |
| API contract drift guard | passed | `tests/test_api_contract.py` |
| All 14 local proof files present | passed | `proof/runtime/v1-release-checklist.json` |
| Submodule pins clean | passed | `proof/runtime/submodule-stack.json` |
| Redaction scan clean | passed | `proof/security/redaction-report.md` |
| Clean-clone rehearsal from GitHub main | passed | `proof/runtime/clean-clone-rehearsal.json` |

---

## External Gates — All Blocked

| Gate | Blocked Reason | Required to Unblock |
|---|---|---|
| Live Hermes Agent provider bridge | `HERMES_AGENT_ENABLED=1` not set | Set `HERMES_AGENT_ENABLED=1` + `HERMES_AGENT_HEALTH_URL` pointing at running v0.14.0 |
| Bounded AS_USER grants | All 4 env vars absent | Set `HERMES_HUMAN_GRANT_SECRET`, `HERMES_AS_USER_GRANT_ID`, `HERMES_AS_USER_SCOPES`, `HERMES_AS_USER_EXPIRES_AT` (short TTL) |
| Hermes Proof MCP transport | No MCP servers configured; transport closed | Implement MCP stdio server, `hermes mcp add`, workspace-scoped to `G:\Github\HermesSlicer` |
| Computer-use visual proof | Platform is Windows; macOS-only | macOS host, `cua-driver` installed, bounded AS_USER, visual proof run |

---

## Top Gaps Found by Audit (P0 → P1 → P2)

### P0 — Blocks Truthful Tag
1. **No owner acceptance decision record** for the 4 external gates. `V1_RELEASE_CHECKLIST.md` requires explicit owner sign-off; none exists.
2. **No `write_hermes_proof_mcp_live.py` script** — even when the MCP transport opens, there is no code path to produce a `passed` `hermes-proof-mcp.json`.

### P1 — Important Before Tag
3. `validate_proof.py` deep-checks only 8 of 14 proof files; 6 files are existence-checked only.
4. No standalone `proof/runtime/as_user_session.json` artifact.
5. `pyproject.toml` missing `license = {text = "AGPL-3.0-only"}`.
6. ROADMAP.md P0 gate 5 plugin-enable phrasing is stale.

### P2 — Useful Before Tag
7. No MCP stdio server implementation (`hermes_slicer/mcp_server.py`).
8. Missing `requestBody` schemas on POST endpoints in `api_contract.openapi.yaml`.
9. Missing `hermes-tool-tts_speak.json` proof artifact.
10. `regenerate_proof.ps1` and `clean_clone_rehearsal.ps1` do not assert Hermes CLI version before proceeding.
11. No AS_USER TTL edge-case tests, no v0.12 rejection test, no IPv6 bind tests.
12. No `CONTRIBUTING.md`, no `CHANGELOG.md`.

---

## Audit File Inventory

| File | Purpose |
|---|---|
| `proof/claude_audits/00_EXECUTIVE_SUMMARY.md` | This file — truth checklist, gate summary, top gaps |
| `proof/claude_audits/01_E2E_COMPLETION_AUDIT.md` | End-to-end stack audit by layer |
| `proof/claude_audits/02_GAP_REGISTER.md` | All gaps by priority with evidence |
| `proof/claude_audits/03_BLOCKERS_AND_EXTERNAL_GATES.md` | External gates, separation from local completed work |
| `proof/claude_audits/04_CODEX_FIX_QUEUE.md` | Ranked Codex action queue |
| `proof/claude_audits/05_EVIDENCE_INDEX.md` | All proof artifacts and their gate status |
| `proof/claude_audits/agents/agent1_runtime_wiring.md` | Runtime Wiring Agent raw report |
| `proof/claude_audits/agents/agent2_hermes_gate.md` | Hermes Agent Gate raw report |
| `proof/claude_audits/agents/agent3_proof_mcp.md` | Proof and MCP raw report |
| `proof/claude_audits/agents/agent4_ui_product.md` | UI and Product raw report |
| `proof/claude_audits/agents/agent5_release_completion.md` | Release Completion raw report |

---

## Non-Markdown Files Changed During Audit

None. The Claude audit followed the CLAUDE_AUDIT_CONTRACT.md hard rules. No source code, tests, scripts, proof JSON, screenshots, assets, configuration, or lock files were modified. All output is Markdown only under `proof/claude_audits/`.
