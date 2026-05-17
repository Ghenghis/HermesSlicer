# HermesSlicer V1 — Blockers and External Gates
Date: 2026-05-17
Audit Contract: `CLAUDE_AUDIT_CONTRACT.md`

This document separates **local completed work** from **external blocked gates** and describes exactly what is required to unblock each gate.

**Codex correction:** this Claude audit is preserved as review evidence, but its original "does not block V1 local tag" language is not release policy. `V1_RELEASE_CHECKLIST.md` and `proof/runtime/v1-release-checklist.json` are authoritative: a full V1 tag remains blocked until live Hermes Agent, AS_USER, Hermes Proof MCP, and computer-use gates are proved. A narrower local-sidecar tag would require explicit owner approval documenting excluded/deferred live gates.

---

## Local Work — Completed

The following items are fully implemented, proved, and passing. No Codex implementation is required.

| Item | Evidence |
|---|---|
| Hermes Agent v0.14.0 (2026.5.16) pinned and verified | `proof/runtime/hermes-plugin-smoke.json` → `version.matches_expected: true` |
| hermes-slicer plugin registered in 3 wrappers | All 3 wrappers: `action_count: 13`, `has_hermes_proof_mcp: true`, `status: "passed"` |
| Bridge bound to 127.0.0.1 with SystemExit guard | `hermes_slicer/bridge.py`, `tests/test_bridge_core.py` |
| 13 actions whitelisted, routed, and tested | `ALLOWED_ACTIONS == ACTION_ROUTES` asserted in tests |
| G-code export blocked by default (`HERMES_ENABLE_EXPORT_GCODE=1` required) | `hermes_slicer/slicer.py`, test coverage |
| Login visual/geometry gate (3 viewports) | `proof/runtime/login-geometry.json` → `status: "passed"` |
| 5 screenshots present and format-valid | `proof/runtime/screenshot-format.json` → `status: "passed"` |
| JusPrin reframe complete in all product source | `tests/test_ui_static.py` asserts zero JusPrin in `web/` |
| Brand tokens in CSS, config, and tests | `tests/test_ui_static.py::test_css_uses_brand_tokens` |
| API contract drift guard | `api_contract.openapi.yaml`, `tests/test_api_contract.py` |
| 15 local proof files present | `proof/runtime/v1-release-checklist.json` → `local_proof_files: 15/15` |
| Submodule pins clean, BASES.md complete | `proof/runtime/submodule-stack.json` → `status: "passed"`, `errors: []` |
| Redaction scan clean | `proof/security/redaction-report.md` → no secrets found |
| Clean-clone rehearsal from GitHub main | `proof/runtime/clean-clone-rehearsal.json` → `status: "passed"`, 6/6 steps |
| Root LICENSE and NOTICE present | AGPL-3.0; all 9 submodules attributed in NOTICE |
| V1 release checklist with blocked gate documentation | `V1_RELEASE_CHECKLIST.md`, `proof/runtime/v1-release-checklist.json` |

---

## External Gate 1: Live Hermes Agent Provider Bridge

**Gate ID:** `live_hermes_agent_provider_bridge`
**Current status:** BLOCKED
**Proof artifact:** `proof/runtime/hermes-proof-mcp.json` → `hermes_agent_bridge.status: "blocked"`

### What is blocked
The bridge `/health` endpoint reports `live_connectivity_claimed: false`. No live Hermes Agent provider calls can be made from the slicer bridge.

### Why it is blocked
`HERMES_AGENT_ENABLED=1` is not set. The gate logic in `hermes_slicer/config.py::hermes_agent_bridge_gate()` refuses to claim live connectivity without this flag, regardless of provider key presence.

### What IS present (ready when unblocked)
- `OPENAI_API_KEY` present
- `ANTHROPIC_API_KEY` present
- `GEMINI_API_KEY` present
- `OPENAI_BASE_URL` present

### What is required to unblock
1. Set `HERMES_AGENT_ENABLED=1` in the runtime environment.
2. Set `HERMES_AGENT_HEALTH_URL=http://127.0.0.1:<port>/health` pointing at a running Hermes Agent v0.14.0 / v2026.5.16 instance.
3. The health endpoint must return `ok` or `passed` and identify as `v0.14.0 (2026.5.16)`.
4. Re-run `scripts/write_hermes_proof_mcp_status.py` to produce an updated artifact.

**Note:** This does not require code changes. It requires operator environment configuration.

**Codex correction:** This blocks a full V1 tag until live Hermes Agent health proof passes. It may only be deferred for a separately scoped local-sidecar tag with explicit owner approval.

---

## External Gate 2: Bounded AS_USER Session Grants

**Gate ID:** `bounded_as_user_grants`
**Current status:** BLOCKED
**Proof artifact:** `proof/runtime/hermes-proof-mcp.json` → `as_user_session.status: "blocked"`

### What is blocked
No human delegation (AS_USER) grant is active. The bridge cannot act on behalf of a user with delegated scopes. Required for computer-use and future elevated actions.

### Why it is blocked
All 4 required environment variables are absent:
- `HERMES_HUMAN_GRANT_SECRET` — not present
- `HERMES_AS_USER_GRANT_ID` — not present
- `HERMES_AS_USER_SCOPES` — empty; must include at least one explicit scope
- `HERMES_AS_USER_EXPIRES_AT` — not present; must be ISO-8601 UTC

### Grant security properties (implemented, ready)
- Max TTL enforced at 900 seconds (15 minutes)
- Empty scopes are rejected
- Expired timestamps are rejected
- No path grants all-actions by default — scopes must be explicit

