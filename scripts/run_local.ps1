# Starts the Shtrader LA Python engine via the local FastAPI server.
# Usage:  .\scripts\run_local.ps1   (or `npm run engine`)
# The web console can then be run in another terminal with `npm run dev`,
# or both at once with `npm run start:all`.

$ErrorActionPreference = "Stop"

$RepoRoot = Join-Path $PSScriptRoot ".."
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Error "Python venv not found at $Python. Create it first, e.g.:
    python -m venv .venv
    .venv\Scripts\python -m pip install -r requirements.txt"
    exit 1
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
Write-Host "Shtrader LA engine API starting at http://0.0.0.0:8000" -ForegroundColor Green
Write-Host "Health:   http://127.0.0.1:8000/health" -ForegroundColor DarkGray
Write-Host "Chat:     POST http://127.0.0.1:8000/api/v1/chat" -ForegroundColor DarkGray
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

& $Python -m uvicorn shtrader_la.api.app:app --host 0.0.0.0 --port 8000