# Agent 4: UI and Product Audit Report
Date: 2026-05-17
Auditor: Claude Agent (ui-product)

## 1. Summary

The HermesSlicer V1 UI stack is structurally complete at the local-session level. The login gate, panel, brand tokens, and screenshot proof all pass their automated gates as of 2026-05-17. The JusPrin-to-Hermes reframe is complete in all product-owned source files — zero JusPrin, JusBot, or Obico strings appear in `web/`, `hermes_slicer/`, `tests/`, `scripts/`, or `config/`. Remaining references are confined to research docs (`proof/research/`), planning docs, and the `NOTICE`/`.gitmodules` files that correctly identify `upstream/JusPrin` as a pinned AGPL reference submodule.

The panel header (`<h1>Hermes Agent Tool Console</h1>`) and quick-action buttons confirm tool-console identity is fully applied. No slicer-settings-chatbot behavior is present.

Four external gate categories remain blocked: live Hermes Agent provider bridge, AS_USER bounded grant, Hermes Proof MCP transport, and computer-use visual proof. None block the local-UI V1 tag itself.

**Overall V1 tag readiness for the UI layer: local gates all pass; external/live gates are blocked.**

---

## 2. Login Gate

## P3: Login Gate — All Three Viewports Pass
- Status: verified complete
- Evidence: `proof/runtime/login-geometry.json` — `"status": "passed"`, `"errors": []`. Viewports: `desktop_1366x768` (`full_card_visible: true`, ratio `0.655`, mode `desktop_compact`), `desktop_1920x1080` (`full_card_visible: true`, ratio `0.655`, mode `desktop_full`), `mobile_390x844` (`full_card_visible: true`, ratio `1.0`, mode `mobile`).
- Why it matters: Proves the login card does not overflow any reference viewport.
- Codex next action: Re-run `scripts/verify_login_geometry.py` after any CSS geometry change.
- Release impact: documentation only — gate passes.

## P3: Login Asset Hash Verified
- Status: verified complete
- Evidence: `proof/runtime/login-geometry.json` — `asset.sha256` equals `expected_sha256` (`89979c452028fbc0780dc0781acb8697764460c8c203ec57bb55968160ab77c8`), size `1120x718` matches expected.
- Why it matters: Confirms shipped login PNG is the accepted Hermes reference image, not a placeholder.
- Codex next action: Any replacement hero image must update `EXPECTED_LOGIN_SHA256` and `EXPECTED_LOGIN_SIZE` in `scripts/verify_login_geometry.py` and re-run gate.
- Release impact: blocks tag if hash drifts without gate update.

## P3: Forbidden Text Absent From Login Source
- Status: verified complete
- Evidence: `proof/runtime/login-geometry.json` → `source_checks.forbidden_text_absent: true`. Forbidden list: `"JusPrin"`, `"JusBot"`, `"Obico"`, `"Continue to Hermes Tools"`, `"No slicing. Just print."` — all absent from `web/index.html` and `web/styles.css`.
- Why it matters: Login surface carries no legacy JusPrin or Obico copy.
- Codex next action: Keep `FORBIDDEN_TEXT` tuple in `scripts/verify_login_geometry.py` updated if new legacy strings are identified.
- Release impact: blocks tag if any forbidden string is found.

## P2: Login Is a Local-Session Gate, Not an OAuth Flow
- Status: verified complete
- Evidence: `web/app.js` lines 41-54 — `submitAuth` collects username/password, calls `sessionStorage.setItem("hermesLocalSession", "connected")` via a 120ms stub. "Forgot password" and "Sign Up" display "not connected in this local V1 build." `tests/test_ui_static.py::test_login_form_is_real_local_session_ui` asserts `submitAuth`, `hermesLocalSession`, and `sessionStorage` presence.
- Why it matters: Confirms no token or OAuth handling; no credential in proof logs. Deliberate V1 design decision.
- Codex next action: When adding real auth later, keep tokens outside proof logs; expose only a boolean capability state.
- Release impact: polish for V1; blocks live-credential feature for V2+.

