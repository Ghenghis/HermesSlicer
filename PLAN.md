# HermesSlicer V1 Plan

## Decision

Build bridge-first. OrcaSlicer remains the normal GUI; HermesSlicer runs as a local web panel and bridge on `127.0.0.1:8765`.

## Day-One Slice

1. Initialize repo, branch, safety ignores, and proof folders.
2. Implement the bridge with `/health`, `/api/actions`, `/api/orca/version`, `/api/slice/dry-run`, `/api/slice/export-preflight`, `/api/voices/azure/en`, `/api/hermes-agent/tool-request`, and proof ledger writes.
3. Implement the dark floating panel with hide, drag, resize, Hermes Agent tool requests, quick actions, voice assignment, and proof drawer.
4. Add a Hermes Agent plugin wrapper that registers `hermes_agent_tools` under the `hermes_agent` toolset.
5. Resolve local Orca FLSUN T1, V400, and S1 machine/process/filament tuples before allowing G-code export.
6. Produce proof reports, health JSON, screenshots, and redaction scan output.

## Scope Lock

No deep OrcaSlicer fork, no printer start, no public network exposure, no raw credential logging.

## Current Acceptance Branch

`codex/v1-acceptance-consolidation` merges the bootstrap, JusPrin research, Hermes Agent integration, and FLSUN resolver work.
