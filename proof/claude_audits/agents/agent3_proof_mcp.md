# Agent 3: Proof and MCP Audit Report
Date: 2026-05-17
Auditor: Claude Agent (proof-mcp)

## 1. Summary

The V1 proof bundle is structurally complete and truthful. All 14 local proof files exist, the clean-clone rehearsal passed all 6 steps from GitHub `main`, the ledger is append-only and always sanitized before writes, and the redaction scan reports clean. The Hermes Proof MCP gate is correctly reported as `blocked` — `workspace_scope_ok: false`, `evidence_ledger_ok: false`, `transport_closed`. Six actionable gaps exist: the most significant is that no `write_hermes_proof_mcp_live.py` script exists to produce a passing artifact once the MCP transport opens; the validation script deep-checks only 8 of 14 proof files; and there is no standalone AS_USER proof artifact.

---

## 2. Proof Regeneration

## P3: regenerate_proof.ps1 Regenerates All 14 Required Proof Files
- Status: verified complete
- Evidence: `proof/runtime/v1-release-checklist.json` → `proof_summary.local_proof_files` lists 14 files, all `exists: true`, `failed: []`, `missing: []`. Script `scripts/regenerate_proof.ps1` calls all writer scripts.
- Why it matters: A single command regenerates the full local proof bundle.
- Codex next action: None for V1. Add `--verify-hermes-version` pre-check to the script (see P2 below).
- Release impact: documentation only.

## P2: regenerate_proof.ps1 Does Not Assert Hermes CLI Version Before Proceeding
- Status: open — missing guard
- Evidence: `scripts/regenerate_proof.ps1` does not call `hermes version` and assert `v0.14.0` before generating proof artifacts. If a stale v0.12 install is present, proof artifacts could be generated with wrong version data.
- Why it matters: A CI or developer machine with a stale Hermes install could produce passing-looking artifacts tied to the wrong version.
- Codex next action: Add `hermes version` call at the top of `scripts/regenerate_proof.ps1`; fail fast with a clear error if the version string does not match `v0.14.0 (2026.5.16)`.
- Release impact: polish — closes a version-staleness hole.

## P0: No Script to Write a Live (Passing) Hermes Proof MCP Artifact
- Status: open — needs Codex implementation
- Evidence: `scripts/write_hermes_proof_mcp_status.py` always writes a `blocked` artifact based on current env state. There is no separate `write_hermes_proof_mcp_live.py` script that accepts a verified MCP transport result and writes a `passed` artifact. The live gate cannot transition to `passed` without a script that can produce that state.
- Why it matters: Even if the operator sets all required env vars and opens the MCP transport, there is no code path to generate a `passed` `hermes-proof-mcp.json`. Codex cannot close this gate with env vars alone.
- Codex next action: Create `scripts/write_hermes_proof_mcp_live.py` that: (1) calls `hermes_agent_bridge_gate()`, (2) calls `hermes_mcp_transport_gate()` with `workspace_root=G:\Github\HermesSlicer`, (3) calls `as_user_session_gate()`, (4) calls `hermes_verify_evidence()` via the active MCP tool, and (5) writes `proof/runtime/hermes-proof-mcp.json` with `status: "passed"` only when all checks return `ok`. This script must not be called from `regenerate_proof.ps1` automatically — it requires a confirmed live environment.
- Release impact: blocks live MCP gate — does NOT block V1 local tag.

---

## 3. Proof Validation

## P1: validate_proof.py Deep-Checks Only 8 of 14 Proof Files
- Status: open — needs Codex improvement
- Evidence: `scripts/validate_proof.py` has deep-validation logic for 8 proof files (bridge-health, smoke-report, login-geometry, hermes-plugin-smoke, hermes-proof-mcp, hermes-computer-use, submodule-stack, v1-release-checklist). The remaining 6 (`hermes-tool-health.json`, `hermes-tool-export_preflight.json`, `hermes-tool-tool_request.json`, `flsun-profile-inventory.json`, `flsun-export-preflight.json`, `screenshot-format.json`) are only existence-checked, not status-validated.
- Why it matters: A tool-dispatch proof file could contain `"status": "failed"` and still pass the proof validation gate.
- Codex next action: Add deep-validation blocks for the 6 unchecked files. At minimum: assert `"status"` field exists and equals `"passed"` for each. Add to `tests/test_proof_validation.py`.
- Release impact: polish — closes a silent-failure gap in the validation gate.

