param(
    [string]$RemoteUrl = "https://github.com/Ghenghis/HermesSlicer.git",
    [string]$Branch = "main",
    [string]$ParentDir = (Join-Path $env:TEMP "HermesSlicer-rehearsals"),
    [switch]$SkipProof
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$ScriptBlock
    )

    Write-Host "==> $Name"
    & $ScriptBlock
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$cloneDir = Join-Path $ParentDir "HermesSlicer-v1-$stamp"
$bridgeProcess = $null

New-Item -ItemType Directory -Force -Path $ParentDir | Out-Null

Invoke-Step "git clone --recurse-submodules" {
    git clone --branch $Branch --recurse-submodules $RemoteUrl $cloneDir
}

Push-Location $cloneDir
try {
    Invoke-Step "unit tests" {
        python -m unittest discover -s tests
    }

    Invoke-Step "compileall" {
        python -m compileall hermes_slicer integrations scripts tests
    }

    Invoke-Step "submodule validation" {
        python scripts\validate_submodules.py
    }

    if (-not $SkipProof) {
        $listener = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($listener) {
            throw "Port 8765 is already in use by process $($listener.OwningProcess). Re-run with -SkipProof or free the port for an isolated proof rehearsal."
        }

        $bridgeProcess = Start-Process -FilePath python -ArgumentList "-m", "hermes_slicer.bridge", "--host", "127.0.0.1", "--port", "8765" -WorkingDirectory $cloneDir -WindowStyle Hidden -PassThru
        Start-Sleep -Seconds 2

        Invoke-Step "proof regeneration" {
            powershell -ExecutionPolicy Bypass -File scripts\regenerate_proof.ps1
        }
    }

    Invoke-Step "redaction scan" {
        python scripts\redaction_scan.py .
    }

    Write-Host "CLEAN CLONE REHEARSAL PASSED"
    Write-Host "Clone path: $cloneDir"
}
finally {
    if ($bridgeProcess -and -not $bridgeProcess.HasExited) {
        Stop-Process -Id $bridgeProcess.Id -Force
    }
    Pop-Location
}
