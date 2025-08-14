<#
.SYNOPSIS
  Run categorize-and-relate pipeline using Ollama.

.DESCRIPTION
  - Loads and templates prompt.md
  - Injects input text (from -InputPath or stdin) into the prompt
  - Optionally injects existing categories from a JSON file
  - Supports simple {{KEY}} templating replacements
  - Calls `ollama generate` with model (default: gemma3:4b)
  - Allows dry-run to preview the final prompt before sending to the model

.PARAMETER InputPath
  Path to a text file with the raw input to be categorized. If omitted, stdin will be used.

.PARAMETER CategoriesPath
  Optional path to a JSON file with pre-existing categories. Injected as {{CATEGORIES_JSON}} or {{CATEGORIES_BULLETS}} if present in prompt; otherwise appended as a "Known categories" section.

.PARAMETER Var
  Optional list of key=value pairs for templating replacements. Example: -Var "PROJECT=Demo" -Var "AUTHOR=Alice"

.PARAMETER VarsJson
  Optional path to a JSON file with a flat object of key -> value for templating.

.PARAMETER Model
  Ollama model name (default: "gemma3:4b").

.PARAMETER Temperature
  Sampling temperature (default: 0).

.PARAMETER Seed
  Random seed for determinism (default: 42).

.PARAMETER OutputPath
  If provided, writes the model response to this file.

.PARAMETER DryRun
  If set, outputs the final rendered prompt and exits without calling Ollama.

.EXAMPLE
  # Read input from file, inject categories.json, run and save output
  ./run.ps1 -InputPath input.txt -CategoriesPath categories.json -OutputPath result.json

.EXAMPLE
  # Read input from stdin, preview final prompt
  Get-Content input.txt | ./run.ps1 -DryRun

.NOTES
  Requires: PowerShell 7+, Ollama installed and running locally.
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$InputPath,

  [Parameter(Mandatory = $false)]
  [string]$CategoriesPath,

  [Parameter(Mandatory = $false)]
  [string[]]$Var,

  [Parameter(Mandatory = $false)]
  [string]$VarsJson,

  [Parameter(Mandatory = $false)]
  [string]$Model = "gemma3:4b",

  [Parameter(Mandatory = $false)]
  [double]$Temperature = 0,

  [Parameter(Mandatory = $false)]
  [int]$Seed = 42,

  [Parameter(Mandatory = $false)]
  [string]$OutputPath,

  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-InputText {
  param([string]$Path)
  if ($Path) {
    if (-not (Test-Path -Path $Path -PathType Leaf)) {
      throw "InputPath not found: $Path"
    }
    return [System.IO.File]::ReadAllText($Path)
  }
  # Read from stdin if available
  if ($MyInvocation.ExpectingInput) {
    $all = [System.Text.StringBuilder]::new()
    foreach ($line in $input) { [void]$all.AppendLine($line) }
    return $all.ToString()
  }
  throw "No input provided. Specify -InputPath or pipe content via stdin."
}

function Get-TemplateVars {
  param(
    [string[]]$Pairs,
    [string]$JsonPath
  )
  $map = @{}
  if ($JsonPath) {
    if (-not (Test-Path -Path $JsonPath -PathType Leaf)) { throw "VarsJson not found: $JsonPath" }
    $jsonObj = Get-Content -Raw -Path $JsonPath | ConvertFrom-Json
    if ($jsonObj -is [System.Collections.IDictionary]) {
      foreach ($k in $jsonObj.Keys) { $map[$k] = [string]$jsonObj[$k] }
    } else {
      throw "VarsJson must deserialize to a flat object (key -> value)."
    }
  }
  if ($Pairs) {
    foreach ($p in $Pairs) {
      if ($p -notmatch '^[^=]+=.+$') { throw "Invalid -Var format. Use key=value. Got: $p" }
      $kv = $p.Split('=',2)
      $map[$kv[0]] = $kv[1]
    }
  }
  return $map
}

function Render-Template {
  param(
    [string]$Template,
    [hashtable]$Vars
  )
  $rendered = $Template
  foreach ($k in $Vars.Keys) {
    $placeholder = '{{' + $k + '}}'
    # Use simple -replace with escaped regex for literal replacement
    $pattern = [Regex]::Escape($placeholder)
    $value = [string]$Vars[$k]
    $rendered = [Regex]::Replace($rendered, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $value })
  }
  return $rendered
}

