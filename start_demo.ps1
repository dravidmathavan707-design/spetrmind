$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Project = Join-Path $Root 'SIH26055'
$Dashboard = Join-Path $Project 'dashboard\react-app'
$Python = Join-Path $Root '.venv\Scripts\python.exe'

if (!(Test-Path $Python)) {
    $Python = (Get-Command python).Source
}

if (!(Test-Path (Join-Path $Dashboard 'node_modules'))) {
    Push-Location $Dashboard
    npm install
    Pop-Location
}

Start-Process powershell -WorkingDirectory $Project -ArgumentList @(
    '-NoExit', '-Command',
    "& '$Python' -m uvicorn api.main:app --host 127.0.0.1 --port 8000"
)

Start-Process powershell -WorkingDirectory $Dashboard -ArgumentList @(
    '-NoExit', '-Command',
    'npm run dev -- --host 127.0.0.1 --port 5173'
)

Write-Host 'SpectraMind demo is starting.'
Write-Host 'Open http://127.0.0.1:5173/ after both terminals are ready.'