## P2: Login Geometry Is Computed, Not Pixel-Exact
- Status: open — known limitation
- Evidence: `scripts/verify_login_geometry.py::estimate_layout()` computes layout from CSS breakpoint rules and viewport dimensions. It does not measure rendered pixels from a live browser.
- Why it matters: Cannot catch CSS regressions caused by browser rendering quirks, font metrics, or scrollbar behavior. Validates CSS math consistency, not actual render.
- Codex next action: For V2, add a Playwright screenshot-and-pixel-check step against the three reference viewports.
- Release impact: polish for V1.

---

## 3. Hermes Agent Tool Console

## P3: Panel Identity Is Hermes Agent Tool Console
- Status: verified complete
- Evidence: `web/index.html` — `aria-label="Hermes Agent tool console"`, `<h1>Hermes Agent Tool Console</h1>`. Quick-action buttons: `bridge.actions`, `hermes.proof_mcp`, `slice.export_preflight`, `proof.recent`, `orca.version`, `slice.dry_run`. Tool input placeholder: `"Tool ID or request"`.
- Why it matters: Panel is unambiguously framed as a Hermes Agent tool routing surface, not a settings chatbot.
- Codex next action: None for V1.
- Release impact: verified complete.

## P3: No Slicer-Settings Automation Behavior in Panel UI
- Status: verified complete
- Evidence: `web/app.js` contains no slicer-settings mutation code. All slicer-facing paths go through `api()` calls to bridge endpoints. `export_gcode` is gated behind `HERMES_ENABLE_EXPORT_GCODE=1`.
- Why it matters: Prevents accidental automated slicer changes via the chat surface.
- Codex next action: Keep `HERMES_ENABLE_EXPORT_GCODE` off by default in all documentation and setup guides.
- Release impact: verified complete.

## P3: Panel States (open, hidden, FLSUN) All Covered by Screenshots
- Status: verified complete
- Evidence: `proof/runtime/screenshot-format.json` — all five screenshots present with valid image signatures: `panel-open.png`, `panel-hidden.png`, `panel-flsun.png`, `login-hermes-slicer.jpg`, `hermes-agent-tools.jpg`.
- Why it matters: Proves the hide/show dock button and FLSUN proof view are exercised.
- Codex next action: Refresh screenshots whenever UI changes substantially.
- Release impact: verified complete.

## P2: Live Hermes Agent Bridge Not Connected
- Status: blocked — needs external credential
- Evidence: `proof/runtime/v1-release-checklist.json` → `hermes_agent_bridge.status: "blocked"`. `HERMES_AGENT_ENABLED=1` not set. Panel shows `"bridge offline"` when Python bridge not running.
- Why it matters: Without a running bridge, tool console quick-actions return errors.
- Codex next action: Set `HERMES_AGENT_ENABLED=1`, configure a provider key, set `HERMES_AGENT_HEALTH_URL`.
- Release impact: blocks live-feature claim; does NOT block V1 local-session tag.

## P2: Voice and Mic Stubs Not Connected — No Disabled State
- Status: open — known V1 limitation
- Evidence: `proof/research/floating_panel_report.md` — "Voice capture/playback is stubbed until Azure credentials are present." `web/index.html` mic and stop buttons are present and visually active even when Azure credentials are absent.
- Why it matters: A user may click mic and see no response with no explanation.
- Codex next action: On bridge health check, if `/api/voices/azure/en` returns empty list or error, add `disabled` attribute and `title="Azure credentials not configured"` to the mic button.
- Release impact: polish for V1; blocks voice feature for V2+.

---

## 4. Screenshot Proof

## P3: All Five Required Screenshots Present and Valid
- Status: verified complete
- Evidence: `proof/runtime/screenshot-format.json` → `"status": "passed"`. All five files confirmed with correct PNG/JPEG image signatures: `panel-open.png`, `panel-flsun.png`, `panel-hidden.png`, `login-hermes-slicer.jpg`, `hermes-agent-tools.jpg`.
- Why it matters: Screenshot existence and format integrity are a required V1 gate.
- Codex next action: None.
- Release impact: verified complete.

