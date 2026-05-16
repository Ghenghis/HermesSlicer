# HermesSlicer V1 Plan

## Decision

Build bridge-first. OrcaSlicer remains the normal GUI; HermesSlicer runs as a local web panel and bridge on `127.0.0.1:8765`.

## Day-One Slice

1. Initialize repo, branch, safety ignores, and proof folders.
2. Implement the bridge with `/health`, `/api/actions`, `/api/orca/version`, `/api/slice/dry-run`, `/api/voices/azure/en`, `/api/chat/message`, and proof ledger writes.
3. Implement the dark floating panel with hide, drag, resize, chat, quick actions, voice assignment, and proof drawer.
4. Add a Hermes integration example that calls the bridge.
5. Produce proof reports, health JSON, screenshots, and redaction scan output.

## Scope Lock

No deep OrcaSlicer fork, no printer start, no public network exposure, no raw credential logging.
