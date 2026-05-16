# JusPrin Pattern Report

Date: 2026-05-16

## Source

- URL: https://github.com/TheSpaghettiDetective/JusPrin
- Local path: `upstream/JusPrin`
- Commit: `095fb665762ad4dbbb2bed155b3a728dd1a3bac2`
- License caution: Orca/Prusa-derived slicer code should be treated as AGPL-risk reference material unless a license decision allows reuse.

## Commands Run

```powershell
git submodule add --depth 1 https://github.com/TheSpaghettiDetective/JusPrin.git upstream/JusPrin
git -C upstream\JusPrin rev-parse HEAD
git -C upstream\JusPrin log -1 --pretty=format:'%H%n%s%n%ci'
rg --files upstream\JusPrin | Select-Object -First 40
```

Observed:

```text
095fb665762ad4dbbb2bed155b3a728dd1a3bac2
Update GitHub Actions workflow to reflect JusPrin branding in Flatpak build
2025-10-19 18:21:50 -0700
```

## Useful Patterns To Mine Next

- Natural-language intent to slicer setting/profile selection.
- AI assistant UX around slicing decisions.
- How an Orca fork represents settings and applies presets internally.
- Where cloud endpoints, auth, telemetry, or external services enter the flow.

## V1 Decision

JusPrin is now present as an upstream base under `upstream/JusPrin`, but V1 does not copy its code. Mine patterns and document exact source files first.

## Proof Completed

`proof/research/jusprin_file_map.md` now records the inspected assistant/settings files in the submodule. Further JusPrin work stays research-only unless a license decision permits copying implementation.
