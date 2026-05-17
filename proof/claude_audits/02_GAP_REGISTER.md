# HermesSlicer V1 — Gap Register
Date: 2026-05-17
Audit Contract: `CLAUDE_AUDIT_CONTRACT.md`

All actionable findings from the 5 audit agents, deduplicated and ranked.

---

## P0 — Blocks Truthful V1 Completion or Can Cause Unsafe/False Claims

## P0-01: No Owner Acceptance Decision Record for Blocked External Gates

- Status: open — needs Codex implementation
- Evidence: `V1_RELEASE_CHECKLIST.md` states "Do not tag V1 until external live-agent, AS_USER, MCP, and computer-use gates are proved or explicitly accepted as release-blocking owner decisions." No `## Owner Acceptance Decisions` section exists in that file. `proof/runtime/v1-release-checklist.json` → `tag_readiness.ready: false`.
- Why it matters: The V1 tag cannot be created truthfully without either satisfying the 4 external gates OR recording an explicit owner acceptance decision with rationale for each one. Without this record, the tag would be a false completion claim.
- Codex next action: Add `## Owner Acceptance Decisions` section to `V1_RELEASE_CHECKLIST.md` with one entry per blocked gate: gate ID, rationale for accepting as release-blocking owner decision, owner name, and date. Update `scripts/write_v1_release_checklist.py` to check for this section and write `owner_decisions_recorded: true` to the JSON. Re-run the script.
- Release impact: **blocks tag**

## P0-02: No Script to Write a Live (Passing) Hermes Proof MCP Artifact

- Status: open — needs Codex implementation
- Evidence: `scripts/write_hermes_proof_mcp_status.py` always writes a `blocked` artifact based on current env state. No `write_hermes_proof_mcp_live.py` script exists. Even when the MCP transport opens and all env vars are set, there is no code path to produce a `passed` `hermes-proof-mcp.json`.
- Why it matters: The Hermes Proof MCP gate cannot transition from `blocked` to `passed` without this script. Codex cannot close this gate with environment variables alone.
- Codex next action: Create `scripts/write_hermes_proof_mcp_live.py` that: (1) calls `hermes_agent_bridge_gate()`, (2) calls `hermes_mcp_transport_gate()` with `workspace_root=G:\Github\HermesSlicer`, (3) calls `as_user_session_gate()`, (4) calls `hermes_verify_evidence()` via the active MCP tool, (5) writes `proof/runtime/hermes-proof-mcp.json` with `status: "passed"` only when all checks return `ok`. This script must NOT be added to `regenerate_proof.ps1`; it requires a confirmed live environment.
- Release impact: **blocks live MCP gate** — does not block V1 local tag

---

## P1 — Important Gap That Should Be Fixed Before V1 Tag

## P1-01: validate_proof.py Deep-Checks Only 8 of 14 Proof Files

- Status: open — needs Codex implementation
- Evidence: `scripts/validate_proof.py` deep-validates 8 files. The following 6 are only existence-checked: `hermes-tool-health.json`, `hermes-tool-export_preflight.json`, `hermes-tool-tool_request.json`, `flsun-profile-inventory.json`, `flsun-export-preflight.json`, `screenshot-format.json`.
- Why it matters: A tool-dispatch proof file containing `"status": "failed"` would pass the validation gate silently.
- Codex next action: Add deep-validation blocks for the 6 unchecked files. At minimum: assert `"status"` field exists and equals `"passed"`. Add corresponding tests in `tests/test_proof_validation.py`.
- Release impact: **polish** — closes a silent-failure gap; does not block V1 tag

## P1-02: No Standalone AS_USER Session Proof Artifact

- Status: open — needs Codex implementation
- Evidence: AS_USER gate status is embedded inside `proof/runtime/hermes-proof-mcp.json` only. No `proof/runtime/as_user_session.json` artifact exists.
- Why it matters: Independent verification of the AS_USER gate requires parsing the composite MCP artifact. A standalone artifact would allow the gate to be proved independently of the MCP transport gate.
- Codex next action: Create `scripts/write_as_user_session_proof.py` that calls `as_user_session_gate()` and writes `proof/runtime/as_user_session.json`. Add to `scripts/regenerate_proof.ps1` and `proof/runtime/v1-release-checklist.json` expected files list.
- Release impact: **polish** — does not block V1 tag

## P1-03: `pyproject.toml` Missing `license` Field

