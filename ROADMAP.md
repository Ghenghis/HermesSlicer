# HermesSlicer V1 Roadmap

Date: 2026-05-17

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
| FLSUN T1 local printer observation | Complete for read-only V1 | `proof/runtime/printer-observation.json`; both `192.168.0.10` and `192.168.0.11` exposed Mainsail, Moonraker, OctoPrint compatibility, and camera snapshots |
| G-code export safety | Complete for V1 | Blocked by default unless `HERMES_ENABLE_EXPORT_GCODE=1`; printer start is not implemented |
| Floating panel | Complete for V1 | `proof/screenshots/*.png`, `proof/runtime/screenshot-format.json` |
| Login visual/geometry gate | Complete | `scripts/verify_login_geometry.py`, `proof/runtime/login-geometry.json` |
| Hermes Agent local plugin wrapper | Complete for V1; active install proved on Hermes Agent `v0.14.0` | `integrations/hermes-slicer/`, `.hermes/plugins/hermes-slicer/`, `proof/runtime/hermes-plugin-smoke.json` |
| Hermes Agent computer-use gate | Blocked for V1 on this host | `proof/runtime/hermes-computer-use.json`; upstream v0.14 computer-use requires macOS `cua-driver` plus bounded AS_USER and visual proof |
| API contract drift guard | Complete | `api_contract.openapi.yaml`, `tests/test_api_contract.py` |
| Hermes Proof MCP evidence channel | Complete for workspace transport | `hermes_slicer/mcp_server.py`, `scripts/write_hermes_proof_mcp_live.py`, `proof/runtime/hermes-proof-mcp.json`; active Hermes MCP has `hermes-slicer-proof` enabled with 16 tools |
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

   - Hermes Proof MCP evidence ledger: active Hermes v0.14 has `hermes-slicer-proof` registered as a workspace-scoped stdio MCP server with 16 enabled tools, and `hermes.verify_evidence` proves the local ledger/artifact bundle for `G:\Github\HermesSlicer`.
   - Hermes Agent provider bridge: blocked because `/health` reports `live_connectivity_claimed=false`; active provider envs are present, but the external environment must still set `HERMES_AGENT_ENABLED=1` and provide `HERMES_AGENT_HEALTH_URL` live health proof from Hermes Agent `v0.14.0` / `v2026.5.16`.
   - Human AS_USER grant: blocked until external `HERMES_HUMAN_GRANT_SECRET`, `HERMES_AS_USER_GRANT_ID`, `HERMES_AS_USER_SCOPES`, and short `HERMES_AS_USER_EXPIRES_AT` exist.

   V1 may ship with the local Hermes plugin wrapper and proof MCP transport, but it must not claim live Hermes Agent provider failover until the live Agent health and bounded AS_USER gates pass.

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

5. **Read-only local printer observation**

   Current targets:

   - `FLSUN T1 #1`: `192.168.0.10`
   - `FLSUN T1 #2`: `192.168.0.11`

   Required proof:

   ```powershell
   python scripts\write_printer_observation_proof.py
   ```

   This may discover Mainsail, Fluidd, OctoPrint, Moonraker, and camera snapshot endpoints. V1 must keep G-code upload, heater/motion commands, and print start blocked.

6. **Hermes plugin install smoke**

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

   Current observed active CLI passes: `hermes version` reports Hermes Agent `v0.14.0 (2026.5.16)` from `upstream/hermes-agent`, and `hermes plugins list` shows `hermes-slicer` enabled from the user plugin directory.

7. **Final release proof**

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

- Replace the lightweight JSON-RPC MCP foundation with the official `upstream/mcp-python-sdk` server wrapper if Hermes requires SDK-native transport semantics.
- Add live Azure TTS playback behind Azure Speech credentials, `HERMES_ENABLE_TTS=1`, and a proof artifact that records playback as synthesized or played.
- Add optional G-code export proof with an explicit local operator gate.
- Add Moonraker/OctoPrint/Klipper upload-only research gates after read-only observation is proved and scoped.
- Add printer start only after a separate human-confirmed safety design.
- Promote Hermes Agent computer-use only after V1, starting read-only and gated by explicit AS_USER scope plus a visual proof run against the HermesSlicer UI.

## V2 Carry-Forward From Hermes3D

The following Hermes3D patterns are intentionally not enabled as V1 printer actuation, but they are included in the V2 work queue so the project does not lose the path:

- Port the Hermes3D safety bundle pattern into a full HermesSlicer safety decision object: camera freshness, plate-clear classification, truth-gate pass, approval state, incident state, and printer policy.
- Add camera observer evidence capture with operator-approved snapshots, redacted proof artifacts, and a hard failure if a camera endpoint is stale, ambiguous, or unreachable.
- Add watchdog loop: poll printer state, classify INFO/WARN/HARD STOP, speak or show the alert, append proof, and wait for operator decision.
- Add Moonraker/OctoPrint write adapters only after read-only proof, AS_USER scope, printer lock, approval, cleared-plate proof, and rollback/stop evidence are all passing.
- Add real emergency-stop transport only after a mocked HARD STOP budget proof passes and the operator confirms the exact supported printer backend.
- Add Azure STT and live TTS using the Hermes3D voice route pattern, with credential presence, explicit opt-in, timeout, transcript/audio proof, and text fallback.
- Add signed proof envelopes or hash-chained bundles if local JSONL proof is no longer strong enough for release evidence.

## Release Rule

Do not tag V1 until every P0 gate is either passed with proof or explicitly documented as a release-blocking owner decision.