## P2: Screenshots Are Manually Captured, Not Auto-Refreshed
- Status: open — process gap
- Evidence: `proof/screenshots/README.md` — "Captured with the Codex in-app browser on 2026-05-16." `scripts/verify_screenshots.py` only checks file existence and image signature; it does not capture new screenshots.
- Why it matters: If the UI changes, screenshots silently become stale. The gate still passes even if screenshots no longer reflect the actual UI.
- Codex next action: Add a Playwright capture step that re-takes the five screenshots on demand. Gate the V1 release checklist on a freshness check (screenshot mtime within 7 days of latest commit).
- Release impact: polish for V1.

## P3: No Screenshot for Computer-Use Blocked State
- Status: open — missing artifact
- Evidence: No `computer-use-blocked.png` or equivalent in `proof/screenshots/`. `hermes-computer-use.json` reports `visual_proof.passed: false`.
- Why it matters: A reviewer cannot visually confirm what the user sees when computer-use is blocked on Windows.
- Codex next action: Add `proof/screenshots/computer-use-blocked.png` showing the panel message when computer-use is unavailable. Update `scripts/verify_screenshots.py` `SCREENSHOTS` list.
- Release impact: documentation only for V1.

## P3: Screenshot Filename Manifest Is Hardcoded in verify_screenshots.py
- Status: open — maintenance gap
- Evidence: `scripts/verify_screenshots.py` `SCREENSHOTS` constant lists exactly 5 file names. New screenshots not added to this list will not be checked.
- Why it matters: Coverage silently drops as the screenshot set grows.
- Codex next action: Consider glob-based approach checking all `proof/screenshots/*.{png,jpg}` files.
- Release impact: documentation only.

---

## 5. Layout Gates

## P3: Login Geometry Gate Checks CSS Math Against Three Reference Viewports
- Status: verified complete (with noted limitation)
- Evidence: `scripts/verify_login_geometry.py::estimate_layout()` applies `@media` breakpoints and CSS calc expressions — all three viewports produce `full_card_visible: true`.
- Why it matters: Gate catches arithmetic drift in CSS breakpoints and ratio constants without requiring a browser.
- Codex next action: None for V1. Add browser-rendered pixel check for V2.
- Release impact: verified complete.

## P2: No Test for Floating Panel Default or Clamped Position
- Status: open — missing gate
- Evidence: `web/app.js::clampPanel()` (lines 86-106) enforces 8 px margin and minimum 340×520 dimensions. No test exercises this logic at the three reference viewport sizes.
- Why it matters: A CSS change to the default panel position could place it off-screen with no gate catching it.
- Codex next action: Add a Playwright test that verifies `clampPanel()` keeps the panel within viewport bounds at the three reference viewport sizes.
- Release impact: polish for V1; low risk because panel is draggable.

## P2: No Layout Test for Bridge Host/Port Change Regression
- Status: open — missing gate
- Evidence: `web/app.js` makes fetch calls to relative paths served by the bridge. No test verifies that health-check and API URLs are derived from the configured bridge origin.
- Why it matters: If the bridge is reconfigured to a different port, the panel silently shows "bridge offline" with no actionable error.
- Codex next action: Inject the bridge origin into `web/index.html` or `app.js` at startup from the bridge config. Add a test confirming the health check URL is derived from the configured origin.
- Release impact: low risk for local V1; needed before any multi-host deployment.

---

## 6. JusPrin-to-Hermes Wording Audit

## P0: Web Surface Is Clean — No JusPrin/JusBot/Obico in web/
- Status: verified complete
- Evidence: Grep for `JusPrin|JusBot|Obico` across `web/**/*` — no matches. `tests/test_ui_static.py::test_web_surface_does_not_ship_jusprin_branding` enforces this on every test run.
- Why it matters: The only user-visible surface carries zero legacy branding.
- Codex next action: None.
- Release impact: verified complete.

## P0: hermes_slicer/ Backend Source Is Clean
- Status: verified complete
- Evidence: Grep for `JusPrin|JusBot|Obico` across `hermes_slicer/**/*` — no matches.
- Why it matters: Backend source carries zero JusPrin references.
- Codex next action: None.
- Release impact: verified complete.

