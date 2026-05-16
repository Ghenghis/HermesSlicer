# Bridge Smoke Report

Date: 2026-05-16

Command:

```powershell
python scripts\smoke_bridge.py
```

Observed:

- `/health`: HTTP 200
- `/api/actions`: HTTP 200
- `/api/orca/profiles`: HTTP 200, 126 local Orca profile entries found
- `/api/orca/flsun`: HTTP 200, FLSun T1, V400, and S1 inventory found
- `/api/voices/azure/en`: HTTP 200, 12 generated English voices
- `/api/hermes/proof-mcp`: HTTP 200, returns local Hermes Proof MCP status artifact
- `/api/orca/version`: HTTP 200, `--info` probe succeeded on `samples/test_cube.stl`
- `/api/slice/dry-run`: HTTP 200, request validated without writing G-code
- `/api/slice/export-preflight`: HTTP 200, resolved a compatible FLSUN machine/process/filament tuple without writing G-code
- `/api/hermes-agent/tool-request`: HTTP 200, routed a Hermes Agent tool request to `slice.export_preflight`
- `/api/chat/message`: HTTP 200, compatibility alias only for Hermes Agent tool request routing
- `/api/tts/speak`: HTTP 200, safely blocked because Azure Speech credentials are absent
- `/api/action` with `bridge.health`: HTTP 200
- `/api/action` with `orca.flsun_inventory`: HTTP 200
- `/api/action` with `slice.export_preflight`: HTTP 200
- `/api/action` with `hermes_agent.tool_request`: HTTP 200
- `/api/action` with `tts.speak`: HTTP 200, safely blocked
- `/api/action` with invalid action: HTTP 400
- `scripts/write_flsun_profile_proof.py`: wrote profile inventory, matrix, and export preflight proof
- `scripts/validate_submodules.py`: verified nine pinned upstream submodules and wrote `proof/runtime/submodule-stack.json`
- `integrations/hermes_agent_tool.py health`: HTTP 200 through the local Hermes Agent tool shim and wrote `proof/runtime/hermes-tool-health.json`
- `integrations/hermes_agent_tool.py export_preflight`: HTTP 200 through the local Hermes Agent tool shim and wrote `proof/runtime/hermes-tool-export_preflight.json`
- `integrations/hermes_agent_tool.py tool_request`: HTTP 200 through the local Hermes Agent tool shim and wrote `proof/runtime/hermes-tool-tool_request.json`
- `proof/screenshots/login-hermes-slicer.jpg`: Hermes Slicer local-session gate verified in browser
- `proof/screenshots/hermes-agent-tools.jpg`: Hermes Agent tool console verified in browser with readable tool IDs

Decision: bridge smoke passed.
