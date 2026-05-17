# Agent 2: Hermes Agent Gate Audit Report
Date: 2026-05-17
Auditor: Claude Agent (hermes-gate)

## 1. Summary

| Gate | Status |
|------|--------|
| Hermes v0.14 version enforcement | verified complete |
| Stale v0.12 references in project-owned files | none found |
| Plugin smoke (3 wrappers + harness) | verified complete |
| Live Hermes Agent health gate | blocked — needs external credential |
| Hermes Proof MCP transport | blocked — needs external environment |
| AS_USER bounded grant gate | blocked — needs external credential |
| Computer-use gate (Windows platform) | blocked by design — macOS only |
| V1 tag-readiness | NOT READY — 4 external gates remain blocked |

**Truth checklist answers:**
- Active Hermes proves `v0.14.0 (2026.5.16)`: **YES** — `proof/runtime/hermes-plugin-smoke.json` `version.matches_expected: true`
- Project-owned path relies on Hermes v0.12: **NO** — all grep scans clean
- `hermes-slicer` enabled and smoke-proved: **YES** — all 3 wrappers pass, isolated harness passes (`tools: 1`)
- Live Hermes Agent connectivity: **BLOCKED** — `HERMES_AGENT_ENABLED=1` not set
- Hermes Proof MCP for this workspace: **BLOCKED** — no MCP servers configured; `transport_closed`
- AS_USER bounded grant: **BLOCKED** — all 4 required env vars absent
- Computer-use visual proof: **BLOCKED** — platform is Windows; macOS-only gate
- V1 tag-ready right now: **NO** — `tag_readiness.ready: false`

---

## 2. Hermes v0.14 Enforcement

## P3: Hermes v0.14 Version Gate — Verified Complete
- Status: verified complete
- Evidence: `proof/runtime/hermes-plugin-smoke.json` — `version.matches_expected: true`, CLI at `C:\Python314\Scripts\hermes.EXE` pointing to `upstream/hermes-agent`, stdout `Hermes Agent v0.14.0 (2026.5.16)`, `expected_package_version: "0.14.0"`, `expected_release_tag: "v2026.5.16"`.
- Why it matters: Confirms the upstream submodule binary is active; no stale install.
- Codex next action: None. Version constants locked in `scripts/smoke_hermes_plugin.py` and `hermes_slicer/config.py`.
- Release impact: documentation only — gate passes.

---

## 3. Stale v0.12 References Scan

## P3: Stale v0.12 Reference Scan — Clean
- Status: verified complete
- Evidence: Grep of `v0\.12|0\.12\.0|hermes.*0\.12` across `hermes_slicer/`, `integrations/`, `scripts/`, `tests/`, `.hermes/`, `config/`, `proof/` (excluding `upstream/`) returned zero code matches. One occurrence found in `proof/claude_audits/AUDIT_TEMPLATE.md` — an audit form label, not a code reference.
- Why it matters: No stale v0.12 code path can bypass the version gate or cause a false pass.
- Codex next action: None. Continue running version gate check on every proof regeneration.
- Release impact: documentation only.

---

## 4. Plugin Smoke Gate

## P3: Plugin Smoke Gate — Verified Complete
- Status: verified complete
- Evidence: `proof/runtime/hermes-plugin-smoke.json` — all 3 wrappers pass (`committed_project_plugin`, `committed_project_plugin_cwd_fallback`, `integration_plugin`), `isolated_active_project_plugin_harness.status: "passed"` (`plugins_seen: 23`, `hermes-slicer` enabled, `tools: 1`, `source: project`). All wrappers: `action_count: 13`, `has_export_preflight: true`, `has_hermes_proof_mcp: true`, `handler_callable: true`.
- Why it matters: Confirms plugin integrates cleanly with active Hermes v0.14 via both root-resolution paths.
- Codex next action: Post-V1 hardening: add assertion that `action_count >= 13` to `scripts/smoke_hermes_plugin.py` to catch regressions.
- Release impact: verified complete.

