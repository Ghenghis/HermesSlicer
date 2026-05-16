# Floating Panel Report

Date: 2026-05-16

## Sources

- `G:\Github\Hermes_OrcaSlicer_Codex_Contract_Kit\ui\FLOATING_PANEL_SPEC.md`
- `G:\Github\Hermes_OrcaSlicer_Codex_Contract_Kit\ui\panel_mockup.html`

## Decision

Use a browser-served local panel for V1 rather than embedding inside OrcaSlicer. This gives the user a working panel today and avoids a large GUI fork.

## Implemented

- Dark-first UI at `web/index.html`.
- Hide/show dock button.
- Drag handle.
- Browser resize.
- Text chat.
- Mic state stub.
- Stop speaking button.
- Agent selector and rename field.
- Azure English voice dropdown per agent.
- Provider badge.
- Proof drawer.
- Slicer status through bridge health.

## Risks

- Browser panel is not OS-level always-on-top. A Tauri/Electron shell can wrap the same web UI later if needed.
- Voice capture/playback is stubbed until Azure credentials are present.
