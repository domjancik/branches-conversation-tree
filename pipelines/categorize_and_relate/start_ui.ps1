# Starts the FastAPI server (uvicorn) and the static UI server in separate PowerShell windows.
# Usage: Run from the pipeline root (pipelines/categorize_and_relate)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$serverDir = Join-Path $root 'server'
$webDir = Join-Path $root 'web'

# API window
$apiCmd = "Set-Location '$serverDir'; $Env:FAST_WHISPER_MODEL='small'; $Env:WHISPER_DEVICE='cpu'; uv run -m uvicorn main:app --reload --port 8000"
Start-Process -FilePath pwsh -ArgumentList '-NoExit','-Command', $apiCmd | Out-Null

Start-Sleep -Seconds 2

# UI window
$webCmd = "Set-Location '$webDir'; python -m http.server 3001"
Start-Process -FilePath pwsh -ArgumentList '-NoExit','-Command', $webCmd | Out-Null

Start-Process 'http://localhost:3001'
Write-Host 'Started API (http://localhost:8000) and UI (http://localhost:3001)'
