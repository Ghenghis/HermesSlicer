# JusPrin File Map

Date: 2026-05-16

## Source State

- Upstream: `https://github.com/TheSpaghettiDetective/JusPrin`
- Local submodule: `upstream/JusPrin`
- Pinned commit: `095fb665762ad4dbbb2bed155b3a728dd1a3bac2`
- License posture: AGPL-family Orca-derived slicer code is research reference only unless HermesSlicer deliberately adopts compatible licensing.

## Commands Run

```powershell
rg -n "AGPL|JusBot|Just Print|AI|license|JusPrin" README.md LICENSE.txt
rg -n "JusPrin(LoginDialog|ChatPanel|PresetConfigUtils|View3D|PlateUtils|NotificationManager|PricingPlanDialog|Utils)" src\slic3r\CMakeLists.txt src\slic3r\GUI\GUI_App.cpp
Get-ChildItem src\slic3r\GUI\JusPrin | Select-Object Name,Length
rg -n "authorize|hide_navbar|WEBVIEW|SCRIPT_MESSAGE|token|BaseUrl|pricing|JusPrin" src\slic3r\GUI\JusPrin
rg -n "class|typedef|using|trigger|handler|notification|preset|slice|export|plate|webview|chat|message|Event|Config" src\slic3r\GUI\JusPrin\JusPrinChatPanel.hpp src\slic3r\GUI\JusPrin\JusPrinChatPanel.cpp src\slic3r\GUI\JusPrin\JusPrinNotificationManager.cpp src\slic3r\GUI\JusPrin\JusPrinPresetConfigUtils.cpp
rg -n "export-gcode|export_gcode|--slice|slice|load_settings|preset|config" src\OrcaSlicer.cpp doc\developer-reference\Preset-and-bundle.md doc\developer-reference\How-to-create-profiles.md doc\developer-reference\slicing-hierarchy.md
```

Observed:

```text
JusPrin README describes GenAI slicing assistance and AGPL licensing.
src/slic3r/CMakeLists.txt lines 579-594 register the JusPrin GUI files.
src/slic3r/GUI/GUI_App.cpp line 118 includes the login dialog, and line 3773 instantiates it.
src/slic3r/GUI/JusPrin contains 16 focused C++/header files for chat, auth, preset/config, plate/project, overlay, notification, pricing, and URL utilities.
src/OrcaSlicer.cpp contains CLI config loading, slice actions, and G-code export flow.
```

## Product Lessons

JusPrin validates the same high-level product direction we are using for HermesSlicer V1: keep the slicer as the source of truth, put the assistant in a side panel, and expose a narrow action surface for settings, project state, slicing, export, and notifications.

HermesSlicer should not copy the C++ implementation. The useful pattern is architectural: a chat surface sends typed actions, native code validates those actions, the slicer remains in charge of presets and export, and assistant-visible state is generated from slicer/project data.

## High-Value Files

`README.md`

- Lines 4-23 frame the user problem: GenAI selects/optimizes slicing settings so users avoid manual parameter hunting.
- Lines 47-57 state the AGPL licensing chain. This is the key reason HermesSlicer currently treats JusPrin as a pattern source, not copied code.

`src/slic3r/CMakeLists.txt`

- Lines 579-594 list the complete JusPrin GUI integration set. This gives us the file boundary for future research:
  - `JusPrinLoginDialog`
  - `JusPrinChatPanel`
  - `JusPrinPresetConfigUtils`
  - `JusPrinView3D`
  - `JusPrinPlateUtils`
  - `JusPrinNotificationManager`
  - `JusPrinPricingPlanDialog`
  - `JusPrinUtils`

`src/slic3r/GUI/GUI_App.cpp`

- Line 118 includes `JusPrinLoginDialog`.
- Line 3773 creates the login dialog. This shows JusPrin integrated directly into the Orca GUI startup/application flow, while HermesSlicer V1 intentionally stays outside the Orca process as a local sidecar.

`src/slic3r/GUI/JusPrin/JusPrinChatPanel.hpp`

- Lines 24-60 define a wxPanel with separate void and JSON handler maps.
- Lines 31-40 define assistant event methods for auto-orient, model-object changes, native errors, notifications, focus, and slicing progress.
- Lines 68-87 name the chat-facing action categories: presets, edited presets, plate rendering, preset selection, config application, project state, slicing, export, orient, undo, preview switch, badges, and arrange.

`src/slic3r/GUI/JusPrin/JusPrinChatPanel.cpp`

- Lines 30-39 create and wire the embedded web view.
- Lines 73-98 register supported action names.
- Lines 102-168 send native slicer events back into the assistant surface.
- Lines 203-267 expose presets, edited presets, rendered plate view, current project data, preset selection, and config application.
- Lines 298-339 call native slicer operations such as slice-all, export G-code, auto-orient, undo, preview, and arrange.
- Lines 401-411 advertise supported actions to the embedded chat page.
- Lines 414-457 parse action messages and dispatch to the correct handler map.

