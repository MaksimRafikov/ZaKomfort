param()

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
  exit 0
}

$message = @"
[UI checklist] Verify contrast, focus states, responsive widths (375/768/1024/1440), and no emoji icons.
"@

$response = @{
  additional_context = $message
} | ConvertTo-Json -Compress

Write-Output $response
exit 0
