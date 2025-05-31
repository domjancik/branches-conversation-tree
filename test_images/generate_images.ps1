# Script to generate 50 images with unique timestamps
# Each image is saved with a timestamped filename

# Configuration
$apiUrl = "http://localhost:8888/v1/generation/text-to-image"
$totalImages = 50

# Ensure we have the body parameter from the existing session or define it
if (-not (Get-Variable -Name body -ErrorAction SilentlyContinue)) {
    Write-Warning "The `$body variable is not defined. Using a default prompt."
    $body = @{
        prompt = "Beautiful landscape with mountains and lakes"
        width = 512
        height = 512
    } | ConvertTo-Json
}

# Create output directory if it doesn't exist
$outputDir = ".\generated_images"
if (-not (Test-Path -Path $outputDir)) {
    New-Item -Path $outputDir -ItemType Directory | Out-Null
    Write-Host "Created output directory: $outputDir"
}

Write-Host "Starting generation of $totalImages images..." -ForegroundColor Cyan
$startTime = Get-Date

# Loop to generate images
for ($i = 1; $i -le $totalImages; $i++) {
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $filename = Join-Path -Path $outputDir -ChildPath "generated_image_${i}_${timestamp}.png"
    
    # Progress bar and info
    $percentComplete = ($i / $totalImages) * 100
    Write-Progress -Activity "Generating Images" -Status "Processing image $i of $totalImages" -PercentComplete $percentComplete
    Write-Host "[$i/$totalImages] Generating image..." -NoNewline
    
    try {
        # Make the API request
        $response = Invoke-RestMethod -Method Post -Uri $apiUrl -Body $body -ContentType "application/json"
        
        # Extract the base64 image data
        $imageData = $response.url -replace '^data:image/png;base64,', ''
        
        # Convert to bytes and save
        [System.Convert]::FromBase64String($imageData) | Set-Content -Path $filename -AsByteStream
        
        Write-Host " Saved as $(Split-Path $filename -Leaf)" -ForegroundColor Green
    }
    catch {
        Write-Host " Failed!" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
    }
    
}

Write-Progress -Activity "Generating Images" -Completed
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host "`nImage generation completed!" -ForegroundColor Cyan
Write-Host "Total images generated: $totalImages" -ForegroundColor Yellow
Write-Host "Total time: $($duration.TotalMinutes.ToString('0.00')) minutes" -ForegroundColor Yellow
Write-Host "Images saved in: $outputDir" -ForegroundColor Yellow