## P2: Proof Validation Gap — Blocked State Must Not Be Accepted as Passed
- Status: verified complete (not a gap)
- Evidence: `scripts/validate_proof.py` deep-validation for `hermes-proof-mcp.json` explicitly checks `status == "blocked"` or `status == "passed"` with different validation paths. The `blocked` check does NOT set the overall proof run to `failed` — blocked external gates are expected and documented.
- Why it matters: Confirms the validator does not reject a `blocked` artifact as invalid.
- Codex next action: None. Document this behavior in validator comments.
- Release impact: documentation only.

---

## 4. Ledger Behavior

## P3: Ledger Is Append-Only and Always Sanitized
- Status: verified complete
- Evidence: `hermes_slicer/proof.py` — `record_event()` always calls `sanitize_obj()` before writing to `proof/ledger.jsonl`. `sanitize_obj()` redacts known secret patterns (API keys, tokens, HERMES_HUMAN_GRANT_SECRET) to `"[REDACTED]"`. `proof/ledger.jsonl` contains 52 events as of audit; all structurally valid.
- Why it matters: Secrets cannot appear in the ledger even if accidentally passed through an action payload.
- Codex next action: Add a test that passes a synthetic secret string through `sanitize_obj()` and asserts it is redacted.
- Release impact: documentation only — current behavior is correct.

## P2: Ledger Schema Not Programmatically Enforced on Write
- Status: open — minor gap
- Evidence: `proof/PROOF_LEDGER_SCHEMA.json` defines the expected schema but `hermes_slicer/proof.py` does not validate entries against it before writing. Invalid entries (missing timestamp, null action) would be silently accepted.
- Why it matters: A malformed ledger entry would not be caught until a reader tries to parse it.
- Codex next action: Add `jsonschema.validate(entry, LEDGER_SCHEMA)` in `record_event()` before the write. Import the schema from `proof/PROOF_LEDGER_SCHEMA.json`. Add a test for schema rejection of invalid entries.
- Release impact: polish — does not block V1 tag.

---

## 5. Redaction

## P3: Redaction Scan — Clean
- Status: verified complete
- Evidence: `proof/security/redaction-report.md` — no secrets found in tracked files. `scripts/redaction_scan.py` scans all tracked files for known secret patterns.
- Why it matters: No credentials or API keys are committed.
- Codex next action: None.
- Release impact: documentation only.

## P3: redaction_scan.py Does Not Cover `.env` / `.example` Files
- Status: open — minor gap
- Evidence: `scripts/redaction_scan.py` scans git-tracked files only. `.env` files are in `.gitignore` so they are untracked and not scanned. `config/*.example.json` files are tracked but contain placeholder strings.
- Why it matters: Low risk because `.env` files are untracked, but a developer could accidentally commit one. A pre-commit hook would catch this more reliably.
- Codex next action: Add a `pre-commit` hook that runs `redaction_scan.py` before each commit. Alternatively, add `.env*` and `*secrets*` patterns to the scan's filesystem (not just git-tracked) check.
- Release impact: polish — low risk for V1.

---

## 6. Clean-Clone Rehearsal

## P3: Clean-Clone Rehearsal — All 6 Steps Passed
- Status: verified complete
- Evidence: `proof/runtime/clean-clone-rehearsal.json` → `status: "passed"`. All 6 steps: `git clone --recurse-submodules` ✓, `unit tests` ✓, `compileall` ✓, `submodule validation` ✓, `proof regeneration` ✓, `redaction scan` ✓. Clone from `https://github.com/Ghenghis/HermesSlicer.git` on 2026-05-17T07:28 to 07:38 (9m46s).
- Why it matters: Confirms the repo is reproducible from GitHub `main` without local state.
- Codex next action: Re-run `scripts/clean_clone_rehearsal.ps1` after any submodule pin change or major source change.
- Release impact: documentation only — gate passes.

## P2: Clean-Clone Rehearsal Script Does Not Assert Hermes CLI Version
- Status: open — missing guard
- Evidence: `scripts/clean_clone_rehearsal.ps1` calls `python -m unittest discover`, `compileall`, submodule validation, and proof regeneration. It does not call `hermes version` before proof regeneration to confirm the active CLI in the clean clone environment matches `v0.14.0 (2026.5.16)`.
- Why it matters: A clean clone on a machine with a stale Hermes install would produce stale proof artifacts without failing the rehearsal.
- Codex next action: Add `hermes version` assertion step to `clean_clone_rehearsal.ps1` after clone, before proof regeneration. Fail the rehearsal if version does not match expected.
- Release impact: polish — closes a cross-machine reproducibility gap.