function Build-CategoriesBlocks {
  param([string]$CategoriesJsonRaw)
  # Try to produce bullets as well (best-effort)
  $bullets = $null
  try {
    $parsed = $CategoriesJsonRaw | ConvertFrom-Json -ErrorAction Stop
    $lines = @()
    if ($parsed -is [System.Collections.IEnumerable]) {
      foreach ($item in $parsed) {
        $id = $item.id
        $label = $item.category ?? $item.label ?? $item.name
        $desc = $item.description ?? $item.summary
        $line = "- [${id}] ${label}"
        if ($desc) { $line += ": $desc" }
        $lines += $line
      }
    } elseif ($parsed -is [System.Collections.IDictionary]) {
      foreach ($key in $parsed.Keys) {
        $val = $parsed[$key]
        $label = $val.category ?? $val.label ?? $val.name ?? $key
        $desc = $val.description ?? $val.summary
        $line = "- [${key}] ${label}"
        if ($desc) { $line += ": $desc" }
        $lines += $line
      }
    }
    if ($lines.Count -gt 0) { $bullets = ($lines -join "`n") }
  } catch { }
  return [pscustomobject]@{
    Json    = $CategoriesJsonRaw
    Bullets = $bullets
  }
}

function Inject-Into-Prompt {
  param(
    [string]$Prompt,
    [string]$InputText,
    [string]$CategoriesJsonRaw
  )
  $vars = @{
    'RAW_TEXT' = $InputText
  }

  if ($CategoriesJsonRaw) {
    $blocks = Build-CategoriesBlocks -CategoriesJsonRaw $CategoriesJsonRaw
    $vars['CATEGORIES_JSON'] = $blocks.Json
    if ($blocks.Bullets) { $vars['CATEGORIES_BULLETS'] = $blocks.Bullets }
  }

  # Primary injection: replace {{RAW_TEXT}} or fallback to legacy placeholder
  $rendered = Render-Template -Template $Prompt -Vars $vars

  if ($rendered -match '<PASTE RAW TEXT HERE>') {
    $rendered = $rendered -replace [Regex]::Escape('<PASTE RAW TEXT HERE>'), [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $InputText }
  }

  # Categories handling: if no placeholders present and we have categories, append a section before the Input block
  if ($CategoriesJsonRaw) {
    $hasJsonPh = $rendered -match [Regex]::Escape('{{CATEGORIES_JSON}}')
    $hasBulPh  = $rendered -match [Regex]::Escape('{{CATEGORIES_BULLETS}}')
    if (-not ($hasJsonPh -or $hasBulPh)) {
      $append = "`nKnown categories (optional, provided by data source):`n``````json`n$($blocks.Json)`n``````".Replace("``````","```")
      # Try to place it just before the Input: section
      if ($rendered -match "`nInput:\s*`n\"\"\"") {
        $rendered = $rendered -replace "(`n)Input:(\s*`n\"\"\")", ([System.Text.RegularExpressions.MatchEvaluator]{ param($m) "$append$($m.Groups[1].Value)Input:$($m.Groups[2].Value)" })
      } else {
        $rendered += $append
      }
    }
  }

  return $rendered
}

# Locate prompt.md relative to this script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$promptPath = Join-Path $scriptDir 'prompt.md'
if (-not (Test-Path -Path $promptPath -PathType Leaf)) {
  throw "prompt.md not found at $promptPath"
}
$promptTemplate = Get-Content -Raw -Path $promptPath

# Read inputs
$inputText = Read-InputText -Path $InputPath

$categoriesRaw = $null
if ($CategoriesPath) {
  if (-not (Test-Path -Path $CategoriesPath -PathType Leaf)) { throw "CategoriesPath not found: $CategoriesPath" }
  $categoriesRaw = Get-Content -Raw -Path $CategoriesPath
}

# Extra template vars
$templateVars = Get-TemplateVars -Pairs $Var -JsonPath $VarsJson

# First inject standard variables, then any extra template vars
$rendered = Inject-Into-Prompt -Prompt $promptTemplate -InputText $inputText -CategoriesJsonRaw $categoriesRaw
if ($templateVars.Count -gt 0) {
  $rendered = Render-Template -Template $rendered -Vars $templateVars
}

if ($DryRun.IsPresent) {
  Write-Output $rendered
  return
}

# Prepare Ollama generate call
# Build options as JSON
$options = @{ temperature = $Temperature; seed = $Seed } | ConvertTo-Json -Compress

# Call ollama generate; capture stdout and stderr
try {
  $response =  ollama run $Model --options $options -p $rendered 2>&1
} catch {
  throw "Failed to invoke ollama generate. Ensure Ollama is installed and running. Error: $($_.Exception.Message)"
}

if ($LASTEXITCODE -ne 0) {
  throw "ollama generate exited with code $LASTEXITCODE. Output:`n$response"
}

if ($OutputPath) {
  $outDir = Split-Path -Parent $OutputPath
  if ($outDir -and -not (Test-Path -Path $outDir -PathType Container)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
  Set-Content -Path $OutputPath -Value $response -NoNewline
  Write-Host "Saved response to $OutputPath" -ForegroundColor Green
} else {
  Write-Output $response
}

