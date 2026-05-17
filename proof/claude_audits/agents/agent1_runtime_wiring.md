# Agent 1: Runtime Wiring Audit Report
Date: 2026-05-17
Auditor: Claude Agent (runtime-wiring)

## 1. Summary

The HermesSlicer V1 runtime wiring is structurally sound for local operation. The bridge binds exclusively to `127.0.0.1`, all 13 whitelisted actions are implemented and tested, CORS is locked to the runtime bind address, and all three Hermes plugin wrappers register an identical `hermes_agent_tools` toolset. G-code export is blocked by default; printer start is not implemented. All bridge-facing proof artifacts (`hermes-tool-health.json`, `hermes-tool-export_preflight.json`, `hermes-tool-tool_request.json`) report `passed`. One routing gap exists: the `voices` / `tts_speak` action path through the plugin is not yet backed by a matching proof artifact. A `voices.azure.en` action may be missing from the whitelist. The most significant remaining gap is the absence of an MCP stdio server, which is a P1 post-V1 item required before the Hermes Proof MCP transport gate can pass.

---

## 2. Bridge Endpoints

## P3: Bridge Endpoint Whitelist — Verified Complete
- Status: verified complete
- Evidence: `hermes_slicer/bridge.py` — `ALLOWED_ACTIONS` set matches `ACTION_ROUTES` dict exactly; `tests/test_bridge_core.py` asserts this equality. All 13 actions confirmed.
- Why it matters: No undocumented actions can be dispatched.
- Codex next action: None. Maintain the equality assertion in tests.
- Release impact: documentation only — gate passes.

## P3: Bridge Bind Address — Verified Localhost-Only
- Status: verified complete
- Evidence: `hermes_slicer/bridge.py` — `SystemExit` guard on bind attempts to `0.0.0.0` or any non-127 address. `tests/test_bridge_core.py::test_bridge_bind_address` covers this.
- Why it matters: Prevents public exposure of the local sidecar.
- Codex next action: Add parameterized test cases for `::` (IPv6 loopback) and `192.168.x.x` (LAN bind) to close edge case gaps.
- Release impact: documentation only — current gate passes.

## P3: CORS Origin Locked to Runtime Bind Address
- Status: verified complete
- Evidence: `hermes_slicer/bridge.py` — `Access-Control-Allow-Origin` set to the bound address string, not `*`.
- Why it matters: Prevents cross-origin CSRF from other tabs or local apps.
- Codex next action: None.
- Release impact: documentation only — gate passes.

## P2: `/health` Does Not Claim Live Connectivity Without HERMES_AGENT_ENABLED=1
- Status: verified complete
- Evidence: `proof/runtime/hermes-proof-mcp.json` → `hermes_agent_bridge.live_connectivity_claimed: false`. `hermes_slicer/config.py::hermes_agent_bridge_gate()` checks `HERMES_AGENT_ENABLED` first.
- Why it matters: Prevents false live-agent claims in the health response.
- Codex next action: None. Gate is correctly implemented.
- Release impact: documentation only.

## P2: Missing `requestBody` Schemas on POST Endpoints in OpenAPI Spec
- Status: open — needs Codex implementation
- Evidence: `api_contract.openapi.yaml` — POST endpoints (`/api/action`, `/api/action/batch`) do not define `requestBody` schemas; request body shape must be inferred from `bridge.py`.
- Why it matters: API consumers and tools (Swagger UI, code generators) cannot validate request bodies. Drift between bridge and spec is undetectable.
- Codex next action: Add `requestBody` with `application/json` schema objects for `action`, `payload`, and any required fields to all POST endpoints in `api_contract.openapi.yaml`. Re-run `tests/test_api_contract.py` to confirm drift detection.
- Release impact: polish — does not block V1 tag.

---

## 3. Action Dispatch

## P3: G-code Export Blocked by Default — Verified
- Status: verified complete
- Evidence: `hermes_slicer/slicer.py` line ~576 — `export_gcode` checks `HERMES_ENABLE_EXPORT_GCODE` before proceeding; returns a `blocked` response if unset. No printer-start action exists in `ACTION_ROUTES`.
- Why it matters: Prevents accidental G-code export or printer start without operator opt-in.
- Codex next action: None. Document this env var in README/CONTRIBUTING.
- Release impact: documentation only — gate passes.

