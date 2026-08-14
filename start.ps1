# VITALS & MDPS Startup Script
# Run: powershell -ExecutionPolicy Bypass -File "start.ps1"

$ErrorActionPreference = 'Stop'
$ROOT = $PSScriptRoot
$PY   = "C:\Users\ankit\Downloads\msds\apps\api\.venv\Scripts\python.exe"

if (-not (Test-Path $PY)) {
  $PY = "python"
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Starting VITALS & MDPS Server on http://localhost:8000" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

& $PY (Join-Path $ROOT "serve.py") 8000
