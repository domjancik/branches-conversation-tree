# Run all required services

Start-Process -FilePath "pwsh" -ArgumentList ".\run_api.ps1" -WorkingDirectory ".\data_store"
Start-Process -FilePath "pwsh" -ArgumentList ".\run_audio_processing.ps1" -WorkingDirectory ".\audio-llm-processing"
