# MDPS Startup Script
# Run: powershell -ExecutionPolicy Bypass -File "start.ps1"

$ErrorActionPreference = 'Stop'
$ROOT = $PSScriptRoot
$PY   = "python"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Starting MDPS Streamlit Dashboard on http://localhost:8501" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

& $PY -m streamlit run (Join-Path $ROOT "mdps-streamlit\app.py")