- Status: open — needs Codex implementation
- Evidence: `pyproject.toml` — no `license` key in `[project]` table. `LICENSE` file exists and is AGPL-3.0.
- Why it matters: Required before any public package distribution. Automated tooling (PyPI, pip VCS install) may not recognize the license without this field.
- Codex next action: Add `license = {text = "AGPL-3.0-only"}` to the `[project]` table in `pyproject.toml`.
- Release impact: **polish for local V1** — blocks public package distribution

## P1-04: ROADMAP.md P0 Gate 5 Plugin-Enable Phrasing Is Stale

- Status: open — stale documentation
- Evidence: ROADMAP.md P0 gate 5 uses conditional future phrasing ("With an active Hermes install: `hermes plugins enable hermes-slicer`") but the proof JSON shows it already enabled (`enabled: true`).
- Why it matters: A reviewer checking gate status could misread this as an outstanding action item.
- Codex next action: Update ROADMAP.md P0 gate 5 block to past-confirmed phrasing: "Confirmed active: `hermes-slicer` is enabled per `proof/runtime/hermes-plugin-smoke.json`."
- Release impact: documentation only

---

## P2 — Useful Improvement or Missing Regression Coverage

## P2-01: MCP stdio Server Not Implemented

- Status: open — needs Codex implementation (post-V1)
- Evidence: No `hermes_slicer/mcp_server.py`. `hermes mcp list` = "No MCP servers configured." `proof/runtime/hermes-proof-mcp.json` → `active_hermes_mcp_configured: false`.
- Why it matters: Without an MCP stdio server, the Hermes Proof MCP transport gate cannot pass. This is the only code-level path to unblocking that gate.
- Codex next action: Implement `hermes_slicer/mcp_server.py` as a JSON-RPC 2.0 stdio MCP server exposing the 13 bridge actions as tools. Add `python -m hermes_slicer.mcp_server` entry point to `pyproject.toml`. Register with `hermes mcp add hermes-slicer-proof --command python --args -m hermes_slicer.mcp_server`.
- Release impact: **blocks Hermes Proof MCP live feature** — does not block V1 local tag

## P2-02: Missing `requestBody` Schemas on POST Endpoints in OpenAPI Spec

- Status: open — needs Codex implementation
- Evidence: `api_contract.openapi.yaml` — POST endpoints (`/api/action`, `/api/action/batch`) have no `requestBody` schemas.
- Why it matters: API drift tests cannot detect changes to request body shape. Code generators produce incomplete client code.
- Codex next action: Add `requestBody` with `application/json` schema objects for `action`, `payload`, and required fields to all POST endpoints. Re-run `tests/test_api_contract.py`.
- Release impact: polish

## P2-03: Missing Proof Artifact for `tts_speak` Action

- Status: open — missing artifact
- Evidence: No `proof/runtime/hermes-tool-tts_speak.json`. The `tts_speak` route exists in `ACTION_ROUTES` but has no proof run.
- Why it matters: TTS functionality is unproved at the tool-dispatch level. A regression in the Azure voice path would not be caught.
- Codex next action: Add `scripts/write_hermes_tool_tts_speak_proof.py` that calls the `tts_speak` action (returning `blocked` if Azure credentials absent) and writes `proof/runtime/hermes-tool-tts_speak.json`. Add to `scripts/regenerate_proof.ps1`.
- Release impact: polish

## P2-04: `regenerate_proof.ps1` Does Not Assert Hermes CLI Version

- Status: open — missing guard
- Evidence: `scripts/regenerate_proof.ps1` does not call `hermes version` and assert `v0.14.0 (2026.5.16)` before running proof writers.
- Why it matters: A stale Hermes install would produce proof artifacts tied to the wrong version without failing the script.
- Codex next action: Add `hermes version` assertion at the top of `scripts/regenerate_proof.ps1`. Fail fast if version string does not match `v0.14.0 (2026.5.16)`.
- Release impact: polish — closes version-staleness hole

## P2-05: `clean_clone_rehearsal.ps1` Does Not Assert Hermes CLI Version

- Status: open — missing guard
- Evidence: `scripts/clean_clone_rehearsal.ps1` does not verify the Hermes CLI version in the clean clone environment before running proof regeneration.
- Why it matters: A CI or developer machine with a stale Hermes install could produce stale proof artifacts without failing the rehearsal.
- Codex next action: Add `hermes version` assertion step after clone, before proof regeneration. Fail the rehearsal if version does not match.
- Release impact: polish — closes cross-machine reproducibility gap

## P2-06: No Staleness Check on Clean-Clone Artifact in Release Checklist

