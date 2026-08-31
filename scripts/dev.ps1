# AI Quality Analytics Platform — Windows dev commands
# Usage: .\scripts\dev.ps1 install | api-dev | web-dev | test

param(
    [Parameter(Position = 0)]
    [ValidateSet("install", "api-dev", "web-dev", "worker-dev", "test", "lint")]
    [string]$Command = "install"
)

$Root = Split-Path -Parent $PSScriptRoot
$ErrorActionPreference = "Stop"

function Install-All {
    Push-Location "$Root\packages\evaluation-engine"
    uv sync --dev
    Pop-Location

    Push-Location "$Root\apps\api"
    uv sync --dev
    Pop-Location

    Push-Location "$Root\apps\web"
    npm install
    Pop-Location
}

function Start-ApiDev {
    Push-Location "$Root\apps\api"
    uv run uvicorn has_api.main:app --reload --host 0.0.0.0 --port 8000
}

function Start-WebDev {
    Push-Location "$Root\apps\web"
    npm run dev
}

function Start-WorkerDev {
    Push-Location "$Root\apps\api"
    uv run arq has_api.workers.settings.WorkerSettings
}

function Invoke-Tests {
    Push-Location "$Root\packages\evaluation-engine"
    uv run pytest
    Pop-Location

    Push-Location "$Root\apps\api"
    uv run pytest
    Pop-Location

    Push-Location "$Root\apps\web"
    npm run test
    Pop-Location
}

function Invoke-Lint {
    Push-Location "$Root\apps\api"
    uv run ruff check .
    Pop-Location

    Push-Location "$Root\packages\evaluation-engine"
    uv run ruff check .
    Pop-Location

    Push-Location "$Root\apps\web"
    npm run lint
    Pop-Location
}

switch ($Command) {
    "install"    { Install-All }
    "api-dev"    { Start-ApiDev }
    "web-dev"    { Start-WebDev }
    "worker-dev" { Start-WorkerDev }
    "test"       { Invoke-Tests }
    "lint"       { Invoke-Lint }
}
