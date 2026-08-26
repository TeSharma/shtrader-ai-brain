# Starts the Shtrader LA Python engine via the local FastAPI server.
# Usage:  .\scripts\run_local.ps1   (or `npm run engine`)
# The web console can then be run in another terminal with `npm run dev`,
# or both at once with `npm run start:all`.

$ErrorActionPreference = "Stop"

$RepoRoot = Join-Path $PSScriptRoot ".."
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$BindAddress = "0.0.0.0"
$Port = 8000
$Probe = "http://127.0.0.1:$Port/health"

if (-not (Test-Path $Python)) {
    Write-Error "Python venv not found at $Python. Create it first, e.g.:
    python -m venv .venv
    .venv\Scripts\python -m pip install -r requirements.txt"
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
& $Python -c "import fastapi,uvicorn,pydantic" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing requirements.txt into .venv ..." -ForegroundColor Cyan
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