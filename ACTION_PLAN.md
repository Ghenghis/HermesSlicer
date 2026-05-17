# HermesSlicer V1 Action Plan

Date: 2026-05-16

## Objective

Finish V1 end to end without scope drift. The target is a proofable local sidecar, not a printer-control fork.

## Immediate P0 Checklist

- [x] Pin the complete upstream reference stack as submodules.
- [x] Validate all submodule remotes, commits, dirty states, and Hermes Agent `v2026.5.16` / package `0.14.0`.
- [x] Add an API contract drift test.
- [x] Add `ROADMAP.md` as the source of truth for V1 completion.
- [x] Reframe the panel as a Hermes Agent tool console instead of a JusPrin-style slicer settings chatbot.
- [x] Replace reference-login branding with a Hermes Slicer local-session gate.
- [x] Add a login visual/geometry acceptance gate for 1366x768, 1920x1080, and mobile.
- [ ] Enable/prove live Hermes Agent provider bridge connectivity, requiring external `HERMES_AGENT_ENABLED=1` plus a healthy provider backend.
- [ ] Enable/prove bounded AS_USER session grants, or document missing external `HERMES_HUMAN_GRANT_SECRET` as a release blocker.
- [x] Pick and add root `LICENSE` plus any needed `NOTICE`.
- [x] Run clean-clone rehearsal with submodules.
- [ ] Refresh browser/panel screenshots from the final branch state.
- [ ] Smoke the installable Hermes plugin against the active Hermes install.
- [x] Add final V1 release checklist output with proof summary, blocked external credentials, and tag-readiness notes.
- [x] Run final local proof command set.
- [ ] Append Hermes Proof MCP evidence after the MCP transport is restored.
- [ ] Tag the V1 release only after the above gates pass.

## Agent Operating Rule

For every remaining V1 task:

- Codex lead owns implementation and final integration.
- At least one read-only explorer audits concrete repo gaps.
- At least one proof/safety pass checks scope, safety, and evidence.
- Hermes Proof MCP evidence is appended whenever the MCP is available.
- If Hermes Agent health reports disabled, do not claim live Hermes Agent bridge connectivity.
- Do not expose Hermes Agent computer-use through the V1 slicer bridge.

## Stop Conditions

Stop and resolve before moving forward if:

- A command needs public network bind.
- A path would read private data or expose secrets.
- A task would upload to a printer or start a print.
- A change copies AGPL/GPL upstream implementation into local product code without a license note.
- A claimed MCP/agent connection cannot be proven by a gate.

## Final V1 Command Set

```powershell
python -m unittest discover -s tests
python -m compileall hermes_slicer integrations scripts tests
python scripts\validate_submodules.py
powershell -ExecutionPolicy Bypass -File scripts\regenerate_proof.ps1
python scripts\verify_login_geometry.py
python scripts\write_v1_release_checklist.py
python scripts\redaction_scan.py .
git status --short --branch
```
