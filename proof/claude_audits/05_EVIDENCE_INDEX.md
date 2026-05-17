# HermesSlicer V1 — Evidence Index
Date: 2026-05-17
Audit Contract: `CLAUDE_AUDIT_CONTRACT.md`

All proof artifacts and their gate status as observed during the 2026-05-17 audit.

---

## Runtime Proof Artifacts

| File | Gate | Status | Key Fields |
|---|---|---|---|
| `proof/runtime/hermes-plugin-smoke.json` | Hermes v0.14 + plugin smoke | **passed** | `version.matches_expected: true`, `status: "passed"`, CLI: `v0.14.0 (2026.5.16)` |
| `proof/runtime/hermes-proof-mcp.json` | Hermes Proof MCP + live bridge + AS_USER | **blocked** | `status: "blocked"`, `hermes_agent_bridge.enabled: false`, `proof_mcp.workspace_scope_ok: false` |
| `proof/runtime/hermes-computer-use.json` | Computer-use visual control | **blocked** | `status: "blocked"`, `platform: "Windows"`, `cua_driver_installed: false` |
| `proof/runtime/v1-release-checklist.json` | Tag readiness | **blocked** | `tag_readiness.ready: false`, `local_gates_ready: true`, `clean_clone_rehearsal_passed: true` |
| `proof/runtime/clean-clone-rehearsal.json` | Clean-clone from GitHub main | **passed** | `status: "passed"`, all 6 steps passed, 2026-05-17 |
| `proof/runtime/login-geometry.json` | Login visual/geometry gate | **passed** | `status: "passed"`, `errors: []`, all 3 viewports `full_card_visible: true` |
| `proof/runtime/screenshot-format.json` | Screenshot format validity | **passed** | `status: "passed"`, all 5 screenshots valid PNG/JPEG |
| `proof/runtime/bridge-health.json` | Bridge health + Orca discovery | **passed** | Present, `bytes: 2916` |
| `proof/runtime/proof-validation.json` | Proof bundle validation | **passed** | Present, `bytes: 877` |
| `proof/runtime/hermes-tool-health.json` | `health` action route | **passed** | Present, `bytes: 2916` |
| `proof/runtime/hermes-tool-export_preflight.json` | `export_preflight` action route | **passed** | Present, `bytes: 2275` |
| `proof/runtime/hermes-tool-tool_request.json` | `tool_request` action route | **passed** | Present, `bytes: 2705` |
| `proof/runtime/submodule-stack.json` | Submodule pin integrity | **passed** | `status: "passed"`, `errors: []` |
| `proof/runtime/flsun-profile-inventory.json` | FLSUN T1/V400/S1 profiles | **passed** | Present, `bytes: 2916` |
| `proof/runtime/flsun-export-preflight.json` | FLSUN export preflight | **passed** | Present, `bytes: 2275` |
| `proof/runtime/smoke-report.md` | Bridge smoke report | **passed** | Present, `bytes: 2293` |
| `proof/runtime/hermes-tool-tts_speak.json` | `tts_speak` action route | **MISSING** | Not generated; see QUEUE-15 |

---

## Security Artifacts

| File | Gate | Status | Key Fields |
|---|---|---|---|
| `proof/security/redaction-report.md` | Redaction scan | **passed** | No secrets found in tracked files |
| `proof/ledger.jsonl` | Proof ledger | **valid** | 52 events, append-only, all sanitized |

---

## Screenshots

| File | Gate | Status |
|---|---|---|
| `proof/screenshots/login-hermes-slicer.jpg` | Login artwork | **present** — JPEG valid |
| `proof/screenshots/hermes-agent-tools.jpg` | Tool console state | **present** — JPEG valid |
| `proof/screenshots/panel-open.png` | Panel open state | **present** — PNG valid |
| `proof/screenshots/panel-hidden.png` | Panel hidden state | **present** — PNG valid |
| `proof/screenshots/panel-flsun.png` | FLSUN proof view | **present** — PNG valid |
| `proof/screenshots/computer-use-blocked.png` | Computer-use blocked state | **MISSING** — see QUEUE-25 |

---

## Source Files Audited (Read-Only)

