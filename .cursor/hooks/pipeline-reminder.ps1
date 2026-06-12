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

$message = @"
[Pipeline checklist] Use inbox as source only, reference only assets/* in data.js, keep case id <-> assets folder slug consistent, verify gallery/video paths exist.
"@

$response = @{
  additional_context = $message
} | ConvertTo-Json -Compress

Write-Output $response
exit 0