## P2: No Staleness Check on Clean-Clone Artifact in Release Checklist
- Status: open — missing check
- Evidence: `V1_RELEASE_CHECKLIST.md` reports `clean_clone_rehearsal_passed: yes` but does not assert when the rehearsal was run. If the rehearsal artifact is more than N days old, the checklist should warn.
- Why it matters: A rehearsal artifact from a stale branch state could give false confidence.
- Codex next action: Add a staleness check in `scripts/write_v1_release_checklist.py` — if `clean-clone-rehearsal.json::started_at` is more than 7 days before today, report `clean_clone_rehearsal_stale: true` in the checklist JSON.
- Release impact: polish.

---

## 7. Hermes Proof MCP Status

## P1: Hermes Proof MCP — Truthfully Blocked
- Status: blocked — verified truthful
- Evidence: `proof/runtime/hermes-proof-mcp.json` → `status: "blocked"`, `proof_mcp.workspace_scope_ok: false`, `proof_mcp.evidence_ledger_ok: false`, `proof_mcp.active_hermes_mcp_configured: false`, `proof_mcp.codex_mcp_transport_status: "transport_closed"`, `proof_mcp.workspace_root: null`.
- Why it matters: The report correctly distinguishes between a blocked local gate and a non-existent MCP transport. No false pass is claimed.
- Codex next action: See P0 above — a live script must be written to produce a `passed` artifact once the transport opens.
- Release impact: blocks live MCP feature — does NOT block V1 tag.

## P1: Workspace Scope Guard Is Implemented
- Status: verified complete
- Evidence: `proof/runtime/hermes-proof-mcp.json` → `expected_workspace_root: "G:\\Github\\HermesSlicer"`. The workspace scope check must reject a Hermes3D-scoped MCP lock (`G:\Github\Hermes3D`) as evidence for this workspace.
- Why it matters: Cross-workspace MCP evidence must never count for HermesSlicer gates.
- Codex next action: Add a test that passes a `workspace_root=G:\Github\Hermes3D` value to the workspace scope gate and asserts `workspace_scope_ok: false`.
- Release impact: documentation only — current guard is implemented.

---

## 8. Missing / Improvements Needed

| Item | Priority | Notes |
|------|----------|-------|
| `write_hermes_proof_mcp_live.py` script | P0 | Required to produce a passing MCP artifact |
| Deep-validation for 6 unchecked proof files | P1 | Silent failure gap in validate_proof.py |
| Standalone `proof/runtime/as_user_session.json` artifact | P1 | AS_USER gate embedded in MCP artifact only |
| Hermes version assertion in regenerate_proof.ps1 | P2 | Prevents stale-install artifacts |
| Hermes version assertion in clean_clone_rehearsal.ps1 | P2 | Prevents cross-machine stale proof |
| Clean-clone staleness check in release checklist | P2 | Flags stale rehearsal artifacts |
| Proof chain diagram (local → external → tag-readiness) | P2 | Missing visual overview |
| Schema enforcement on ledger writes | P2 | Silent invalid-entry risk |
| Pre-commit hook for redaction_scan.py | P3 | Belt-and-suspenders for .env accidental commits |
| Workspace scope rejection test | P3 | Confirms Hermes3D MCP does not count |

---

## 9. Codex Next Actions (Ranked)

1. **[Unblocks live MCP gate — P0]** Create `scripts/write_hermes_proof_mcp_live.py` that writes a `passed` artifact only after all MCP gate conditions verify. Do NOT call from `regenerate_proof.ps1`.
2. **[Closes validation gap — P1]** Add deep-validation for 6 unchecked proof files in `scripts/validate_proof.py` and `tests/test_proof_validation.py`.
3. **[Adds standalone AS_USER artifact — P1]** Create `scripts/write_as_user_session_proof.py` writing `proof/runtime/as_user_session.json`.
4. **[Closes version-staleness hole — P2]** Add Hermes version assertion to `scripts/regenerate_proof.ps1` and `scripts/clean_clone_rehearsal.ps1`.
5. **[Closes staleness blind spot — P2]** Add rehearsal staleness check in `scripts/write_v1_release_checklist.py`.
6. **[Closes silent-failure gap — P2]** Add `jsonschema.validate()` call in `hermes_slicer/proof.py::record_event()`.
7. **[Documentation — P2]** Add proof chain diagram to `README.md` or `proof/` showing local gates → external gates → tag readiness.
8. **[Pre-commit hook — P3]** Add pre-commit redaction scan to `.claude/settings.json` hooks.
