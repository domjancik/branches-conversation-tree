# Read .env file and set environment variables
Get-Content .env | foreach {
  $name, $value = $_.split('=')
  if ([string]::IsNullOrWhiteSpace($name) || $name.Contains('#')) {
    continue
  }
  Set-Content env:\$name $value
}

cd "$env:SD_API_PATH"
conda activate envs\vl_streamdiffusion\
python examples\optimal-performance\api.py
