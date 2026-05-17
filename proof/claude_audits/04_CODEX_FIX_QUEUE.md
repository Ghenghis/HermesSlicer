# HermesSlicer V1 — Codex Fix Queue
Date: 2026-05-17
Audit Contract: `CLAUDE_AUDIT_CONTRACT.md`

Ranked list of Codex actions in execution order. Each item includes the exact step needed, no implementation guesses. All items are Markdown-only audit output; no source files were changed during this audit.

**Note on non-Markdown file changes during audit:** None. This audit followed CLAUDE_AUDIT_CONTRACT.md hard rules strictly.

---

## Queue Order Rationale

Execution order:
1. **P0 unblocking actions** — must be done first to enable a truthful tag
2. **P1 correctness fixes** — important before tag; no code-behavior risk
3. **P2 test coverage** — security test gaps ranked before documentation gaps
4. **P2 code improvements** — routing and proof infrastructure
5. **P2 documentation** — CONTRIBUTING.md, CHANGELOG.md, diagram
6. **P3 polish** — screenshots, README verification, nice-to-haves

---

## QUEUE-01 (P0): Record Owner Acceptance Decisions in V1_RELEASE_CHECKLIST.md

**Gap ref:** P0-01
**File:** `V1_RELEASE_CHECKLIST.md`, `scripts/write_v1_release_checklist.py`
**Exact steps:**

1. Add the following section to `V1_RELEASE_CHECKLIST.md`:
   ```markdown
   ## Owner Acceptance Decisions

   | Gate | Decision | Rationale | Owner | Date |
   |---|---|---|---|---|
   | live_hermes_agent_provider_bridge | accepted-blocker | Env-only; provider keys present; will unblock after HERMES_AGENT_ENABLED is set | [owner] | [date] |
   | bounded_as_user_grants | accepted-blocker | Env-only; no code change required; will set secrets when ready | [owner] | [date] |
   | hermes_proof_mcp_transport | accepted-blocker | Requires MCP stdio server implementation (post-V1) | [owner] | [date] |
   | hermes_agent_computer_use_visual_control | accepted-blocker | macOS-only; Windows host; not in V1 scope | [owner] | [date] |
   ```

2. In `scripts/write_v1_release_checklist.py`, add a check that reads `V1_RELEASE_CHECKLIST.md` and sets `owner_decisions_recorded: true` in the output JSON when the `## Owner Acceptance Decisions` section is present with all 4 gate rows.

3. Update `proof/runtime/v1-release-checklist.json::tag_readiness.notes` to reflect that owner decisions have been recorded.

4. Re-run: `python scripts\write_v1_release_checklist.py`

---

## QUEUE-02 (P0): Create `scripts/write_hermes_proof_mcp_live.py`

**Gap ref:** P0-02
**File:** `scripts/write_hermes_proof_mcp_live.py` (new file)
**Exact steps:**

Create a new script that:
1. Imports `hermes_agent_bridge_gate()`, `as_user_session_gate()`, `hermes_mcp_transport_gate()` from `hermes_slicer/config.py`.
2. Calls each gate function and checks all return `ok: true` / `status: "passed"`.
3. Calls `hermes_verify_evidence()` via the active Hermes MCP tool with `workspace_root="G:\\Github\\HermesSlicer"`.
4. Only if all checks pass, writes `proof/runtime/hermes-proof-mcp.json` with `status: "passed"`, `workspace_scope_ok: true`, `evidence_ledger_ok: true`.
5. If any check fails, exits with a non-zero code and a clear error message — does NOT overwrite the existing artifact.
6. **Do NOT add this script to `scripts/regenerate_proof.ps1`** — it requires a confirmed live environment.

---

## QUEUE-03 (P1): Add `license` Field to `pyproject.toml`

**Gap ref:** P1-03
**File:** `pyproject.toml`
**Exact step:**
Add to the `[project]` table:
```toml
license = {text = "AGPL-3.0-only"}
```

---

## QUEUE-04 (P1): Add Deep-Validation for 6 Unchecked Proof Files