Required conditions documented (must all be set for project-plugin loading):
- `HERMES_ENABLE_PROJECT_PLUGINS=1`
- `hermes plugins enable hermes-slicer` in the active Hermes install
- Run from HermesSlicer repo root or set `HERMES_SLICER_ROOT`

---

## 5. Live Health Gate

## P1: Live Hermes Agent Bridge — Blocked (External Credential Required)
- Status: blocked — needs external credential
- Evidence: `proof/runtime/hermes-proof-mcp.json` → `hermes_agent_bridge.enabled: false`, `live_connectivity_claimed: false`, `HERMES_AGENT_ENABLED` not set, no `HERMES_AGENT_HEALTH_URL` configured. Provider keys `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, and `OPENAI_BASE_URL` are present — only the enable flag and health URL are missing.
- Why it matters: Without `HERMES_AGENT_ENABLED=1`, live connectivity is always refused regardless of provider key presence. Three provider keys are available and ready.
- Codex next action: Set `HERMES_AGENT_ENABLED=1` and `HERMES_AGENT_HEALTH_URL=http://127.0.0.1:<port>/health`. No code changes required. Re-run `scripts/write_hermes_proof_mcp_status.py` after setting.
- Release impact: blocks live feature — does NOT block V1 tag per owner decision.

Gate logic in `hermes_slicer/config.py::hermes_agent_bridge_gate()` is correctly implemented:
- `HERMES_AGENT_ENABLED=1` check first
- Provider key presence check
- Live health probe requiring v0.14.0 identity and `ok`/`passed` response
- Anti-confusion guard prevents using the slicer bridge URL as the health endpoint

## P2: Hermes Proof MCP Transport — Blocked
- Status: blocked — needs external environment
- Evidence: `hermes mcp list` returns "No MCP servers configured"; `codex_mcp_transport_status: "transport_closed"`; `workspace_scope_ok: false`; `active_hermes_mcp_configured: false`.
- Why it matters: Evidence cannot be MCP-verified for this workspace. A Hermes3D-scoped MCP must not count for HermesSlicer workspace evidence. Only a workspace-scoped MCP with `workspace_root=G:\Github\HermesSlicer` qualifies.
- Codex next action: Configure workspace-scoped MCP server (`hermes mcp add hermes-slicer-proof --command python --args -m hermes_slicer.mcp_server`), set `workspace_root`, verify evidence. No code changes needed for the env setup; the MCP stdio server itself must be implemented first.
- Release impact: blocks live MCP feature — does NOT block V1 tag.

---

## 6. AS_USER Grant Gate

## P1: AS_USER Bounded Grant — Blocked (External Credential Required)
- Status: blocked — needs external credential
- Evidence: `proof/runtime/hermes-proof-mcp.json` → `as_user_session.granted: false`, `secret_present: false`, `grant_id_present: false`, `scopes: []`, `max_ttl_seconds: 900`. All 4 required env vars absent.
- Why it matters: Required for computer-use and future elevated actions. Security properties are defined in code but untested at runtime.
- Codex next action: Set `HERMES_HUMAN_GRANT_SECRET`, `HERMES_AS_USER_GRANT_ID`, `HERMES_AS_USER_SCOPES` (explicit, non-empty, e.g., `visual.inspect,slice.preflight`), `HERMES_AS_USER_EXPIRES_AT` (UTC ISO-8601, within 15 minutes). No code changes required.
- Release impact: blocks live AS_USER feature — does NOT block V1 tag.

`as_user_session_gate()` implementation is correct:
- All 4 vars required
- Max 900s TTL enforced
- Empty scopes rejected
- Expired grants rejected
- No path grants all-actions by default

## P2: Missing Test — AS_USER Grant TTL Expiry Not Unit-Tested
- Status: open — needs Codex implementation
- Evidence: `tests/test_hermes_integration.py` has no tests exercising `as_user_session_gate()`. TTL boundary cases (expired, TTL > 900s, TTL = 900s), empty-scopes, and valid-grant cases are all uncovered.
- Why it matters: TTL expiry is a security property. A regression in timestamp parsing or TTL comparison would be undetected.
- Codex next action: Add `AsUserSessionGateTests` in `tests/test_hermes_integration.py` covering: (a) all vars absent → blocked, (b) expired timestamp → blocked, (c) TTL > 900s → blocked, (d) TTL = 900s exactly → passed, (e) valid grant with explicit scopes → passed, (f) empty scopes → blocked.
- Release impact: polish — closes a security test gap. Does not block V1 tag.