## P1: JusPrin References in Planning/Research Docs Are Intentional and Correct
- Status: verified complete
- Evidence: All remaining JusPrin references are in appropriate contexts: `TASKS.md` (completed history), `README.md` (credits upstream/JusPrin correctly, explicitly contrasts HermesSlicer), `NOTICE` (required AGPL attribution), `.gitmodules` (required submodule entry), research docs, and the `FORBIDDEN_TEXT` tuple in scripts (defensive check that it must be absent). None indicate leaked product branding.
- Why it matters: Reframe is complete. No legacy copy in any user-facing path.
- Codex next action: If a future automated legacy-term lint is added, these files must be in the allowlist.
- Release impact: documentation only.

## P1: Panel Framing Reframe Is Fully Applied
- Status: verified complete
- Evidence: `README.md` states "not a JusPrin-style slicer settings chatbot." `ACTION_PLAN.md` reframe task marked `[x]` complete. `web/index.html` `aria-label` and `<h1>` confirm the reframe in the live UI.
- Why it matters: Product language is consistent from README to running UI.
- Codex next action: None.
- Release impact: verified complete.

## P2: No JusPrin-Branded Images or Assets Present
- Status: verified complete
- Evidence: `web/assets/` contains only Hermes-branded files: `hermes-orca-minimal.svg`, `hermes-orca-primary.svg`, `hermes-slicer-icon-32.png`, `hermes-slicer-icon-256.png`, `hermes-slicer-login.png`, `readme-hero.png`. No JusPrin or Obico images.
- Why it matters: No legacy visual identity in the product.
- Codex next action: None.
- Release impact: verified complete.

## P2: BRAND.md and brand_tokens.json Are Hermes-Only
- Status: verified complete
- Evidence: `BRAND.md` lists only Hermes + Orca assets. `config/brand_tokens.json` — three tokens: `background_primary: #08101c`, `accent_cyan: #00d8ff`, `accent_gold: #f7b93e`. `tests/test_ui_static.py::test_css_uses_brand_tokens` asserts all three values appear as CSS custom properties in `web/styles.css`.
- Why it matters: Brand consistency enforced across CSS, config, and tests.
- Codex next action: None.
- Release impact: verified complete.

---

## 7. Missing / Improvements Needed

## P1: No Web Frontend Build Tooling (Known V1 Design Decision)
- Status: open — known V1 design decision
- Evidence: `web/` contains only `index.html`, `app.js`, `styles.css`, and `assets/`. No `package.json`, no bundler, no build step.
- Why it matters: Correct for V1. Future complexity (TypeScript, component splitting) will require a migration.
- Codex next action: Document the "no bundler by design" decision in README developer section. If complexity grows, add a Vite build step behind a `Makefile` target.
- Release impact: polish / documentation for V1.

## P2: No Help Overlay or Onboarding Flow
- Status: open — missing V1 feature
- Evidence: `web/index.html` has no help overlay, tooltip tour, or onboarding step beyond the login gate. New users see quick-action buttons with no documentation for what tool IDs are.
- Why it matters: First-run UX gap. Users unfamiliar with tool IDs will not know what to enter.
- Codex next action: Add a collapsible "?" help section to `web/index.html` listing available tool IDs and brief descriptions, driven by the bridge's `bridge.actions` response.
- Release impact: polish for V1.

## P2: No Architecture Diagram in Documentation
- Status: open — missing artifact
- Evidence: No visual system diagram in `README.md` or project docs.
- Why it matters: New developers cannot quickly understand the runtime topology.
- Codex next action: Add the diagram from Section 8 below to `README.md` under an "Architecture" heading.
- Release impact: documentation only.

## P3: No CONTRIBUTING.md or Developer Setup Guide
- Status: open — missing doc
- Evidence: No `CONTRIBUTING.md` found in the project root.
- Why it matters: No clear path from clone to running panel for a new developer.
- Codex next action: Create `CONTRIBUTING.md` covering: prerequisites (Python 3.11+, OrcaSlicer path), `pip install -e .`, `python -m hermes_slicer.bridge`, opening `http://127.0.0.1:8765`, and the five proof screenshot checkpoints.
- Release impact: documentation only.

---