| File | Audit Domain |
|---|---|
| `hermes_slicer/bridge.py` | Runtime Wiring |
| `hermes_slicer/config.py` | Hermes Gate, Runtime Wiring |
| `hermes_slicer/proof.py` | Proof and MCP |
| `hermes_slicer/security.py` | Hermes Gate |
| `hermes_slicer/slicer.py` | Runtime Wiring, UI |
| `hermes_slicer/voices.py` | Runtime Wiring |
| `hermes_slicer/__init__.py` | Runtime Wiring |
| `integrations/hermes_agent_tool.py` | Runtime Wiring, Hermes Gate |
| `integrations/hermes-slicer/plugin.yaml` | Runtime Wiring |
| `integrations/hermes-slicer/__init__.py` | Runtime Wiring |
| `integrations/hermes_plugin.yaml` | Runtime Wiring |
| `.hermes/plugins/hermes-slicer/plugin.yaml` | Runtime Wiring |
| `.hermes/plugins/hermes-slicer/__init__.py` | Runtime Wiring |
| `api_contract.openapi.yaml` | Runtime Wiring |
| `web/index.html` | UI and Product |
| `web/app.js` | UI and Product |
| `web/styles.css` | UI and Product |
| `config/brand_tokens.json` | UI and Product |
| `config/agents.example.json` | Runtime Wiring |
| `pyproject.toml` | Release Completion |
| `LICENSE` | Release Completion |
| `NOTICE` | Release Completion |
| `ROADMAP.md` | Release Completion |
| `ACTION_PLAN.md` | Release Completion |
| `TASKS.md` | Release Completion |
| `V1_STATUS.md` | All agents |
| `V1_RELEASE_CHECKLIST.md` | Release Completion |
| `BASES.md` | Release Completion |
| `BRANCHES.md` | Release Completion |
| `PLAN.md` | Release Completion |
| `BRAND.md` | UI and Product |

---

## Test Files Audited

| File | Coverage Domain |
|---|---|
| `tests/test_bridge_core.py` | Bridge bind, action routing, CORS, health |
| `tests/test_hermes_integration.py` | Plugin wiring, hermes_agent_bridge_gate, proof MCP |
| `tests/test_proof_validation.py` | Proof file existence and basic validation |
| `tests/test_submodule_stack.py` | Submodule pin and integrity |
| `tests/test_ui_static.py` | Branding, CSS tokens, forbidden text, login form |
| `tests/test_api_contract.py` | OpenAPI spec drift |

---

## Script Files Audited

| File | Purpose |
|---|---|
| `scripts/smoke_hermes_plugin.py` | Plugin smoke runner |
| `scripts/write_hermes_proof_mcp_status.py` | MCP status proof writer |
| `scripts/write_hermes_computer_use_proof.py` | Computer-use proof writer |
| `scripts/validate_proof.py` | Proof bundle validator |
| `scripts/redaction_scan.py` | Secret scanner |
| `scripts/regenerate_proof.ps1` | Proof regeneration orchestrator |
| `scripts/clean_clone_rehearsal.ps1` | Clean-clone rehearsal runner |
| `scripts/verify_login_geometry.py` | Login layout gate |
| `scripts/verify_screenshots.py` | Screenshot format gate |
| `scripts/write_v1_release_checklist.py` | Release checklist generator |
| `scripts/validate_submodules.py` | Submodule pin validator |

---

## Research Documents Reviewed

| File | Domain |
|---|---|
| `proof/research/floating_panel_report.md` | UI architecture |
| `proof/research/jusprin_pattern_report.md` | JusPrin pattern analysis |
| `proof/research/jusprin_file_map.md` | JusPrin file inventory |
| `proof/research/hermes_agent_file_map.md` | Hermes Agent file inventory |
| `proof/research/hermes_extension_report.md` | Extension research |
| `proof/research/azure_voices_report.md` | TTS research |
| `proof/research/private_data_report.md` | Privacy research |
| `proof/research/submodule_stack_review.md` | Submodule review |
| `proof/mcp_binding_report.md` | MCP binding analysis |
| `proof/orchestrator_decisions.md` | Orchestration decisions |

---

## Proof Ledger Schema

| File | Status |
|---|---|
| `proof/PROOF_LEDGER_SCHEMA.json` | Present — 3 required fields: `timestamp`, `action`, `result` |
| Schema enforcement on writes | **MISSING** — see QUEUE-18 |

---

## Gate Status Summary

| Gate ID | Status | Local or External |
|---|---|---|
| `hermes_v014_version` | passed | local |
| `hermes_slicer_plugin_smoke` | passed | local |
| `bridge_bind_localhost` | passed | local |
| `action_dispatch_whitelist` | passed | local |
| `gcode_export_blocked_default` | passed | local |
| `login_geometry_3_viewports` | passed | local |
| `screenshot_format_valid` | passed | local |
| `jusprin_reframe_complete` | passed | local |
| `brand_tokens_in_css` | passed | local |
| `api_contract_drift` | passed | local |
| `local_proof_bundle_complete` | passed | local |
| `submodule_pins_clean` | passed | local |
| `redaction_scan_clean` | passed | local |
| `clean_clone_rehearsal` | passed | local |
| `live_hermes_agent_provider_bridge` | **blocked** | external |
| `bounded_as_user_grants` | **blocked** | external |
| `hermes_proof_mcp_transport` | **blocked** | external |
| `hermes_agent_computer_use_visual_control` | **blocked** | external (platform) |

**Local gates: 14/14 passed. External gates: 0/4 passed.**