---

## 7. Computer-Use Gate

## P3: Computer-Use Gate — Correctly Blocked on Windows (By Design)
- Status: blocked by design
- Evidence: `proof/runtime/hermes-computer-use.json` → `available: false`, `supported_platform: false`, `platform: "Windows"`, `cua_driver_installed: false`. `hermes computer-use status` stdout: `"cua-driver: not installed. Run: hermes computer-use install"`.
- Why it matters: Gate correctly reports the platform constraint. No computer-use exposure exists in V1 bridge routes.
- Codex next action: None for V1. Post-V1 on macOS: requires `cua-driver`, bounded AS_USER with `visual.inspect` scope, and `HERMES_COMPUTER_USE_VISUAL_PROOF_PATH` pointing to an existing file under `proof/`.
- Release impact: documentation only — gate is correctly `blocked`.

Confirmed: `bridge.py` `ACTION_ROUTES` and `ALLOWED_ACTIONS` contain no computer-use route. The visual proof gate in `write_hermes_computer_use_proof.py` includes a path-traversal guard rejecting paths outside `proof/`.

---

## 8. Missing / Improvements Needed

## P2: Missing Test — Hermes Version Gate Rejection of v0.12
- Status: open — needs Codex implementation
- Evidence: `scripts/smoke_hermes_plugin.py::parse_hermes_version()` sets `matches_expected: False` for non-0.14.0, but no unit test passes a mocked v0.12 string to confirm rejection.
- Why it matters: A prefix-match bug (e.g., `"0.12.0".startswith("0.14")` returning False is correct, but a regex error could pass v0.12).
- Codex next action: Add `ParseHermesVersionTests` in a new `tests/test_smoke_hermes_plugin.py` covering: v0.12.0 rejection, v0.14.0 acceptance, v0.14.1 rejection (exact match required), malformed version string.
- Release impact: polish — does not block V1 tag.

## P2: Missing Proof Artifact for AS_USER Session Gate
- Status: open — missing artifact
- Evidence: There is no `proof/runtime/as_user_session.json` artifact. The AS_USER gate status is embedded inside `hermes-proof-mcp.json` only.
- Why it matters: A standalone AS_USER proof artifact would allow independent verification of the grant gate without parsing the composite MCP artifact.
- Codex next action: Add `scripts/write_as_user_session_proof.py` that calls `as_user_session_gate()` and writes `proof/runtime/as_user_session.json`. Add to `scripts/regenerate_proof.ps1`.
- Release impact: polish — does not block V1 tag.

---

## 9. Codex Next Actions (Ranked)

1. **[Unblocks live Hermes Agent — P1]** Set `HERMES_AGENT_ENABLED=1` + `HERMES_AGENT_HEALTH_URL`; re-run `scripts/write_hermes_proof_mcp_status.py`. No code changes.
2. **[Unblocks AS_USER gate — P1]** Set 4 AS_USER env vars with explicit scopes and short TTL; re-run proof scripts. No code changes.
3. **[Unblocks MCP transport — P1]** Implement MCP stdio server, then configure workspace-scoped `hermes mcp add`. No standalone env-only fix — MCP server code is required first.
4. **[Closes security test gap — P2]** Add `AsUserSessionGateTests` covering TTL expiry, empty scopes, valid grant.
5. **[Closes version gate test gap — P2]** Add `ParseHermesVersionTests` covering v0.12 rejection and v0.14.0 acceptance.
6. **[Adds standalone proof artifact — P2]** Add `scripts/write_as_user_session_proof.py` and `proof/runtime/as_user_session.json`.
7. **[Post-V1 only — P3]** Computer-use: macOS host + cua-driver + bounded AS_USER with visual proof.