**Gap ref:** P1-01
**Files:** `scripts/validate_proof.py`, `tests/test_proof_validation.py`
**Exact steps:**

1. In `scripts/validate_proof.py`, add deep-validation blocks for each of the following files — at minimum assert `data["status"] == "passed"`:
   - `proof/runtime/hermes-tool-health.json`
   - `proof/runtime/hermes-tool-export_preflight.json`
   - `proof/runtime/hermes-tool-tool_request.json`
   - `proof/runtime/flsun-profile-inventory.json`
   - `proof/runtime/flsun-export-preflight.json`
   - `proof/runtime/screenshot-format.json`

2. Add corresponding tests in `tests/test_proof_validation.py` that write minimal valid and invalid fixtures and assert the validator accepts/rejects them.

---

## QUEUE-05 (P1): Create `scripts/write_as_user_session_proof.py`

**Gap ref:** P1-02
**Files:** `scripts/write_as_user_session_proof.py` (new), `proof/runtime/as_user_session.json` (new), `scripts/regenerate_proof.ps1`, `scripts/write_v1_release_checklist.py`
**Exact steps:**

1. Create `scripts/write_as_user_session_proof.py` that calls `as_user_session_gate()` from `hermes_slicer/config.py` and writes the gate result dict to `proof/runtime/as_user_session.json` with a `generated_at` timestamp.
2. Add it to `scripts/regenerate_proof.ps1`.
3. Add `proof/runtime/as_user_session.json` to the expected files list in `scripts/write_v1_release_checklist.py`.

---

## QUEUE-06 (P1): Update ROADMAP.md P0 Gate 5 Phrasing

**Gap ref:** P1-04
**File:** `ROADMAP.md`
**Exact change:** In P0 gate 5 "Hermes plugin install smoke" section, replace the conditional future phrasing "With an active Hermes install: `hermes plugins enable hermes-slicer`" block with:
> Confirmed active: `hermes-slicer` is enabled per `proof/runtime/hermes-plugin-smoke.json`. Plugin confirmed as `enabled: true`, `source: user`, version `0.1.0`.

---

## QUEUE-07 (P2): Add AS_USER TTL Edge-Case Tests

**Gap ref:** P2-07
**File:** `tests/test_hermes_integration.py` or `tests/test_bridge_core.py`
**Exact test cases:**
- `test_as_user_all_vars_absent()` → expects `status: "blocked"`
- `test_as_user_expired_timestamp()` → set `HERMES_AS_USER_EXPIRES_AT` to 1 minute ago → `status: "blocked"`
- `test_as_user_ttl_exactly_900s()` → set `EXPIRES_AT` to exactly 15 minutes from now → `status: "passed"`
- `test_as_user_ttl_901s()` → set `EXPIRES_AT` to 15 minutes + 1 second → `status: "blocked"`
- `test_as_user_empty_scopes()` → set `HERMES_AS_USER_SCOPES=""` → `status: "blocked"`
- `test_as_user_valid_grant()` → all vars present with valid short TTL and explicit scopes → `status: "passed"`

---

## QUEUE-08 (P2): Add Hermes v0.12 Version Rejection Test

**Gap ref:** P2-08
**File:** New `tests/test_smoke_hermes_plugin.py` or `tests/test_bridge_core.py`
**Exact test cases:**
- `test_version_012_rejected()` — mock `hermes version` output to `"Hermes Agent v0.12.0 (2026.1.1)"` → assert `matches_expected: false`, `status: "blocked"`
- `test_version_0140_accepted()` — mock output to `"Hermes Agent v0.14.0 (2026.5.16)"` → assert `matches_expected: true`, `status: "passed"`
- `test_version_0141_rejected()` — mock to `"Hermes Agent v0.14.1 (2026.5.16)"` → assert `matches_expected: false` (exact match required)
- `test_version_malformed_rejected()` — mock to `"invalid"` → assert `matches_expected: false`

---

## QUEUE-09 (P2): Add IPv6 and LAN Public-Bind Prevention Tests

