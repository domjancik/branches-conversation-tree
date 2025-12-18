# Read .env file and set environment variables
Get-Content .env | ForEach-Object {
  $name, $value = $_.split('=')
  if ([string]::IsNullOrWhiteSpace($name) || $name.Contains('#')) {
    return
  }
  Set-Content env:\$name $value
}

# Configuration
$MaxRestartAttempts = 10  # Maximum number of restart attempts
$RestartDelay = 5  # Seconds to wait before restarting
$HealthCheckInterval = 10  # Seconds between health checks
$ApiPort = 8888  # API port to check

function Test-ApiHealth {
    <#
    .SYNOPSIS
    Check if the API is responding to health checks
    #>
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$ApiPort/docs" -Method Get -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

function Start-StreamDiffusionApi {
    <#
    .SYNOPSIS
    Start the StreamDiffusion API process
    #>
    Write-Host "Starting StreamDiffusion API..." -ForegroundColor Green
    
    Push-Location "$env:SD_API_PATH"
    try {
        # Try to find conda Python executable in the environment
        # Common locations for conda environments
        $condaEnvPath = "$env:SD_API_PATH\envs\vl_streamdiffusion"
        $pythonExe = "$condaEnvPath\python.exe"
        
        if (Test-Path $pythonExe) {
            # Use Python from conda environment directly
            Write-Host "Using Python from conda environment: $pythonExe" -ForegroundColor Cyan
            $process = Start-Process -FilePath $pythonExe -ArgumentList "examples\optimal-performance\api.py" -PassThru -NoNewWindow
        }
        else {
            # Fallback: use conda run (if available) or system Python
            Write-Host "Conda environment Python not found, using conda run..." -ForegroundColor Yellow
            $condaCmd = "conda run -n vl_streamdiffusion python examples\optimal-performance\api.py"
            $process = Start-Process -FilePath "cmd" -ArgumentList "/c", $condaCmd -PassThru -NoNewWindow
        }
        
        return $process
    }
    finally {
        Pop-Location
    }
}

function Stop-StreamDiffusionApi {
    <#
    .SYNOPSIS
    Stop the StreamDiffusion API process gracefully
    #>
    param([System.Diagnostics.Process]$Process)
    
    if ($Process -and -not $Process.HasExited) {
        Write-Host "Stopping StreamDiffusion API (PID: $($Process.Id))..." -ForegroundColor Yellow
        try {
            $Process.Kill()
            $Process.WaitForExit(5000)  # Wait up to 5 seconds
        }
        catch {
            Write-Host "Error stopping process: $_" -ForegroundColor Red
        }
    }
}

# Main execution loop with restart logic
$restartCount = 0
$process = $null

while ($restartCount -lt $MaxRestartAttempts) {
    try {
        # Start the API process
        $process = Start-StreamDiffusionApi
        
        if (-not $process) {
            Write-Host "Failed to start API process" -ForegroundColor Red
            $restartCount++
            if ($restartCount -lt $MaxRestartAttempts) {
                Write-Host "Waiting $RestartDelay seconds before restart attempt $($restartCount + 1)..." -ForegroundColor Yellow
                Start-Sleep -Seconds $RestartDelay
            }
            continue
        }
        
        Write-Host "API process started (PID: $($process.Id))" -ForegroundColor Green
        Write-Host "Monitoring process health (checking every $HealthCheckInterval seconds)..." -ForegroundColor Cyan
        
        # Monitor the process
        while (-not $process.HasExited) {
            Start-Sleep -Seconds $HealthCheckInterval
            
            # Check if process is still running
            if ($process.HasExited) {
                Write-Host "API process exited with code $($process.ExitCode)" -ForegroundColor Yellow
                break
            }
            
            # Optional: Check API health (uncomment if you want HTTP health checks)
            # if (-not (Test-ApiHealth)) {
            #     Write-Host "API health check failed, restarting..." -ForegroundColor Yellow
            #     Stop-StreamDiffusionApi -Process $process
            #     break
            # }
        }
        
        # Process exited, check if we should restart
        if ($process.ExitCode -ne 0) {
            Write-Host "Process exited with error code $($process.ExitCode)" -ForegroundColor Red
        }
        
        $restartCount++
        
        if ($restartCount -lt $MaxRestartAttempts) {
            Write-Host "Restarting API (attempt $restartCount/$MaxRestartAttempts)..." -ForegroundColor Yellow
            Write-Host "Waiting $RestartDelay seconds before restart..." -ForegroundColor Yellow
            Start-Sleep -Seconds $RestartDelay
        }
        else {
            Write-Host "Maximum restart attempts ($MaxRestartAttempts) reached. Exiting." -ForegroundColor Red
            break
        }
    }
    catch {
        Write-Host "Error in main loop: $_" -ForegroundColor Red
        if ($process) {
            Stop-StreamDiffusionApi -Process $process
        }
        $restartCount++
        
        if ($restartCount -lt $MaxRestartAttempts) {
            Write-Host "Waiting $RestartDelay seconds before restart attempt $($restartCount + 1)..." -ForegroundColor Yellow
            Start-Sleep -Seconds $RestartDelay
        }
    }
}

# Cleanup
if ($process -and -not $process.HasExited) {
    Write-Host "Stopping API process..." -ForegroundColor Yellow
    Stop-StreamDiffusionApi -Process $process
}

Write-Host "Script ended." -ForegroundColor Cyan
