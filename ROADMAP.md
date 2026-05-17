# HermesSlicer V1 Roadmap

Date: 2026-05-16

## Mission

Ship HermesSlicer V1 as a local, proof-driven OrcaSlicer sidecar:

`OrcaSlicer GUI -> HermesSlicer floating panel -> localhost bridge -> slicer/profile proof -> Hermes Agent tooling -> Hermes Proof MCP evidence`

V1 is complete only when the repo can prove the stack end to end from a clean checkout without exposing secrets, binding publicly, or starting a printer.

## Do Not Stray Rules

- Stay bridge-first. Do not deep-fork Orca/Prusa/FLSUN UI code for V1.
- Keep the bridge on `127.0.0.1`.
- Do not upload to a printer or start a print in V1.
- Do not copy upstream AGPL/GPL implementation into `hermes_slicer/` without a source, license, and reason note.
- Do not add random upstreams. Every submodule must be authoritative, pinned, documented in `BASES.md`, and validated by `scripts/validate_submodules.py`.
- Do not claim Hermes Agent or Proof MCP connectivity unless a gate proves it.
- Every V1 completion step must leave proof in the local proof bundle and, when available, Hermes Proof MCP evidence.

## Current Progress

| Track | Status | Proof |
| --- | --- | --- |
| GitHub repo, branches, and default `main` | Complete | `BRANCHES.md`, pushed `main` |
| Upstream reference stack | Complete | `BASES.md`, `proof/runtime/submodule-stack.json` |
| Local bridge and action dispatch | Complete | `/health`, `/api/actions`, `/api/action`, `proof/ledger.jsonl` |
| Orca executable/profile discovery | Complete | `proof/runtime/bridge-health.json`, `proof/runtime/smoke-report.md` |
| FLSUN T1/V400/S1 profile preflight | Complete | `proof/runtime/flsun-profile-inventory.json`, `proof/runtime/flsun-export-preflight.json` |
| G-code export safety | Complete for V1 | Blocked by default unless `HERMES_ENABLE_EXPORT_GCODE=1`; printer start is not implemented |
| Floating panel | Complete for V1 | `proof/screenshots/*.png`, `proof/runtime/screenshot-format.json` |
| Login visual/geometry gate | Complete | `scripts/verify_login_geometry.py`, `proof/runtime/login-geometry.json` |
| Hermes Agent local plugin wrapper | Complete for V1; active install blocked by external version/config | `integrations/hermes-slicer/`, `.hermes/plugins/hermes-slicer/`, `proof/runtime/hermes-plugin-smoke.json` |
| API contract drift guard | Complete | `api_contract.openapi.yaml`, `tests/test_api_contract.py` |
| Hermes Proof MCP evidence channel | Blocked in current session | `proof/runtime/hermes-proof-mcp.json`; current MCP transport is closed |
| Root project license | Complete | `LICENSE`, `NOTICE` |
| V1 release checklist | Blocked on external gates | `V1_RELEASE_CHECKLIST.md`, `proof/runtime/v1-release-checklist.json` |
| Clean-clone release rehearsal | Complete | `proof/runtime/clean-clone-rehearsal.json` |

## P0 Gates For V1 Complete

1. **Hermes Proof MCP and agent-session gate**

   Required proof:

   ```powershell
   # In this Codex session/tooling:
   # hermes_verify_evidence must report ok=true.
   # hermes_agent_health must report ok=true before claiming live Hermes Agent bridge connectivity.
   ```

   Current observed state:

   - Hermes Proof MCP evidence ledger: local artifact retains the last known verification, but the current MCP transport is closed.
   - Hermes Agent provider bridge: blocked because the bridge reports `bridge disabled`; external environment must enable `HERMES_AGENT_ENABLED=1` and provide a healthy provider backend.
   - Human AS_USER grant: blocked until external `HERMES_HUMAN_GRANT_SECRET` exists.

   V1 may ship with the local Hermes plugin wrapper, but it must not claim live Hermes Agent provider failover until this gate passes.

2. **Root license and notices**

   Root `LICENSE` and `NOTICE` are present. The V1 posture is AGPL-3.0-only for HermesSlicer-authored sidecar code outside `upstream/`; submodules retain their own licenses and notices.

3. **Clean checkout rehearsal**

   From a separate folder:

   ```powershell
   git clone --recurse-submodules https://github.com/Ghenghis/HermesSlicer.git HermesSlicer-v1-rehearsal
   cd HermesSlicer-v1-rehearsal
   python -m unittest discover -s tests
   python scripts\validate_submodules.py
   powershell -ExecutionPolicy Bypass -File scripts\regenerate_proof.ps1
   ```

   Or run the scripted rehearsal from this repo:

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\clean_clone_rehearsal.ps1
   ```

4. **UI proof refresh**

   Refresh the floating panel screenshots after the final branch state. Confirm panel-open, FLSUN proof view, and hidden state still render.

5. **Hermes plugin install smoke**

   Current committed proof:

   ```powershell
   python scripts\smoke_hermes_plugin.py
   ```

   This proves both committed wrappers register `hermes_agent_tools`, and it runs an isolated active-Hermes project-plugin harness without mutating the user's global Hermes config.

   With an active Hermes install:

   ```powershell
   $env:HERMES_ENABLE_PROJECT_PLUGINS = "1"
   $env:HERMES_SLICER_ROOT = "<repo-root>"
   hermes plugins enable hermes-slicer
   hermes -z "Check HermesSlicer bridge health" -t hermes_agent
   ```

   Current observed active CLI is blocked because it is not Hermes Agent `v2026.5.16` / package `0.14.0`, and it does not list `hermes-slicer` in `hermes plugins list`. If the active Hermes install path differs, document the actual path and evidence.

6. **Final release proof**

   Required commands:

   ```powershell
   python -m unittest discover -s tests
python -m compileall hermes_slicer integrations scripts tests
python scripts\validate_submodules.py
powershell -ExecutionPolicy Bypass -File scripts\regenerate_proof.ps1
python scripts\verify_login_geometry.py
python scripts\write_v1_release_checklist.py
python scripts\redaction_scan.py .
```

## P1 After V1

- Add a true MCP stdio server backed by `upstream/mcp-python-sdk`.
- Add live Azure TTS playback behind explicit credentials and opt-in proof.
- Add optional G-code export proof with an explicit local operator gate.
- Add Moonraker/OctoPrint/Klipper upload-only research gates.
- Add printer start only after a separate human-confirmed safety design.
- Consider Hermes Agent computer-use only after V1, starting read-only and gated by explicit AS_USER scope.

## Release Rule

Do not tag V1 until every P0 gate is either passed with proof or explicitly documented as a release-blocking owner decision.
