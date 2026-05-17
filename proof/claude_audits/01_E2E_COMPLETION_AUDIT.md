# HermesSlicer V1 — End-to-End Completion Audit
Date: 2026-05-17
Audit Contract: `CLAUDE_AUDIT_CONTRACT.md`

This document audits the full V1 stack layer by layer, from GitHub repository to proof evidence.

---

## Stack Layer Map

```
GitHub repo (main)
    └── Clean-clone rehearsal
        └── Bridge (127.0.0.1:8765)
            ├── Login gate (web/index.html)
            ├── Hermes Agent Tool Console (web/app.js)
            ├── Action dispatch (13 whitelisted actions)
            │   ├── Orca discovery (orca_version, profiles)
            │   ├── FLSUN proof (export_preflight, dry_run)
            │   ├── G-code export (export_gcode — blocked by default)
            │   ├── Proof layer (proof_recent, hermes_proof_mcp)
            │   ├── TTS (tts_speak — stub until Azure)
            │   └── Tool request passthrough (tool_request)
            └── Hermes Agent plugin (hermes_agent_tools)
                └── Hermes Agent CLI v0.14.0 (2026.5.16)
                    ├── Live provider bridge [BLOCKED — external]
                    ├── AS_USER grant [BLOCKED — external]
                    ├── Proof MCP [BLOCKED — external]
                    └── Computer-use [BLOCKED — platform]
```

---

## Layer 1: GitHub Repository

| Item | Status | Notes |
|---|---|---|
| Repo accessible at `https://github.com/Ghenghis/HermesSlicer` | verified | Clean-clone rehearsal confirmed |
| Default branch is `main` | verified | `BRANCHES.md` |
| All submodules pinned and documented | verified | `BASES.md`, `proof/runtime/submodule-stack.json` |
| `upstream/hermes-agent` pinned to v2026.5.16 / 0.14.0 | verified | `proof/runtime/hermes-plugin-smoke.json` |
| Root `LICENSE` (AGPL-3.0) present | verified | `LICENSE` |
| Root `NOTICE` with all upstream attributions | verified | `NOTICE` |
| `pyproject.toml` present | partial | Missing `license` field (P1 gap) |

---

## Layer 2: Clean-Clone Rehearsal

| Step | Status | Evidence |
|---|---|---|
| `git clone --recurse-submodules` | passed | `clean-clone-rehearsal.json` |
| Unit tests | passed | `clean-clone-rehearsal.json` |
| `compileall` | passed | `clean-clone-rehearsal.json` |
| Submodule validation | passed | `clean-clone-rehearsal.json` |
| Proof regeneration | passed | `clean-clone-rehearsal.json` |
| Redaction scan | passed | `clean-clone-rehearsal.json` |
| Duration | ~9m 46s | 2026-05-17T07:28–07:38 |

**Gap:** Rehearsal script does not assert Hermes CLI version before proof regeneration (P2).

---

## Layer 3: HermesSlicer Bridge

| Item | Status | Notes |
|---|---|---|
| Binds to `127.0.0.1` only | verified | `bridge.py` SystemExit guard; `test_bridge_core.py` |
| CORS locked to bind address | verified | Not wildcard `*` |
| `/health` reports `live_connectivity_claimed: false` without HERMES_AGENT_ENABLED | verified | `hermes-proof-mcp.json` |
| 13 actions whitelisted in `ALLOWED_ACTIONS` | verified | `ALLOWED_ACTIONS == ACTION_ROUTES` tested |
| All 13 actions have route handlers | verified | `ACTION_ROUTES` dict |
| `ALLOWED_ACTIONS == ACTION_ROUTES` tested | verified | `tests/test_bridge_core.py` |
| G-code export blocked by default | verified | `HERMES_ENABLE_EXPORT_GCODE` gate |
| No printer-start action | verified | Not in `ACTION_ROUTES` |
| Public-bind test covers `0.0.0.0` | verified | `test_bridge_core.py` |
| Public-bind test covers `::` (IPv6) | **missing** | P2 gap |
| `requestBody` schemas in OpenAPI spec | **missing** | P2 gap |

**Bridge tool proof artifacts:**

| Artifact | Status |
|---|---|
| `proof/runtime/hermes-tool-health.json` | passed |
| `proof/runtime/hermes-tool-export_preflight.json` | passed |
| `proof/runtime/hermes-tool-tool_request.json` | passed |
| `proof/runtime/hermes-tool-tts_speak.json` | **missing** (P2 gap) |

---

## Layer 4: Login Gate and UI

