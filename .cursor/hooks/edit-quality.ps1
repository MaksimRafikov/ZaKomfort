param()

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
  exit 0
}

$lower = $raw.ToLowerInvariant()
$messages = @()

$isJsTouch = $lower.Contains(".js") -or $lower.Contains("js/")
$isStyleTouch = $lower.Contains(".css") -or $lower.Contains("css/")
$isHtmlTouch = $lower.Contains(".html")

if ($isJsTouch -and $raw -match '(?i)\bconsole\.(log|debug|info|warn)\s*\(') {
  $messages += "[Edit quality] console.* call detected in JS changes. Remove debug logging before publishing."
}

if ($isJsTouch -and $lower.Contains("inbox/")) {
  $messages += "[Edit quality] Do not reference inbox/* from production code or js/data.js. Use assets/* only."
}

if ($isStyleTouch -or $isHtmlTouch) {
  $messages += "[Edit quality] Check contrast, focus states, and responsive widths (375/768/1024/1440)."
}

if ($messages.Count -eq 0) {
  exit 0
}

$response = @{
  additional_context = ($messages -join " ")
} | ConvertTo-Json -Compress

Write-Output $response
exit 0
