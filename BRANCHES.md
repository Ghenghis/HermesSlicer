# Branch Strategy

Active branch:

```text
feature/hermes-orca-floating-panel-v1
```

This branch contains the working V1 sidecar: localhost bridge, floating panel, proof bundle, Hermes tool shim, and pinned upstream base submodules.

## Next Branches

Create these from `feature/hermes-orca-floating-panel-v1` after the bootstrap commit lands:

```powershell
git switch -c research/jusprin-pattern-mining
git switch -c integration/hermes-agent-tooling
git switch -c feature/flsun-profile-resolver
```

Use them for:

- `research/jusprin-pattern-mining`: inspect JusPrin assistant/settings patterns without copying AGPL code into product code.
- `integration/hermes-agent-tooling`: adapt the `slicer_bridge` shim to the actual Hermes plugin/MCP install path.
- `feature/flsun-profile-resolver`: resolve T1/V400/S1 machine, process, and filament profiles before enabling G-code export.

## Remote

Target remote:

```text
origin https://github.com/Ghenghis/HermesSlicer.git
```

Push the active branch with:

```powershell
git push -u origin feature/hermes-orca-floating-panel-v1
```