| Item | Status | Notes |
|---|---|---|
| Login visual gate (3 viewports) | passed | `proof/runtime/login-geometry.json` |
| Login asset hash verified | passed | `login-geometry.json` → `asset.sha256` match |
| Forbidden text absent from login source | passed | `source_checks.forbidden_text_absent: true` |
| Login is local-session gate (not OAuth) | verified | `sessionStorage`, no token handling |
| Panel identity: Hermes Agent Tool Console | verified | `<h1>`, `aria-label`, quick-action buttons |
| No slicer-settings chatbot behavior | verified | No settings mutation in `app.js` |
| JusPrin/JusBot/Obico absent from `web/` | verified | `tests/test_ui_static.py` |
| Brand tokens in CSS, config, and tests | verified | `test_css_uses_brand_tokens` |
| All 5 screenshots present (PNG/JPEG valid) | passed | `proof/runtime/screenshot-format.json` |
| Login geometry is rendered-pixel verified | **no** | CSS-math only; no browser pixel check (P2) |
| Screenshots auto-refreshed | **no** | Manually captured; staleness risk (P2) |
| Help overlay for tool IDs | **missing** | P2 gap |
| Voice/mic disabled state when Azure absent | **missing** | P2 gap |

---

## Layer 5: Action Dispatch (13 Actions)

| Action | Status | Notes |
|---|---|---|
| `health` | verified | `hermes-tool-health.json` passed |
| `actions` | verified | Lists all whitelisted actions |
| `profiles` | verified | FLSUN T1/V400/S1 |
| `orca_version` | verified | OrcaSlicer version probe |
| `dry_run` | verified | Slice dry-run |
| `export_preflight` | verified | `hermes-tool-export_preflight.json` passed |
| `export_gcode` | verified (blocked default) | `HERMES_ENABLE_EXPORT_GCODE=1` required |
| `tool_request` | verified | `hermes-tool-tool_request.json` passed |
| `tts_speak` | partial | Route exists; no proof artifact |
| `proof_recent` | verified | Returns ledger entries |
| `hermes_proof_mcp` | blocked | MCP transport closed |
| `agents` | verified | Reads `config/agents.example.json` |
| `voices` | partial | Standalone route; needs OpenAPI clarification |

---

## Layer 6: Hermes Agent Plugin

| Item | Status | Notes |
|---|---|---|
| `.hermes/plugins/hermes-slicer/` wrapper | passed | `action_count: 13`, all flags |
| `integrations/hermes-slicer/` wrapper | passed | Same |
| `integrations/hermes_agent_tool.py` wrapper | passed | Same |
| `isolated_active_project_plugin_harness` | passed | `tools: 1`, `source: project` |
| `HERMES_ENABLE_PROJECT_PLUGINS=1` required | documented | `hermes-plugin-smoke.json` |
| ROOT resolution uses `parents[1]` | partial | Fragile; sentinel-scan recommended (P2) |
| AS_USER gate implementation | verified (blocked) | All security properties implemented; env vars missing |
| Version gate rejects v0.12 | verified (untested) | Logic correct; no unit test (P2) |
| AS_USER TTL expiry | verified (untested) | Logic correct; no unit test (P2) |

---

## Layer 7: Hermes Agent CLI v0.14.0

| Item | Status | Notes |
|---|---|---|
| CLI at `C:\Python314\Scripts\hermes.EXE` | verified | `hermes version` output |
| Points to `upstream/hermes-agent` | verified | `Project: G:\Github\HermesSlicer\upstream\hermes-agent` |
| Version matches expected (`0.14.0 / v2026.5.16`) | verified | `matches_expected: true` |
| No stale v0.12 references in project-owned files | verified | Zero grep matches |
| Live provider bridge | **BLOCKED** | `HERMES_AGENT_ENABLED=1` not set |
| AS_USER grant | **BLOCKED** | 4 env vars absent |
| Hermes Proof MCP | **BLOCKED** | No MCP servers configured |
| Computer-use | **BLOCKED** | Windows platform; macOS-only |

---

## Layer 8: Proof Bundle

| Item | Status | Notes |
|---|---|---|
| All 14 local proof files present | passed | `v1-release-checklist.json` |
| `validate_proof.py` deep-checks 8/14 files | partial | 6 files existence-checked only (P1) |
| Ledger append-only with sanitize | verified | `hermes_slicer/proof.py` |
| Ledger schema enforced on write | **missing** | P2 gap |
| Redaction scan clean | passed | `proof/security/redaction-report.md` |
| `regenerate_proof.ps1` asserts Hermes version | **missing** | P2 gap |
| Standalone AS_USER proof artifact | **missing** | P1 gap |
| `write_hermes_proof_mcp_live.py` script | **missing** | P0 gap |

---

## E2E Completion Score

| Layer | Local Completion | External Gate | Notes |
|---|---|---|---|
| GitHub repo | 100% | — | License field gap in pyproject.toml |
| Clean-clone rehearsal | 100% | — | Version assertion gap in scripts |
| Bridge | 95% | — | Missing IPv6 bind test, requestBody schemas, tts_speak proof |
| Login / UI | 90% | — | Missing pixel render test, help overlay, voice disabled state |
| Action dispatch | 92% | — | tts_speak and voices need proof/clarification |
| Hermes plugin | 90% | — | ROOT resolution fragility, missing AS_USER/version tests |
| Hermes CLI | 100% local | 4 gates blocked | External gates are environment-only (except MCP stdio) |
| Proof bundle | 85% | — | validate_proof gap, missing live-MCP script, missing as_user artifact |
| **Overall** | **~93% local** | **4 blocked** | Tag requires owner decision record |
