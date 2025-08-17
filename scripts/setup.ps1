# PowerShell Setup Script for YouTube to Audio Recording Script
# This script installs the required dependencies for the YouTube audio extraction functionality

param(
    [switch]$InstallSystemDeps = $false,
    [switch]$CreateVenv = $false,
    [string]$VenvName = "youtube-audio-env"
)

Write-Host "YouTube to Audio Recording Script - Setup" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>$null
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Check if pip is available
try {
    pip --version | Out-Null
    Write-Host "✓ pip is available" -ForegroundColor Green
} catch {
    Write-Host "✗ pip not found. Please ensure pip is installed." -ForegroundColor Red
    exit 1
}

# Create virtual environment if requested
if ($CreateVenv) {
    Write-Host "`nCreating virtual environment: $VenvName" -ForegroundColor Yellow
    python -m venv $VenvName
    
    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & ".\$VenvName\Scripts\Activate.ps1"
    
    Write-Host "✓ Virtual environment created and activated" -ForegroundColor Green
}

# Install Python dependencies
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$requirementsPath = Join-Path $scriptDir "requirements.txt"

if (Test-Path $requirementsPath) {
    pip install -r $requirementsPath
    Write-Host "✓ Python dependencies installed" -ForegroundColor Green
} else {
    Write-Host "Installing core dependencies manually..." -ForegroundColor Yellow
    pip install yt-dlp requests python-dotenv
    Write-Host "✓ Core dependencies installed" -ForegroundColor Green
}

# Install system dependencies if requested
if ($InstallSystemDeps) {
    Write-Host "`nInstalling system dependencies..." -ForegroundColor Yellow
    
    # Check if chocolatey is available
    try {
        choco --version | Out-Null
        Write-Host "Using Chocolatey to install ffmpeg..." -ForegroundColor Yellow
        choco install ffmpeg -y
        Write-Host "✓ ffmpeg installed via Chocolatey" -ForegroundColor Green
    } catch {
        # Try winget as alternative
        try {
            winget --version | Out-Null
            Write-Host "Using winget to install ffmpeg..." -ForegroundColor Yellow
            winget install Gyan.FFmpeg
            Write-Host "✓ ffmpeg installed via winget" -ForegroundColor Green
        } catch {
            Write-Host "⚠ Could not install ffmpeg automatically." -ForegroundColor Yellow
            Write-Host "Please install ffmpeg manually:" -ForegroundColor Yellow
            Write-Host "  1. Download from: https://ffmpeg.org/download.html" -ForegroundColor White
            Write-Host "  2. Extract to a folder" -ForegroundColor White
            Write-Host "  3. Add the bin folder to your PATH" -ForegroundColor White
            Write-Host "  Or use: winget install Gyan.FFmpeg" -ForegroundColor White
        }
    }
} else {
    Write-Host "`nTo install system dependencies (ffmpeg), run:" -ForegroundColor Yellow
    Write-Host "  .\setup.ps1 -InstallSystemDeps" -ForegroundColor White
    Write-Host "Or manually install ffmpeg from: https://ffmpeg.org/download.html" -ForegroundColor White
}

# Test dependencies
Write-Host "`nTesting dependencies..." -ForegroundColor Yellow

# Test yt-dlp
try {
    $ytDlpVersion = yt-dlp --version 2>$null
    Write-Host "✓ yt-dlp available: $ytDlpVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ yt-dlp not found in PATH" -ForegroundColor Red
}

# Test ffmpeg
try {
    ffmpeg -version 2>$null | Select-Object -First 1 | ForEach-Object {
        if ($_ -match "ffmpeg version (.+?)\s") {
            Write-Host "✓ ffmpeg available: $($Matches[1])" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "✗ ffmpeg not found in PATH" -ForegroundColor Red
}

# Create sample .env file
$envFile = Join-Path $scriptDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "`nCreating sample .env file..." -ForegroundColor Yellow
@"
# Environment configuration for YouTube to Audio Recording Script

# Directory where audio recordings will be stored
RECORDINGS_DIR=C:\Users\magne\Documents\Branches-ConversationTree\audio_recordings

# Data API URL (adjust port if different)
DATA_API_URL=http://localhost:8000

# Audio Processing API URL (adjust port if different)  
AUDIO_PROCESSOR_URL=http://localhost:8001

# Database path (for reference)
DB_PATH=C:\Users\magne\Documents\Branches-ConversationTree\conversation_tree.db
"@
    Write-Host "✓ Sample .env file created at: $envFile" -ForegroundColor Green
    Write-Host "  Please review and adjust the configuration as needed." -ForegroundColor Yellow
}

Write-Host "`n=============================================" -ForegroundColor Green
Write-Host "Setup completed!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Review the .env file and adjust paths/URLs as needed" -ForegroundColor White
Write-Host "2. Ensure the data API and audio processing services are running" -ForegroundColor White
Write-Host "3. Test the script with: python youtube_to_recording.py <youtube_url>" -ForegroundColor White
Write-Host "`nExample usage:" -ForegroundColor Yellow
Write-Host 'python youtube_to_recording.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"' -ForegroundColor White

# Show command options
Write-Host "`nSetup script options:" -ForegroundColor Cyan
Write-Host "  -InstallSystemDeps  : Install system dependencies (ffmpeg)" -ForegroundColor White  
Write-Host "  -CreateVenv         : Create Python virtual environment" -ForegroundColor White
Write-Host "  -VenvName <name>    : Specify virtual environment name" -ForegroundColor White
