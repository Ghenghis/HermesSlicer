param(
    [string]$BridgeUrl = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($BridgeUrl)) {
    if ($env:HERMES_SLICER_BRIDGE_URL) {
        $BridgeUrl = $env:HERMES_SLICER_BRIDGE_URL
    }
    else {
        $BridgeUrl = "http://127.0.0.1:8765"
    }
}

$BridgeUrl = $BridgeUrl.TrimEnd("/")
$env:HERMES_SLICER_BRIDGE_URL = $BridgeUrl

if (Test-Path -LiteralPath "proof\ledger.jsonl") {
    Remove-Item -LiteralPath "proof\ledger.jsonl"
}

powershell -ExecutionPolicy Bypass -File scripts\check_bridge_health.ps1 -BridgeUrl $BridgeUrl
if ($LASTEXITCODE -ne 0) { throw "check_bridge_health.ps1 failed with exit code $LASTEXITCODE" }

python scripts\write_hermes_proof_mcp_status.py
if ($LASTEXITCODE -ne 0) { throw "write_hermes_proof_mcp_status.py failed with exit code $LASTEXITCODE" }

python scripts\smoke_bridge.py
if ($LASTEXITCODE -ne 0) { throw "smoke_bridge.py failed with exit code $LASTEXITCODE" }

python scripts\write_flsun_profile_proof.py
if ($LASTEXITCODE -ne 0) { throw "write_flsun_profile_proof.py failed with exit code $LASTEXITCODE" }

python scripts\validate_submodules.py
if ($LASTEXITCODE -ne 0) { throw "validate_submodules.py failed with exit code $LASTEXITCODE" }

python tests\test_api_contract.py
if ($LASTEXITCODE -ne 0) { throw "test_api_contract failed with exit code $LASTEXITCODE" }

python integrations\hermes_agent_tool.py health
if ($LASTEXITCODE -ne 0) { throw "hermes_agent_tool.py failed with exit code $LASTEXITCODE" }

python integrations\hermes_agent_tool.py export_preflight
if ($LASTEXITCODE -ne 0) { throw "hermes_agent_tool.py export_preflight failed with exit code $LASTEXITCODE" }

python integrations\hermes_agent_tool.py tool_request
if ($LASTEXITCODE -ne 0) { throw "hermes_agent_tool.py tool_request failed with exit code $LASTEXITCODE" }

python scripts\smoke_hermes_plugin.py
if ($LASTEXITCODE -ne 0) { throw "smoke_hermes_plugin.py failed with exit code $LASTEXITCODE" }

python scripts\write_hermes_computer_use_proof.py
if ($LASTEXITCODE -ne 0) { throw "write_hermes_computer_use_proof.py failed with exit code $LASTEXITCODE" }

python scripts\verify_screenshots.py
if ($LASTEXITCODE -ne 0) { throw "verify_screenshots.py failed with exit code $LASTEXITCODE" }

python scripts\verify_login_geometry.py
if ($LASTEXITCODE -ne 0) { throw "verify_login_geometry.py failed with exit code $LASTEXITCODE" }

python scripts\redaction_scan.py .
if ($LASTEXITCODE -ne 0) { throw "redaction_scan.py failed with exit code $LASTEXITCODE" }

python scripts\write_v1_release_checklist.py
if ($LASTEXITCODE -ne 0) { throw "write_v1_release_checklist.py failed with exit code $LASTEXITCODE" }

python scripts\validate_proof.py
if ($LASTEXITCODE -ne 0) { throw "validate_proof.py failed with exit code $LASTEXITCODE" }
