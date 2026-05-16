# Branch Strategy

Active branch:

```text
codex/v1-acceptance-consolidation
```

This branch merges the working V1 sidecar, upstream research maps, Hermes Agent plugin tooling, FLSUN profile preflight, and refreshed proof bundle.

## Source Branches

These branches were created from `feature/hermes-orca-floating-panel-v1` and then merged into `codex/v1-acceptance-consolidation`:

- `research/jusprin-pattern-mining`: JusPrin assistant/settings pattern map without copying AGPL code into product code.
- `integration/hermes-agent-tooling`: Hermes Agent `hermes_agent_tools` plugin wrapper aligned to upstream `plugin.yaml` plus `register(ctx)` behavior.
- `feature/flsun-profile-resolver`: T1/V400/S1 profile resolver and export preflight gate.

## Bootstrap Branch

`feature/hermes-orca-floating-panel-v1` remains the clean bootstrap/proof branch at the first working sidecar commit.

## Remote

Target remote:

```text
origin https://github.com/Ghenghis/HermesSlicer.git
```

Push the active branch with:

```powershell
git push -u origin codex/v1-acceptance-consolidation
```

Public landing branch:

```text
main
```

`main` is the GitHub landing branch for the integrated V1 acceptance state. It is mirrored from `codex/v1-acceptance-consolidation` after proof regeneration and redaction scan pass. Keep the root license as a release-blocking decision before tagging a final release.
