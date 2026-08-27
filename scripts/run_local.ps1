# Starts the Shtrader LA Python engine via the local FastAPI server.
# Usage:  .\scripts\run_local.ps1   (or `npm run engine`)
# The web console can then be run in another terminal with `npm run dev`,
# or both at once with `npm run start:all`.

$ErrorActionPreference = "Stop"

$RepoRoot = Join-Path $PSScriptRoot ".."
$BindAddress = "0.0.0.0"
$Port = 8000
$Probe = "http://127.0.0.1:$Port/health"
$Python = $null
foreach ($candidate in @(".venv312", ".venv")) {
    $candidateExe = Join-Path $RepoRoot "$candidate/Scripts/python.exe"
    if (Test-Path $candidateExe) {
        $Python = $candidateExe
        break
    }
}
if (-not $Python) {
    $systemPython = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
    if ($systemPython) { $Python = $systemPython }
}
if (-not $Python) {
    Write-Error "Python not found. Create the project venv first, e.g.:
    python -m venv .venv312
    .venv312/Scripts/python -m pip install -r requirements.txt"
    exit 1
}


# If our engine is already serving /health on this port (leftover from an earlier
# run or another `npm run engine`), do NOT spin up a duplicate uvicorn. Duplicate
# processes fight over the port and, under `concurrently`, one dying process can
# take down the web server too. Reuse the running instance instead and exit clean.
try {
    $existing = Invoke-RestMethod -Uri $Probe -TimeoutSec 2 -ErrorAction Stop
    if ($existing.status -eq "ok") {
        Write-Host "Shtrader LA engine already running at http://127.0.0.1:$Port (provider: $($existing.provider))." -ForegroundColor Green
        Write-Host "Reusing the running instance - nothing to start." -ForegroundColor DarkGray
        exit 0
    }
} catch {
    # Nothing listening, or it's not ours - fall through and start fresh.
}

$Requirements = Join-Path $RepoRoot "requirements.txt"
# Best-effort: ensure the API deps are present. Fails fast if python can't import them.
# The stderr redirect needs try/catch: under $ErrorActionPreference = "Stop",
# Windows PowerShell 5.1 turns native stderr output (the ImportError traceback)
# into a terminating NativeCommandError before the installer below could run.
$depsOk = $true
try {
    & $Python -c "import fastapi,uvicorn,pydantic" 2>$null
    if ($LASTEXITCODE -ne 0) { $depsOk = $false }
} catch {
    $depsOk = $false
}
if (-not $depsOk) {
    Write-Host "Installing requirements.txt into the venv ..." -ForegroundColor Cyan
    & $Python -m pip install -r $Requirements
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host ""
Write-Host "Shtrader LA engine API starting at http://$BindAddress`:$Port" -ForegroundColor Green
Write-Host "Health:   $Probe" -ForegroundColor DarkGray
Write-Host "Chat:     POST http://127.0.0.1:$Port/api/v1/chat" -ForegroundColor DarkGray
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

& $Python -m uvicorn shtrader_la.api.app:app --host $BindAddress --port $Port