- Status: open — missing check
- Evidence: `V1_RELEASE_CHECKLIST.md` reports `clean_clone_rehearsal_passed: yes` but does not assert when the rehearsal was run.
- Why it matters: A rehearsal artifact from a stale branch state could give false confidence.
- Codex next action: Add staleness check in `scripts/write_v1_release_checklist.py` — if `clean-clone-rehearsal.json::started_at` is more than 7 days before today, report `clean_clone_rehearsal_stale: true`.
- Release impact: polish

## P2-07: Missing Test — AS_USER TTL Edge Cases Not Unit-Tested

- Status: open — needs Codex implementation
- Evidence: No test for past-expiry timestamp, exactly-15-minute TTL (boundary), 16-minute TTL (should block), or malformed timestamp string in the AS_USER gate.
- Why it matters: TTL expiry is a security property. A regression in `_parse_utc_datetime()` or TTL comparison would be undetected.
- Codex next action: Add `AsUserSessionGateTests` covering: all vars absent, expired timestamp, TTL > 900s, TTL = 900s exactly, empty scopes, valid grant.
- Release impact: polish — closes security test gap

## P2-08: Missing Test — Hermes v0.12 Version Gate Rejection

- Status: open — needs Codex implementation
- Evidence: No test feeds `version: "0.12.0"` to the version gate and confirms `matches_expected: false`.
- Why it matters: A prefix-match bug could allow a stale v0.12 install to pass the gate.
- Codex next action: Add `ParseHermesVersionTests` covering v0.12.0 rejection, v0.14.0 acceptance, v0.14.1 rejection (exact match), malformed string.
- Release impact: polish — closes version gate test gap

## P2-09: Missing Test — Public-Bind Prevention for IPv6 (`::`) and LAN

- Status: open — needs Codex implementation
- Evidence: `tests/test_bridge_core.py` only tests `0.0.0.0`. IPv6 all-interfaces (`::`) and LAN addresses (`192.168.x.x`) are not covered.
- Why it matters: A regression allowing `::` would expose the bridge on IPv6 without detection.
- Codex next action: Parameterize public-bind test with `["0.0.0.0", "::", "192.168.1.1"]`.
- Release impact: polish — closes edge-case security test gap

## P2-10: Proof Ledger Schema Not Enforced on Write

- Status: open — needs Codex implementation
- Evidence: `proof/PROOF_LEDGER_SCHEMA.json` defines the schema but `hermes_slicer/proof.py::record_event()` does not validate against it.
- Why it matters: An invalid entry (missing timestamp, null action) would be silently accepted.
- Codex next action: Add `jsonschema.validate(entry, LEDGER_SCHEMA)` in `record_event()` before the write. Add test for schema rejection.
- Release impact: polish

## P2-11: Proof Ledger Tamper-Detection Tests Minimal

- Status: open — needs Codex implementation
- Evidence: `tests/test_proof_validation.py` has only 1 test. No tests for null timestamp, missing action field, or schema violation.
- Why it matters: A tampered ledger entry would not be caught by the current test suite.
- Codex next action: Add 4 tests: valid entry passes, null timestamp fails, missing action field fails, extra secret field is redacted before write.
- Release impact: polish

## P2-12: MCP stdio Server P1 Item Underdefined in ROADMAP

- Status: open — documentation gap
- Evidence: ROADMAP.md P1: "Add a true MCP stdio server backed by `upstream/mcp-python-sdk`." No protocol, tool list, entry point, or test strategy specified.
- Why it matters: Codex cannot implement this without a design note.
- Codex next action: Add design note to ROADMAP.md P1: "stdio JSON-RPC 2.0 transport, 13 bridge actions as tools, entry point `python -m hermes_slicer.mcp_server`."
- Release impact: documentation only

## P2-13: Azure TTS P1 Item Should Reference Existing Gate

- Status: open — stale description
- Evidence: `tts_speak` action already exists in `bridge.py` and `hermes_agent_tool.py`. The P1 item implies it needs to be built.
- Why it matters: Codex might build a duplicate implementation.
- Codex next action: Update ROADMAP.md P1 Azure TTS item to reference the existing action and specify remaining work.
- Release impact: documentation only

## P2-14: ROOT Resolution in `hermes_agent_tool.py` Uses Fragile `parents[1]`

- Status: open — needs Codex improvement
- Evidence: `integrations/hermes_agent_tool.py` resolves `HERMES_SLICER_ROOT` via `Path(__file__).parents[1]` as cwd fallback. If the integration is symlinked or installed non-standard, this breaks silently.
- Why it matters: Unexpected `HERMES_SLICER_ROOT` points the tool router at the wrong repo.
- Codex next action: Replace `parents[1]` fallback with a sentinel-file scan (walk up from `__file__` until `pyproject.toml` or `.hermes/` is found).
- Release impact: polish

