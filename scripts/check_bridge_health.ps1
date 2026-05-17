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
Invoke-RestMethod -Uri "$BridgeUrl/health" -Method Get