## P2: `voices.azure.en` May Be Missing From ALLOWED_ACTIONS
- Status: open — needs Codex verification
- Evidence: `hermes_slicer/bridge.py` — `ACTION_ROUTES` does not clearly list a `voices` or `voices.azure.en` key. `web/app.js` fetches `/api/voices/azure/en` at startup. `proof/research/hermes_agent_file_map.md` mentions `voices.azure.en` action.
- Why it matters: If the voices fetch URL is not a standard action route (e.g., handled via a dedicated endpoint rather than the action dispatch table), this inconsistency could confuse consumers of the OpenAPI spec.
- Codex next action: Confirm whether `voices.azure.en` is handled as a standalone route or dispatched through `ACTION_ROUTES`. If standalone, add a dedicated path to the OpenAPI spec. If dispatch, add to `ALLOWED_ACTIONS` and `ACTION_ROUTES`.
- Release impact: polish — voice feature is a V2 item.

## P2: Unhandled Action Fallback Risk in `dispatch_action()`
- Status: open — needs Codex verification
- Evidence: If `action` is not in `ALLOWED_ACTIONS`, the bridge currently returns a 400-level error. However, the 500 path for unexpected exceptions in `dispatch_action()` may not distinguish unhandled action names from runtime errors.
- Why it matters: A caller passing an unknown action name should receive a clear 400/404 with the allowed actions list, not a generic 500.
- Codex next action: Confirm the error response schema for unknown actions is `{"status": "blocked", "allowed": [...]}` with HTTP 400, not 500. Add a test for this path.
- Release impact: polish — does not block V1 tag.

## P2: `agents.save` Action Not Documented in Whitelist
- Status: open — needs Codex clarification
- Evidence: `config/agents.example.json` describes an `agents.save` config but it is unclear whether this maps to an action in `ALLOWED_ACTIONS`.
- Why it matters: If agents configuration must be saved via bridge dispatch, the action must be in the whitelist. If not, the config path is config-file-only (acceptable).
- Codex next action: Clarify in comments whether agent config is file-only or bridgeable. If bridgeable, add `agents.save` to `ALLOWED_ACTIONS`, `ACTION_ROUTES`, and `hermes_agent_tool.py`.
- Release impact: documentation only.

---

## 4. Hermes Plugin Wrapper

## P3: All Three Plugin Wrappers — Verified Consistent
- Status: verified complete
- Evidence: `proof/runtime/hermes-plugin-smoke.json` — `committed_project_plugin`, `committed_project_plugin_cwd_fallback`, and `integration_plugin` all report `status: "passed"`, `action_count: 13`, `has_export_preflight: true`, `has_hermes_proof_mcp: true`, `handler_callable: true`.
- Why it matters: No wrapper divergence; all three install paths are equivalent.
- Codex next action: Add a CI assertion that `action_count >= 13` across all three wrappers to catch regressions.
- Release impact: documentation only — gate passes.

## P2: ROOT Resolution Uses `parents[1]` — Fragile Path
- Status: open — needs Codex improvement
- Evidence: `integrations/hermes_agent_tool.py` resolves `HERMES_SLICER_ROOT` via `Path(__file__).parents[1]` as cwd fallback. If the integration is ever symlinked or installed in a non-standard location, this breaks silently.
- Why it matters: Unexpected `HERMES_SLICER_ROOT` points the tool router at the wrong repo.
- Codex next action: Replace `parents[1]` fallback with a sentinel-file scan (walk up from `__file__` until `pyproject.toml` or `.hermes/` is found). Log the resolved root at import time for debugging.
- Release impact: polish — cwd fallback currently works in all tested configurations.

---

## 5. Local Tool Routing

## P3: All 13 Actions Routable — Verified
- Status: verified complete
- Evidence: `proof/runtime/hermes-plugin-smoke.json` → `action_count: 13`. The 13 actions: `health`, `actions`, `profiles`, `orca_version`, `dry_run`, `export_preflight`, `export_gcode`, `tool_request`, `tts_speak`, `proof_recent`, `hermes_proof_mcp`, `agents`, `voices`.
- Why it matters: Plugin exposes all documented bridge actions.
- Codex next action: None.
- Release impact: documentation only.

## P1: MCP stdio Server Not Implemented (Post-V1 Blocker)
- Status: open — needs Codex implementation (post-V1)
- Evidence: `ROADMAP.md` P1 section: "Add a true MCP stdio server backed by `upstream/mcp-python-sdk`." No `hermes_slicer/mcp_server.py` or equivalent exists. `proof/runtime/hermes-proof-mcp.json` → `proof_mcp.active_hermes_mcp_configured: false`; `hermes mcp list` returns "No MCP servers configured."
- Why it matters: Without an MCP stdio server, the Hermes Proof MCP transport gate cannot pass. This is the only code-level path to unblocking that gate.
- Codex next action: Implement `hermes_slicer/mcp_server.py` as a JSON-RPC 2.0 stdio MCP server exposing the 13 bridge actions as tools. Register it via `hermes mcp add hermes-slicer --command python --args -m hermes_slicer.mcp_server`. Document the required `workspace_root` assertion. Add to `pyproject.toml` entry points.
- Release impact: blocks Hermes Proof MCP live feature; does not block V1 local tag.

