# PowerShell wrapper for the audio pipeline CLI
param([Parameter(ValueFromRemainingArguments)]$args)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

uv run python cli.py @args