HermesSlicer implication: keep `/api/action` as the typed dispatch entry, and grow it toward a stable action schema rather than scattered ad hoc endpoints. Each action should return JSON and write a redacted proof event.

`src/slic3r/GUI/JusPrin/JusPrinPresetConfigUtils.cpp`

- Lines 10-25 serialize preset metadata and config.
- Lines 29-88 collect selected and edited print/filament/printer presets.
- Lines 122-172 apply config and select presets through Orca's native preset tabs.

HermesSlicer implication: the FLSUN resolver should treat Orca presets as named, typed artifacts: machine/printer, process/print, and filament. Export must prove compatibility before enabling real G-code.

`src/slic3r/GUI/JusPrin/JusPrinPlateUtils.cpp`

- Lines 97-155 render plate/thumbnail data.
- Lines 297-414 extract plate and current-project JSON, including model/object feature state.

HermesSlicer implication: V1 can stay with sample STL proof, but V2 should expose model/project metadata as assistant-readable JSON before allowing automated slicing recommendations.

`src/slic3r/GUI/JusPrin/JusPrinView3D.cpp` and `.hpp`

- Header lines 71-96 subclass `View3D` and hold the chat panel.
- Source lines 351-394 initialize the overlay and bind canvas/resize events.
- Source lines 409-449 show, hide, resize, change view, and update notification badges.

HermesSlicer implication: our floating web panel is a correct lower-risk V1 substitute for in-process `View3D` integration. The long-term Orca-native panel would need this class of direct GUI integration.

`src/slic3r/GUI/JusPrin/JusPrinNotificationManager.cpp` and `.hpp`

- Header line 9 subclasses `NotificationManager`.
- Source lines 8-21 forward slicing progress into chat events.
- Source lines 24-101 forward validation, upload, slicing, plater, simplify, import, and export notifications.

HermesSlicer implication: the bridge ledger is our notification spine for now. Later, the panel should render progress/error events from real Orca/CLI runs using the same redacted-event pattern.

`src/slic3r/GUI/JusPrin/JusPrinLoginDialog.cpp`

- Lines 31-32 build an OAuth login URL.
- Lines 46-53 bind web view navigation and script-message events.
- Lines 89-105 parse/store the access token.

HermesSlicer implication: avoid token handling in V1. If authentication is added later, keep tokens outside proof logs and expose only boolean capability state.

`src/slic3r/GUI/JusPrin/JusPrinPricingPlanDialog.cpp`

- Lines 16-20 build a pricing web view URL.

HermesSlicer implication: no pricing or external service UI belongs in the V1 local sidecar.

`src/slic3r/GUI/JusPrin/JusPrinUtils.cpp`

- Line 6 reads the JusPrin base URL from app config.

HermesSlicer implication: bridge origin and external integration URLs should remain explicit config, never hard-coded remote service assumptions.

`src/OrcaSlicer.cpp`

- Lines 1102-1110 read CLI profile/config options such as `load_settings` and `load_filaments`.
- Lines 1216-1218 read the numeric `slice` option, which explains why `--slice` without an integer failed in local probing.
- Lines 4721-4737 branch into the slice action.
- Lines 5069-5071 perform G-code export for sliced FFF output.
- Lines 6093-6106 print CLI help and describe configuration-loading precedence.

HermesSlicer implication: real export should not be wired until we can generate or point Orca at proven settings/config input and run a safe profile-loading probe.

`doc/developer-reference/Preset-and-bundle.md`

- Lines 7-24 define the important preset types: print/process, filament, and printer.
- Lines 28-37 explain that compatibility filtering is contextual inside a `PresetBundle`.
- Lines 43-47 distinguish selected and edited presets.

HermesSlicer implication: profile preflight must prove a machine/process/filament tuple, not just list available files.

`doc/developer-reference/How-to-create-profiles.md`

- Line 35 documents process profile naming that combines layer height, preset name, vendor, printer, and variant.
- Line 277 identifies printer variants as `machine` profiles.

HermesSlicer implication: FLSUN aliases should resolve to canonical Orca names like `FLSun T1 0.4 nozzle`, `0.20mm Standard @FLSun T1`, and a compatible filament preset.

`doc/developer-reference/slicing-hierarchy.md`

- Lines 7-21 map the GUI slice action down into plater and print-object slicing.

HermesSlicer implication: the current sidecar should keep using Orca/Prusa CLI probes for proof. A future in-process fork would need direct plater/print integration.

## Work Queue From This Map

1. Keep V1 as a localhost sidecar and do not merge AGPL C++ into product code.
2. Expand `api_contract.openapi.yaml` around typed actions instead of proliferating undocumented endpoints.
3. Finish FLSUN profile preflight around canonical printer/process/filament triples.
4. Add assistant-readable project/model metadata only after the safe profile resolver is proven.
5. Defer auth, pricing, and remote service flows until there is an explicit privacy and licensing decision.