---

## 6. Proof Artifacts

## P3: Bridge Tool Proof Artifacts — All Passed
- Status: verified complete
- Evidence: `proof/runtime/hermes-tool-health.json` → `status: "passed"`. `proof/runtime/hermes-tool-export_preflight.json` → `status: "passed"`. `proof/runtime/hermes-tool-tool_request.json` → `status: "passed"`.
- Why it matters: Confirms the bridge tool dispatch responded correctly at proof time.
- Codex next action: None. Re-run `scripts/regenerate_proof.ps1` after any bridge change.
- Release impact: documentation only.

## P2: No Proof Artifact for `tts_speak` or `voices`
- Status: open — missing artifact
- Evidence: The 14 local proof files listed in `v1-release-checklist.json` do not include a `hermes-tool-tts_speak.json` or `hermes-tool-voices.json`. The `tts_speak` route exists in `ACTION_ROUTES` but has no proof run.
- Why it matters: TTS functionality is unproved at the tool-dispatch level. A regression in the Azure voice path would not be caught by existing proof artifacts.
- Codex next action: Add `scripts/write_hermes_tool_tts_speak_proof.py` that calls the `tts_speak` action (returning `blocked` if Azure credentials absent) and writes `proof/runtime/hermes-tool-tts_speak.json`. Add to `scripts/regenerate_proof.ps1` and `proof/runtime/v1-release-checklist.json`.
- Release impact: polish — does not block V1 tag.

---

## 7. Improvements and Enhancements Needed

## P2: Add `requestBody` to OpenAPI POST Endpoints
- See section 2 above.

## P2: Add Parameterized Bind Tests (`::`, `192.168.x.x`)
- Status: open — missing coverage
- Evidence: `tests/test_bridge_core.py::test_bridge_bind_address` only tests `0.0.0.0`. IPv6 and LAN cases are uncovered.
- Codex next action: Parameterize the test with `["0.0.0.0", "::", "192.168.1.1"]` to confirm all non-loopback addresses are rejected.
- Release impact: polish.

## P2: Add Proof Artifact for `tts_speak`
- See section 6 above.

## P1: MCP stdio Server Implementation
- See section 5 above.

---

## 8. Missing / Not Included

| Item | Priority | Notes |
|------|----------|-------|
| MCP stdio server (`hermes_slicer/mcp_server.py`) | P1 | Required to unblock Hermes Proof MCP transport |
| `requestBody` schemas in OpenAPI spec | P2 | Required for accurate API contract drift detection |
| `hermes-tool-tts_speak.json` proof artifact | P2 | Proves `tts_speak` action routing |
| IPv6 / LAN bind prevention tests | P2 | Closes edge case in public-bind gate |
| `voices.azure.en` action route clarification | P2 | Confirm standalone vs dispatch table |
| `agents.save` whitelist clarification | P3 | Confirm file-only vs bridgeable |
| Proof artifact for `voices` route | P3 | Low priority; voice is a V2 feature |

---

## 9. Codex Next Actions (Ranked)

1. **[Unblocks Hermes Proof MCP gate — P1]** Implement `hermes_slicer/mcp_server.py` as JSON-RPC 2.0 stdio MCP server, register with `hermes mcp add`, add to pyproject entry points and regenerate_proof.ps1.
2. **[Closes API spec gap — P2]** Add `requestBody` schemas to POST endpoints in `api_contract.openapi.yaml`; re-run `tests/test_api_contract.py`.
3. **[Closes proof gap — P2]** Add `scripts/write_hermes_tool_tts_speak_proof.py` and `proof/runtime/hermes-tool-tts_speak.json`.
4. **[Closes security test gap — P2]** Add parameterized bind-address test covering `::` and `192.168.x.x`.
5. **[Hardening — P2]** Replace `parents[1]` ROOT resolution with sentinel-file scan in `integrations/hermes_agent_tool.py`.
6. **[Clarification — P2]** Confirm `voices.azure.en` route handling; update OpenAPI spec or dispatch table as needed.
7. **[Clarification — P3]** Document `agents.save` as file-only config or add to dispatch table.
