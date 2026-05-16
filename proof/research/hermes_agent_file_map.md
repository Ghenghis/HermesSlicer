# Hermes Agent File Map

Date: 2026-05-16

## Source State

- Upstream: `https://github.com/NousResearch/hermes-agent`
- Local submodule: `upstream/hermes-agent`
- Pinned tag: `v2026.5.16`
- Pinned commit: `a91a57fa5a13d516c38b07a141a9ce8a3daabeb0`
- License posture: MIT, but copied code still needs notice discipline. This branch keeps HermesSlicer-authored glue.

## Commands Run

```powershell
rg -n "class PluginManifest|PluginManifest\(|plugin.yaml|provides_tools|provides" upstream\hermes-agent\hermes_cli\plugins.py
Get-Content upstream\hermes-agent\hermes_cli\plugins.py | Select-Object -Skip 300 -First 40
Get-Content upstream\hermes-agent\tools\registry.py | Select-Object -Skip 220 -First 190
Get-Content upstream\hermes-agent\hermes_cli\plugins.py | Select-Object -Skip 800 -First 110
Get-Content upstream\hermes-agent\plugins\spotify\plugin.yaml
Get-Content upstream\hermes-agent\plugins\google_meet\plugin.yaml
```

Observed:

```text
Directory plugins require plugin.yaml plus __init__.py with register(ctx).
PluginContext.register_tool requires name, toolset, schema, and handler.
Tool handlers are dispatched as handler(args, **kwargs).
Standalone plugins are opt-in through plugins.enabled.
Project plugins are scanned only when HERMES_ENABLE_PROJECT_PLUGINS is set.
```

## High-Value Files

`upstream/hermes-agent/hermes_cli/plugins.py`

- Lines 19-20 document the required directory plugin shape: `plugin.yaml` plus `__init__.py` with `register(ctx)`.
- Lines 317-339 define `PluginContext.register_tool(name, toolset, schema, handler, ...)`.
- Lines 814-819 show project plugin discovery under `.hermes/plugins` only when `HERMES_ENABLE_PROJECT_PLUGINS` is enabled.
- Lines 885-910 show standalone plugins are opt-in via `plugins.enabled`.

`upstream/hermes-agent/tools/registry.py`

- Lines 234-270 define the canonical registry API.
- Lines 390-397 dispatch tools as `handler(args, **kwargs)`.
- Lines 563 onward include helper patterns for JSON-safe tool results.

`upstream/hermes-agent/model_tools.py`

- Lines 179-198 import built-in tools and then load plugins.
- Lines 263 onward filter tool definitions by active toolset.

`upstream/hermes-agent/toolsets.py`

- Lines 683 onward infer plugin toolsets from the live registry, not from YAML-only metadata.

`upstream/hermes-agent/pyproject.toml`

- Line 10 requires Python `>=3.11`.
- Line 205 exposes the installed CLIs: `hermes`, `hermes-agent`, and `hermes-acp`.

## Implementation Decisions

- `integrations/hermes_agent_tool.py` now registers `slicer_bridge` with `toolset="hermes_orca"`, a schema object, and a `handler(args, **kwargs)` compatible function.
- `integrations/hermes-slicer/` is the installable directory plugin shape with `plugin.yaml` and `__init__.py`.
- `integrations/hermes_plugin.yaml` is kept as a manifest reference without unsupported `entry` or `toolsets` keys.
- The bridge is not started by Hermes. The tool returns a blocked JSON result if `http://127.0.0.1:8765` is unavailable.
- `HERMES_SLICER_ROOT` and `HERMES_SLICER_BRIDGE_URL` provide explicit runtime location/configuration when the plugin folder is copied outside this repo.