## P2-15: Screenshots Are Manually Captured; No Auto-Refresh

- Status: open — process gap
- Evidence: `proof/screenshots/README.md` — "Captured with the Codex in-app browser on 2026-05-16." `verify_screenshots.py` only checks existence and format.
- Why it matters: Screenshots silently become stale after UI changes.
- Codex next action: Add a Playwright capture step in `scripts/capture_screenshots.py`. Gate the release checklist on screenshot freshness (mtime within 7 days of latest commit).
- Release impact: polish

## P2-16: No Help Overlay for Tool IDs in Panel

- Status: open — missing feature
- Evidence: `web/index.html` has no help overlay or onboarding for first-run users.
- Why it matters: Users unfamiliar with tool IDs see quick-action buttons with no explanation.
- Codex next action: Add collapsible "?" help section listing available tool IDs with descriptions, driven by the `bridge.actions` response.
- Release impact: polish

## P2-17: Voice/Mic Buttons Have No Disabled State When Azure Absent

- Status: open — missing UX state
- Evidence: Mic and stop buttons are visually active even when Azure credentials are absent.
- Why it matters: Users may click mic and see no response with no explanation.
- Codex next action: On bridge health check, if `/api/voices/azure/en` returns empty list or error, add `disabled` + `title="Azure credentials not configured"` to the mic button.
- Release impact: polish

## P2-18: No CONTRIBUTING.md

- Status: open — missing doc
- Evidence: No `CONTRIBUTING.md` in the project root.
- Why it matters: No developer setup path from clone to running panel.
- Codex next action: Create `CONTRIBUTING.md` covering prerequisites, install, bridge startup, panel URL, test run, and proof screenshot checkpoints.
- Release impact: documentation only

## P2-19: No CHANGELOG.md

- Status: open — missing doc
- Evidence: No `CHANGELOG.md` or `CHANGES.md` found.
- Why it matters: V1 has no release notes.
- Codex next action: Create `CHANGELOG.md` with a V1 entry listing local gates completed, external gates blocked, and date.
- Release impact: documentation only

---

## P3 — Polish, Naming, Documentation, or Nice-to-Have

## P3-01: No Architecture Diagram in README

- Status: open — missing artifact
- Codex next action: Add the Mermaid diagram from `proof/claude_audits/agents/agent5_release_completion.md` Section 11 to `README.md`.
- Release impact: documentation only

## P3-02: Screenshot Filename Manifest Hardcoded in verify_screenshots.py

- Status: open — maintenance gap
- Codex next action: Consider a glob-based approach checking all `proof/screenshots/*.{png,jpg}` files.
- Release impact: documentation only

## P3-03: No Computer-Use Blocked Screenshot

- Status: open — missing artifact
- Codex next action: Add `proof/screenshots/computer-use-blocked.png` showing the panel message when computer-use is unavailable. Update `scripts/verify_screenshots.py` `SCREENSHOTS` list.
- Release impact: documentation only

## P3-04: No Clean-Clone Rehearsal Freshness Assertion in Tests

- Status: open — minor gap
- Codex next action: Add `test_clean_clone_rehearsal_passed()` in `tests/test_proof_validation.py`.
- Release impact: documentation only

## P3-05: No Floating Panel Position Test

- Status: open — missing gate
- Codex next action: Add a Playwright test verifying `clampPanel()` keeps the panel within viewport bounds at the three reference viewport sizes.
- Release impact: polish

## P3-06: `voices.azure.en` Route Clarification Needed

- Status: open — clarification needed
- Codex next action: Confirm whether `voices.azure.en` is a standalone route or in `ACTION_ROUTES`. Update OpenAPI spec accordingly.
- Release impact: documentation only

## P3-07: No Workspace Scope Rejection Test for MCP

- Status: open — minor gap
- Codex next action: Add a test that passes `workspace_root=G:\Github\Hermes3D` to the workspace scope gate and asserts `workspace_scope_ok: false`.
- Release impact: documentation only

## P3-08: No Pre-Commit Hook for Redaction Scan

- Status: open — nice-to-have
- Codex next action: Add pre-commit hook that runs `scripts/redaction_scan.py` before each commit.
- Release impact: documentation only

## P3-09: README.md Developer Setup Coverage Unknown

- Status: open — needs verification
- Codex next action: Read `README.md` developer section; if `pip install -e .`, `python -m hermes_slicer.bridge`, and test invocation are missing, add them.
- Release impact: documentation only

---

## Gap Count Summary

| Priority | Count |
|---|---|
| P0 | 2 |
| P1 | 4 |
| P2 | 19 |
| P3 | 9 |
| **Total** | **34** |
