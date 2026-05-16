# Orchestrator Decisions

Date: 2026-05-16

## Decision

Use a local sidecar architecture for V1:

`OrcaSlicer GUI -> browser floating panel -> localhost bridge -> Orca executable/profile resources -> FLSUN export preflight -> Hermes Agent tool shim -> proof evidence`

## Why

- The contract kit explicitly prefers a local overlay/sidecar and bridge over a deep Orca UI fork.
- OrcaSlicer is installed locally, and a non-destructive `--info` probe against `samples/test_cube.stl` succeeds.
- Public Orca release notes and local behavior show CLI support exists, but the CLI is not polished enough to make a GUI fork the first move.
- Hermes Agent supports plugin/MCP style external tools, so the bridge can be exposed as a safe local tool boundary.

## Scope

V1 ships health, action listing, profile folder listing, Orca executable check, FLSUN T1/V400/S1 inventory, FLSUN export preflight, dry-run request validation, generated Azure English voice catalog, local chat stub, agent voice persistence, Hermes Agent tool shim, API contract drift tests, upstream submodule validation, and proof ledger.

Printer upload/start remains disabled.
