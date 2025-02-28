# Read .env file and set environment variables
Get-Content .env | foreach {
  $name, $value = $_.split('=')
  if ([string]::IsNullOrWhiteSpace($name) || $name.Contains('#')) {
    continue
  }
  Set-Content env:\$name $value
}

cd $env:FOOOCUS_API_PATH
& "$env:FOOOCUS_API_PATH\venv\Scripts\activate.ps1"
python main.py