**Gap ref:** P2-09
**File:** `tests/test_bridge_core.py`
**Exact change:** Parameterize the existing `test_bridge_bind_address` with:
```python
@pytest.mark.parametrize("bad_addr", ["0.0.0.0", "::", "192.168.1.1", "10.0.0.1"])
def test_bridge_rejects_non_loopback_bind(bad_addr):
    # assert SystemExit is raised when bind address is not 127.0.0.1 or ::1
```

---

## QUEUE-10 (P2): Add `regenerate_proof.ps1` Hermes Version Assertion

**Gap ref:** P2-04
**File:** `scripts/regenerate_proof.ps1`
**Exact change:** Add at the top of the script (before any proof writer calls):
```powershell
$hermesVersion = & hermes version 2>&1
if ($hermesVersion -notmatch "Hermes Agent v0\.14\.0 \(2026\.5\.16\)") {
    Write-Error "Hermes CLI version mismatch. Expected v0.14.0 (2026.5.16), got: $hermesVersion"
    exit 1
}
```

---

## QUEUE-11 (P2): Add `clean_clone_rehearsal.ps1` Hermes Version Assertion

**Gap ref:** P2-05
**File:** `scripts/clean_clone_rehearsal.ps1`
**Exact change:** Add Hermes version assertion step after `git clone`, before proof regeneration:
```powershell
$hermesVersion = & hermes version 2>&1
if ($hermesVersion -notmatch "Hermes Agent v0\.14\.0 \(2026\.5\.16\)") {
    Write-Error "Hermes CLI version mismatch in rehearsal environment: $hermesVersion"
    exit 1
}
```

---

## QUEUE-12 (P2): Add Clean-Clone Staleness Check to Release Checklist

**Gap ref:** P2-06
**File:** `scripts/write_v1_release_checklist.py`
**Exact change:** After reading `proof/runtime/clean-clone-rehearsal.json`, parse `started_at` and compare to today. If more than 7 days old, set `clean_clone_rehearsal_stale: true` in the output JSON and add a warning line to the checklist Markdown.

---

## QUEUE-13 (P2): Add Proof Ledger Tamper-Detection Tests

**Gap ref:** P2-11
**File:** `tests/test_proof_validation.py`
**Exact test cases:**
- `test_ledger_valid_entry_accepted()` — write a minimal valid entry; assert no error
- `test_ledger_null_timestamp_rejected()` — set `timestamp: null`; assert schema validation error
- `test_ledger_missing_action_rejected()` — omit `action` field; assert error
- `test_sanitize_redacts_secret()` — pass a dict with an API key value; assert `[REDACTED]` in output

---

## QUEUE-14 (P2): Implement MCP stdio Server (Post-V1 P1)

**Gap ref:** P2-01
**File:** `hermes_slicer/mcp_server.py` (new), `pyproject.toml`, registration command
**Exact steps:**

1. Create `hermes_slicer/mcp_server.py` implementing JSON-RPC 2.0 over stdio (see `upstream/mcp-python-sdk` for the protocol).
2. Expose all 13 bridge actions as tools with proper input schemas.
3. Assert `workspace_root` in evidence responses equals `G:\Github\HermesSlicer`.
4. Add entry point to `pyproject.toml`: `hermes-slicer-mcp = "hermes_slicer.mcp_server:main"`.
5. Register with Hermes: `hermes mcp add hermes-slicer-proof --command python --args -m hermes_slicer.mcp_server`.
6. Add smoke test: `python -m hermes_slicer.mcp_server --test` should exit 0.
7. After registration, run `python scripts\write_hermes_proof_mcp_live.py` (QUEUE-02).

---

## QUEUE-15 (P2): Add `hermes-tool-tts_speak.json` Proof Artifact

**Gap ref:** P2-03
**File:** `scripts/write_hermes_tool_tts_speak_proof.py` (new), `scripts/regenerate_proof.ps1`, `scripts/write_v1_release_checklist.py`
**Exact steps:**

