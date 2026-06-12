param()

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
  exit 0
}

$lower = $raw.ToLowerInvariant()
$isPipelineTouch = $lower.Contains("js/data.js") -or $lower.Contains("assets/") -or $lower.Contains("inbox/")
if (-not $isPipelineTouch) {
  exit 0
}

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$scriptPath = Join-Path $projectRoot "scripts/validate-cases.py"

if (-not (Test-Path $scriptPath)) {
  $msg = "[Pipeline validation] scripts/validate-cases.py is missing."
  @{ additional_context = $msg } | ConvertTo-Json -Compress | Write-Output
  exit 0
}

$output = & python $scriptPath 2>&1
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
  $ok = "[Pipeline validation] OK: data.js links and case structure look consistent."
  @{ additional_context = $ok } | ConvertTo-Json -Compress | Write-Output
  exit 0
}

$joined = ($output | Out-String).Trim()
if ([string]::IsNullOrWhiteSpace($joined)) {
  $joined = "Validation failed with no output."
}

$msg = "[Pipeline validation] Issues detected:`n$joined"
@{ additional_context = $msg } | ConvertTo-Json -Compress | Write-Output
exit 0
