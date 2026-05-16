# Orca API Bridge Report

Date: 2026-05-16

## Sources

- https://github.com/AFKFelix/orca-slicer-api
- https://wiki.bambuddy.cool/features/slicer-api/
- `G:\Github\Hermes_OrcaSlicer_Codex_Contract_Kit\bridge\SLICER_BRIDGE_SPEC.md`

## Source State

Command run:

```powershell
git ls-remote https://github.com/AFKFelix/orca-slicer-api.git HEAD refs/tags/v0.3.0
```

Observed output:

```text
2cc1e0f5ea7efd05bc3b547b3f50b14e9f7e6747	HEAD
b50531d7552aa9fdea9d63ed8d25cc136b856dc8	refs/tags/v0.3.0
```

- License note: AGPL-3.0.

Command run:

```powershell
python scripts\smoke_bridge.py
```

Observed output excerpt:

```text
health: HTTP 200
profiles: HTTP 200
flsun: HTTP 200
invalid: HTTP 400
```

## Observed

- The project wraps OrcaSlicer CLI in a REST service.
- It supports STL, STEP, and 3MF slicing, profile storage, async jobs, and Docker images.
- Its own README warns that no authentication or authorization is implemented and it should not be exposed publicly without security layers.

## Decision

Do not vendor AFKFelix code in V1. Use it as a pattern only. HermesSlicer implements a smaller local bridge with strict localhost binding, action allowlist, path validation, disabled export by default, and proof logging.

## Risks

- Useful async slicing patterns may be worth reusing later after license review.
- Docker/headless Orca paths remain a fallback if Windows GUI executable behavior becomes unreliable.
