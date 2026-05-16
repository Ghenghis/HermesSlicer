Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (Test-Path -LiteralPath "proof\ledger.jsonl") {
    Remove-Item -LiteralPath "proof\ledger.jsonl"
}

python scripts\smoke_bridge.py
if ($LASTEXITCODE -ne 0) { throw "smoke_bridge.py failed with exit code $LASTEXITCODE" }

python scripts\write_flsun_profile_proof.py
if ($LASTEXITCODE -ne 0) { throw "write_flsun_profile_proof.py failed with exit code $LASTEXITCODE" }

python scripts\validate_submodules.py
if ($LASTEXITCODE -ne 0) { throw "validate_submodules.py failed with exit code $LASTEXITCODE" }

python integrations\hermes_agent_tool.py health
if ($LASTEXITCODE -ne 0) { throw "hermes_agent_tool.py failed with exit code $LASTEXITCODE" }

python scripts\validate_proof.py
if ($LASTEXITCODE -ne 0) { throw "validate_proof.py failed with exit code $LASTEXITCODE" }

python scripts\verify_screenshots.py
if ($LASTEXITCODE -ne 0) { throw "verify_screenshots.py failed with exit code $LASTEXITCODE" }

python scripts\redaction_scan.py .
if ($LASTEXITCODE -ne 0) { throw "redaction_scan.py failed with exit code $LASTEXITCODE" }