1. Create `scripts/write_hermes_tool_tts_speak_proof.py` that calls the bridge `tts_speak` action and writes `proof/runtime/hermes-tool-tts_speak.json` with `status: "blocked"` if Azure credentials absent or `status: "passed"` if they are present and the call succeeds.
2. Add to `scripts/regenerate_proof.ps1`.
3. Add `proof/runtime/hermes-tool-tts_speak.json` to expected files list in `scripts/write_v1_release_checklist.py`.

---

## QUEUE-16 (P2): Add `requestBody` Schemas to OpenAPI Spec

**Gap ref:** P2-02
**File:** `api_contract.openapi.yaml`
**Exact change:** For each POST endpoint, add:
```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        required: [action]
        properties:
          action:
            type: string
            enum: [health, actions, profiles, orca_version, dry_run, export_preflight, export_gcode, tool_request, tts_speak, proof_recent, hermes_proof_mcp, agents, voices]
          payload:
            type: object
            additionalProperties: true
```
Re-run `tests/test_api_contract.py` to confirm drift detection works.

---

## QUEUE-17 (P2): Replace `parents[1]` ROOT Resolution With Sentinel Scan

**Gap ref:** P2-14
**File:** `integrations/hermes_agent_tool.py`
**Exact change:** Replace the `Path(__file__).parents[1]` cwd fallback with a function that walks up from `__file__` until it finds `pyproject.toml` or `.hermes/` directory. Log the resolved root at import time.

---

## QUEUE-18 (P2): Enforce Ledger Schema on Write

**Gap ref:** P2-10
**File:** `hermes_slicer/proof.py`
**Exact change:** In `record_event()`, after `sanitize_obj()`, call `jsonschema.validate(entry, load_ledger_schema())` where `load_ledger_schema()` reads `proof/PROOF_LEDGER_SCHEMA.json`. Raise `ValueError` on schema violation.

---

## QUEUE-19 (P2): Create CONTRIBUTING.md

**Gap ref:** P2-18
**File:** `CONTRIBUTING.md` (new)
**Content must cover:** Python version requirements, `git clone --recurse-submodules`, `pip install -e .`, `python -m hermes_slicer.bridge`, opening `http://127.0.0.1:8765`, running `python -m unittest discover -s tests`, proof screenshot checkpoints, brand guidelines reference (`BRAND.md`, `config/brand_tokens.json`).

---

## QUEUE-20 (P2): Create CHANGELOG.md

**Gap ref:** P2-19
**File:** `CHANGELOG.md` (new)
**Content:** V1 entry with date (2026-05-17), list of local gates completed, list of external gates blocked with their gate IDs.

---

## QUEUE-21 (P2): Add Architecture Diagram to README.md

**Gap ref:** P3-01
**File:** `README.md`
**Exact change:** Add the Mermaid diagram from `proof/claude_audits/agents/agent5_release_completion.md` Section 11 under an `## Architecture` heading.

---

## QUEUE-22 (P3): Add Help Overlay for Tool IDs in Panel

**Gap ref:** P2-16
**File:** `web/index.html`, `web/app.js`
**Exact change:** Add a collapsible `<details>` element with `<summary>? Help</summary>` that lists available tool IDs from the `bridge.actions` response with one-line descriptions. Populate on `bridge.actions` fetch at startup.

---

## QUEUE-23 (P3): Disable Mic Button When Azure Credentials Absent

**Gap ref:** P2-17
**File:** `web/app.js`
**Exact change:** In the `fetchVoices()` or health-check callback, if `/api/voices/azure/en` returns an empty list or error, add `micButton.disabled = true` and `micButton.title = "Azure credentials not configured"`.

---

## QUEUE-24 (P3): Add Playwright Screenshot Capture Script

**Gap ref:** P2-15
**File:** `scripts/capture_screenshots.py` (new)
**Exact steps:** Playwright script that navigates to `http://127.0.0.1:8765`, captures the 5 required screenshots at the reference viewport, and writes them to `proof/screenshots/`. Add staleness check in release checklist.