### What is required to unblock
1. Generate a `HERMES_HUMAN_GRANT_SECRET` (high-entropy secret string).
2. Create a `HERMES_AS_USER_GRANT_ID` (unique ID per grant).
3. Set `HERMES_AS_USER_SCOPES` to an explicit scope list (e.g., `visual.inspect,slice.preflight`).
4. Set `HERMES_AS_USER_EXPIRES_AT` to a UTC ISO-8601 timestamp within 15 minutes of now.
5. Re-run `scripts/write_hermes_proof_mcp_status.py` to produce an updated artifact.

**Note:** No code changes required. Operator environment configuration only. Do NOT commit secrets.

**Codex correction:** This blocks a full V1 tag until a bounded AS_USER grant is proved by `proof/runtime/as_user_session.json`. It may only be deferred for a separately scoped local-sidecar tag with explicit owner approval.

---

## External Gate 3: Hermes Proof MCP Transport

**Gate ID:** `hermes_proof_mcp_transport`
**Current status:** BLOCKED
**Proof artifact:** `proof/runtime/hermes-proof-mcp.json` → `proof_mcp.status` embedded under `status: "blocked"`

### What is blocked
No Hermes Proof MCP evidence can be appended for this workspace. `hermes mcp list` returns "No MCP servers configured." The Codex lead-session MCP transport is closed. Even if a locks MCP were active, it must be scoped to `G:\Github\HermesSlicer` — not `G:\Github\Hermes3D` or any other workspace.

### Why it is blocked
Two requirements are both unmet:
1. No MCP stdio server is implemented or registered (`hermes_slicer/mcp_server.py` does not exist).
2. No `hermes mcp add` registration exists for this workspace.

### What IS present (foundation ready)
- `proof/runtime/hermes-proof-mcp.json` correctly reports `blocked` with `workspace_scope_ok: false`
- The workspace scope guard (`expected_workspace_root: "G:\\Github\\HermesSlicer"`) is implemented
- The evidence ledger schema is defined in `proof/PROOF_LEDGER_SCHEMA.json`

### What is required to unblock
1. **Code change required:** Implement `hermes_slicer/mcp_server.py` as a JSON-RPC 2.0 stdio MCP server exposing the 13 bridge actions as tools.
2. Register with Hermes: `hermes mcp add hermes-slicer-proof --command python --args -m hermes_slicer.mcp_server`.
3. Confirm `workspace_root` is set to `G:\Github\HermesSlicer` in the MCP server's evidence assertions.
4. **New script required:** Create `scripts/write_hermes_proof_mcp_live.py` that calls all gate functions and writes a `passed` artifact only when all checks return `ok`.
5. Run the live script after MCP transport is verified: `python scripts\write_hermes_proof_mcp_live.py`.

**Codex correction:** This blocks a full V1 tag until a workspace-scoped Hermes Proof MCP transport proves evidence verification. It may only be deferred for a separately scoped local-sidecar tag with explicit owner approval.

---

## External Gate 4: Hermes Agent Computer-Use Visual Control

**Gate ID:** `hermes_agent_computer_use_visual_control`
**Current status:** BLOCKED (platform constraint)
**Proof artifact:** `proof/runtime/hermes-computer-use.json` → `status: "blocked"`

### What is blocked
Hermes Agent v0.14.0 computer-use (visual control of the desktop via `cua-driver`) is not available on the current Windows host. Visual proof cannot be produced.

### Why it is blocked
- Current platform: Windows
- `cua-driver` is macOS-only
- `cua_driver_installed: false`
- `hermes computer-use status` stdout: `"cua-driver: not installed. Run: hermes computer-use install"`

### V1 design decision
HermesSlicer V1 does not expose computer-use through the slicer bridge. No `computer-use` route exists in `ACTION_ROUTES` or `ALLOWED_ACTIONS`. This is by design: computer-use is powerful, platform-specific, and not required for the V1 proofable local sidecar.

### What is required to unblock (post-V1)
1. macOS host with `cua-driver` installed (`hermes computer-use install`).
2. Bounded AS_USER grant with `visual.inspect` scope (Gate 2 must pass first).
3. Set `HERMES_COMPUTER_USE_VISUAL_PROOF_PATH` to an existing path under `proof/`.
4. Run a visual proof session and capture output to the proof path.
5. Re-run `scripts/write_hermes_computer_use_proof.py`.

**Codex correction:** This blocks a full V1 tag for computer-use claims. It may only be deferred for a separately scoped local-sidecar tag that does not claim computer-use support on this Windows host.

---

## Separation Summary

| Category | Status | Blocks Tag? |
|---|---|---|
| Local implementation | Complete | — |
| Local test suite | Passing | — |
| Local proof bundle (15 files) | Present and valid | No |
| Clean-clone rehearsal | Passed | — |
| Owner acceptance decisions | **MISSING** | Yes for any scoped-deferral tag |
| Live Hermes Agent bridge | Blocked (env only) | Yes for full V1 |
| AS_USER bounded grant | Blocked (env only) | Yes for full V1 |
| Hermes Proof MCP transport | Blocked (code + env) | Yes for full V1 |
| Computer-use visual proof | Blocked (platform) | Yes for full V1 computer-use claims |

**Codex correction:** A full V1 tag is blocked by the live gates above. Owner acceptance can only authorize a narrower local-sidecar tag that explicitly excludes or defers unproved live gates.
