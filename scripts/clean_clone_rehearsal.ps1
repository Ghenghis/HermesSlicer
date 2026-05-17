param(
    [string]$RemoteUrl = "https://github.com/Ghenghis/HermesSlicer.git",
    [string]$Branch = "main",
    [string]$ParentDir = (Join-Path $env:TEMP "HermesSlicer-rehearsals"),
    [int]$Port = 8765,
    [string]$ReportPath = "",
    [switch]$SkipProof
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:report = [ordered]@{
    status = "started"
    started_at = (Get-Date).ToString("o")
    remote_url = $RemoteUrl
    branch = $Branch
    clone_path = $null
    proof_skipped = [bool]$SkipProof
    bridge_url = "http://127.0.0.1:$Port"
    steps = @()
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$ScriptBlock
    )

    Write-Host "==> $Name"
    try {
        & $ScriptBlock
        if ($LASTEXITCODE -ne 0) {
            throw "$Name failed with exit code $LASTEXITCODE"
        }
        $script:report.steps += [ordered]@{ name = $Name; status = "passed" }
    }
    catch {
        $script:report.steps += [ordered]@{ name = $Name; status = "failed"; error = $_.Exception.Message }
        throw
    }
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$cloneDir = Join-Path $ParentDir "HermesSlicer-v1-$stamp"
$bridgeProcess = $null
$script:report.clone_path = $cloneDir

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
        $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($listener) {
            throw "Port $Port is already in use by process $($listener.OwningProcess). Re-run with -SkipProof or choose an isolated -Port."
        }

        $bridgeProcess = Start-Process -FilePath python -ArgumentList "-m", "hermes_slicer.bridge", "--host", "127.0.0.1", "--port", "$Port" -WorkingDirectory $cloneDir -WindowStyle Hidden -PassThru
        Start-Sleep -Seconds 2

        Invoke-Step "proof regeneration" {
            $env:HERMES_SLICER_BRIDGE_URL = "http://127.0.0.1:$Port"
            powershell -ExecutionPolicy Bypass -File scripts\regenerate_proof.ps1 -BridgeUrl "http://127.0.0.1:$Port"
        }
    }

    Invoke-Step "redaction scan" {
        python scripts\redaction_scan.py .
    }

    Write-Host "CLEAN CLONE REHEARSAL PASSED"
    Write-Host "Clone path: $cloneDir"
    $script:report.status = "passed"
}
catch {
    $script:report.status = "failed"
    $script:report.error = $_.Exception.Message
    throw
}
finally {
    if ($bridgeProcess -and -not $bridgeProcess.HasExited) {
        Stop-Process -Id $bridgeProcess.Id -Force
    }
    $script:report.finished_at = (Get-Date).ToString("o")
    if (-not [string]::IsNullOrWhiteSpace($ReportPath)) {
        $resolvedReport = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ReportPath)
        $reportDir = Split-Path -Parent $resolvedReport
        New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
        $json = ($script:report | ConvertTo-Json -Depth 8) + [Environment]::NewLine
        [System.IO.File]::WriteAllText($resolvedReport, $json, [System.Text.UTF8Encoding]::new($false))
    }
    Pop-Location
}
