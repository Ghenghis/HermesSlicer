# Claude Agent Audit Contract

Purpose: use Claude and Claude-spawned agents to audit HermesSlicer end to end, then hand Codex a precise Markdown-only completion packet. Claude is not the implementer for this audit. Codex remains the implementation and integration owner.

## Hard Rules

- Markdown only. Claude may create or update files only under `proof/claude_audits/` and only with `.md` extension.
- No source edits. Do not modify `hermes_slicer/`, `integrations/`, `scripts/`, `tests/`, `web/`, `.hermes/`, `config/`, `proof/runtime/`, `proof/screenshots/`, root status docs, or any `upstream/` submodule.
- No generated binaries, screenshots, JSON, logs, cache files, or lock files.
- No secrets. Never print or copy secret values. Presence/absence flags are okay.
- No public bind, printer upload, printer start, destructive file operations, or private-data crawling.
- No V1 completion claims without proof. If a gate is blocked, say blocked.
- Hermes Agent must be current: `v0.14.0 (2026.5.16)` / release tag `v2026.5.16` / package `0.14.0`. Any v0.12 runtime path is a P0 blocker unless it is only upstream historical text.
- Hermes Proof MCP evidence must be workspace-scoped to this repo. Evidence from another workspace does not count.

## Required First Reads

Claude lead must read these before assigning agents:

- `README.md`
- `ROADMAP.md`
- `ACTION_PLAN.md`
- `V1_STATUS.md`
- `V1_RELEASE_CHECKLIST.md`
- `BASES.md`
- `integrations/README.md`
- `proof/mcp_binding_report.md`
- `proof/runtime/hermes-plugin-smoke.json`
- `proof/runtime/hermes-proof-mcp.json`
- `proof/runtime/hermes-computer-use.json`
- `proof/runtime/v1-release-checklist.json`
- `proof/runtime/clean-clone-rehearsal.json`

Claude agents may inspect source, tests, scripts, and proof artifacts read-only. They must ignore `upstream/` except when checking submodule pins, licensing boundaries, or upstream feature references.

## Agent Plan

Claude should use separate read-only agents with non-overlapping questions:

1. **Runtime Wiring Agent**
   Audit bridge endpoints, action dispatch, Hermes plugin wrapper, local tool routing, and proof artifacts. Confirm whether the local V1 sidecar is usable without overclaiming live Hermes provider connectivity.

2. **Hermes Agent Gate Agent**
   Audit Hermes v0.14 enforcement, plugin smoke, live health gate, AS_USER grant gate, computer-use gate, and any stale v0.12 references in project-owned files.

3. **Proof and MCP Agent**
   Audit proof regeneration, proof validation, ledger behavior, redaction, clean-clone rehearsal, and Hermes Proof MCP status. Confirm whether blocked MCP state is represented truthfully.

4. **UI and Product Agent**
   Audit login, Hermes Agent tool console, screenshot proof, layout gates, JusPrin-to-Hermes wording, and whether the UI reflects Hermes Agent tools rather than JusPrin settings automation.

5. **Release Completion Agent**
   Audit `ROADMAP.md`, `ACTION_PLAN.md`, `TASKS.md`, `V1_STATUS.md`, and `V1_RELEASE_CHECKLIST.md` for contradictions, missing P0s, stale claims, or tag-readiness gaps.

Each agent must return findings to Claude lead only. Claude lead then writes the final Markdown packet under `proof/claude_audits/`.

## Allowed Commands

Read-only commands that do not create files are allowed:

```powershell
git status --short --branch
git log --oneline -5
rg -n "pattern" .
python -m unittest discover -s tests
python scripts\validate_submodules.py
python scripts\validate_proof.py
python scripts\redaction_scan.py .
hermes version
hermes plugins list
hermes mcp list
```

Commands that write outside `proof/claude_audits/` are not allowed during Claude audit, including:

```powershell
python -m compileall hermes_slicer integrations scripts tests
powershell -ExecutionPolicy Bypass -File scripts\regenerate_proof.ps1
```

If Claude believes proof regeneration, compile caches, screenshots, or fresh runtime JSON are needed, Claude must record that request in Markdown for Codex. Claude must not run the writing command.

## Required Output Files

Claude lead must create or update these Markdown files unless the audit is blocked before file creation, in which case it must create `proof/claude_audits/00_EXECUTIVE_SUMMARY.md` explaining the blocker:

- `proof/claude_audits/00_EXECUTIVE_SUMMARY.md`
- `proof/claude_audits/01_E2E_COMPLETION_AUDIT.md`
- `proof/claude_audits/02_GAP_REGISTER.md`
- `proof/claude_audits/03_BLOCKERS_AND_EXTERNAL_GATES.md`
- `proof/claude_audits/04_CODEX_FIX_QUEUE.md`
- `proof/claude_audits/05_EVIDENCE_INDEX.md`

Optional agent raw reports may be added as:

- `proof/claude_audits/agents/<agent-name>.md`

No other files should be created by Claude for this audit.

## Finding Format

Every actionable finding must use this format:

```markdown
## P0/P1/P2/P3: Short Title

- Status: open | blocked | needs Codex implementation | needs external credential | verified complete
- Evidence: `path/to/file.ext`, command output summary, or proof artifact
- Why it matters: one or two sentences
- Codex next action: exact implementation or verification step
- Release impact: blocks tag | blocks live feature | polish | documentation only
```

Priority meanings:

- P0: blocks truthful V1 completion or can cause unsafe/false claims.
- P1: important gap that should be fixed before V1 tag.
- P2: useful improvement or missing regression coverage.
- P3: polish, naming, documentation, or nice-to-have.

## Truth Checklist

Claude must explicitly answer these yes/no questions in `00_EXECUTIVE_SUMMARY.md`:

- Does active Hermes prove `v0.14.0 (2026.5.16)`?
- Is any project-owned path still relying on Hermes v0.12?
- Is `hermes-slicer` enabled and smoke-proved?
- Does live Hermes Agent connectivity pass, or is it blocked?
- Does Hermes Proof MCP pass for this workspace, or is transport/evidence blocked?
- Does AS_USER pass with bounded grant, or is it blocked?
- Does computer-use pass with visual proof, or is it blocked?
- Does a clean clone from GitHub `main` pass?
- Is V1 tag-ready right now?

## Codex Handoff Rules

The final handoff to Codex must:

- Separate local completed work from external blocked gates.
- Include exact file paths and commands used.
- Avoid implementation guesses when proof is missing.
- Rank the Codex fix queue in the order Codex should execute.
- State whether any non-Markdown files were changed during audit commands.

Claude should not tag a release, open a PR, push commits, or change Git branches for this audit.