---

## QUEUE-25 (P3): Add Computer-Use Blocked Screenshot

**Gap ref:** P3-03
**Files:** `proof/screenshots/computer-use-blocked.png` (manual capture), `scripts/verify_screenshots.py`
**Exact steps:** Capture a screenshot showing the panel state when computer-use is blocked (Windows host). Add filename to the `SCREENSHOTS` list in `scripts/verify_screenshots.py`.

---

## QUEUE-26 (P3): Update ROADMAP.md Azure TTS P1 Item

**Gap ref:** P2-13
**File:** `ROADMAP.md`
**Exact change:** Update P1 Azure TTS item to: "Complete `tts_speak` action for live playback: add `HERMES_ENABLE_TTS=1` gate, Azure credential check, and `proof/runtime/hermes-tool-tts_speak.json` proof artifact (action already exists in `bridge.py`)."

---

## QUEUE-27 (P3): Verify and Update README.md Developer Setup

**Gap ref:** P3-09
**File:** `README.md`
**Exact step:** Read the `README.md` developer section. If `pip install -e .`, `python -m hermes_slicer.bridge`, and test invocation (`python -m unittest discover -s tests`) are missing, add them under a `## Developer Setup` heading.

---

## Summary Table

| Queue | Priority | Category | File(s) | Blocks Tag? |
|---|---|---|---|---|
| QUEUE-01 | P0 | Owner decision | `V1_RELEASE_CHECKLIST.md`, script | YES |
| QUEUE-02 | P0 | New script | `scripts/write_hermes_proof_mcp_live.py` | NO (live MCP) |
| QUEUE-03 | P1 | Config fix | `pyproject.toml` | NO |
| QUEUE-04 | P1 | Validation | `scripts/validate_proof.py`, tests | NO |
| QUEUE-05 | P1 | New script + artifact | `scripts/write_as_user_session_proof.py` | NO |
| QUEUE-06 | P1 | Docs | `ROADMAP.md` | NO |
| QUEUE-07 | P2 | Tests | `tests/test_hermes_integration.py` | NO |
| QUEUE-08 | P2 | Tests | `tests/` | NO |
| QUEUE-09 | P2 | Tests | `tests/test_bridge_core.py` | NO |
| QUEUE-10 | P2 | Script guard | `scripts/regenerate_proof.ps1` | NO |
| QUEUE-11 | P2 | Script guard | `scripts/clean_clone_rehearsal.ps1` | NO |
| QUEUE-12 | P2 | Staleness check | `scripts/write_v1_release_checklist.py` | NO |
| QUEUE-13 | P2 | Tests | `tests/test_proof_validation.py` | NO |
| QUEUE-14 | P2 | New module | `hermes_slicer/mcp_server.py` | NO (post-V1) |
| QUEUE-15 | P2 | Proof artifact | `scripts/write_hermes_tool_tts_speak_proof.py` | NO |
| QUEUE-16 | P2 | OpenAPI spec | `api_contract.openapi.yaml` | NO |
| QUEUE-17 | P2 | Code hardening | `integrations/hermes_agent_tool.py` | NO |
| QUEUE-18 | P2 | Code hardening | `hermes_slicer/proof.py` | NO |
| QUEUE-19 | P2 | New doc | `CONTRIBUTING.md` | NO |
| QUEUE-20 | P2 | New doc | `CHANGELOG.md` | NO |
| QUEUE-21 | P2 | Docs | `README.md` | NO |
| QUEUE-22 | P3 | UI feature | `web/index.html`, `web/app.js` | NO |
| QUEUE-23 | P3 | UI polish | `web/app.js` | NO |
| QUEUE-24 | P3 | New script | `scripts/capture_screenshots.py` | NO |
| QUEUE-25 | P3 | Screenshot | `proof/screenshots/` | NO |
| QUEUE-26 | P3 | Docs | `ROADMAP.md` | NO |
| QUEUE-27 | P3 | Docs | `README.md` | NO |
