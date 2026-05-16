Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Invoke-RestMethod -Uri "http://127.0.0.1:8765/health" -Method Get