## 8. Architecture Diagram: OrcaSlicer → Panel → Bridge

```
┌──────────────────────────────────────────────────────────────────┐
│  User Browser  (localhost:8765)                                   │
│                                                                   │
│  ┌──────────────────────┐  session-locked  ┌───────────────────┐ │
│  │  auth-gate           │ ─── Sign In ───► │  panel            │ │
│  │  (Hermes Slicer      │                  │  (Hermes Agent    │ │
│  │   local-session      │                  │   Tool Console)   │ │
│  │   login)             │                  │  web/app.js       │ │
│  │  web/index.html      │                  └────────┬──────────┘ │
│  └──────────────────────┘                           │ fetch       │
│                                              /health /api/...     │
└─────────────────────────────────────────────────────┼────────────┘
                                                       │
                                         ┌─────────────▼───────────┐
                                         │  HermesSlicer Bridge    │
                                         │  Python  (port 8765)    │
                                         │  127.0.0.1 only         │
                                         │                         │
                                         │  hermes_slicer/         │
                                         │  ├─ bridge.py           │
                                         │  ├─ slicer.py           │
                                         │  │  (FLSUN resolver,    │
                                         │  │   validate_slice,    │
                                         │  │   export_gcode)      │
                                         │  └─ proof.py            │
                                         │     (ledger.jsonl)      │
                                         └──────────┬──────────────┘
                                                    │
                 ┌──────────────────────────────────┼──────────────────────┐
                 │                                  │                      │
    ┌────────────▼──────────┐      ┌────────────────▼────┐  ┌─────────────▼──────┐
    │  OrcaSlicer CLI       │      │  Hermes Agent       │  │  Proof / Evidence  │
    │  (subprocess)         │      │  v0.14.0            │  │  proof/ledger.jsonl│
    │                       │      │  (optional;         │  │  proof/runtime/    │
    │  --version probe      │      │  HERMES_AGENT_      │  │  proof/screenshots/│
    │  FLSUN profiles       │      │  ENABLED=1)         │  │                    │
    │  G-code export        │      │  integrations/      │  │                    │
    │  (gated by env var)   │      │  hermes-slicer/     │  │                    │
    └───────────────────────┘      └─────────────────────┘  └────────────────────┘

    Key design choices:
    - Browser panel served locally by Python bridge, not embedded in OrcaSlicer
    - All slicer interactions go through Python bridge, never directly from JS
    - G-code export gated behind HERMES_ENABLE_EXPORT_GCODE=1 (off by default)
    - Hermes Agent plugin routes tool requests to bridge; returns blocked result otherwise
    - Proof events written to proof/ledger.jsonl; panel reads via /api/proof/recent
```

---

## 9. Codex Next Actions (Ranked)

1. **[P1]** Set `HERMES_AGENT_ENABLED=1` and configure provider/health URL — unblocks live Hermes Agent bridge gate and enables real tool routing from the panel.
2. **[P1]** Add rendered-pixel browser screenshot gate (Playwright) — replaces CSS-math assertion with real render proof for the login geometry gate.
3. **[P1]** Add `proof/screenshots/computer-use-blocked.png` — capture the panel state when computer-use is blocked. Update `scripts/verify_screenshots.py`.
4. **[P2]** Add architecture diagram to `README.md` — copy diagram from Section 8 above.
5. **[P2]** Add help overlay to `web/index.html` — collapsible "?" section listing tool IDs with descriptions, driven by `bridge.actions` response.
6. **[P2]** Disable mic/stop buttons when Azure credentials are absent — add `disabled` + descriptive `title` attribute on bridge health check.
7. **[P2]** Add auto-refresh screenshot capture script — Playwright-based capture in `scripts/capture_screenshots.py`. Gate release checklist on screenshot freshness.
8. **[P3]** Create `CONTRIBUTING.md` — prerequisites, install steps, bridge startup, panel URL, and screenshot checkpoints.
9. **[P3]** Add floating panel position test (Playwright) — verifies `clampPanel()` within viewport bounds at three reference sizes.
10. **[P3]** Configure AS_USER bounded grant — set 4 required env vars to unblock AS_USER gate and MCP transport.
