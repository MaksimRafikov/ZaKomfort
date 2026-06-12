param()

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
  exit 0
}

$prompt = ""
try {
  $payload = $raw | ConvertFrom-Json
  foreach ($field in @("prompt", "content", "message")) {
    if ($payload.PSObject.Properties.Name -contains $field -and $null -ne $payload.$field) {
      $prompt = [string]$payload.$field
      break
    }
  }
} catch {
  [Console]::Out.Write($raw)
  exit 0
}

if (-not [string]::IsNullOrWhiteSpace($prompt)) {
  $secretPatterns = @(
    'sk-[a-zA-Z0-9]{20,}',
    'ghp_[a-zA-Z0-9]{36,}',
    'AKIA[A-Z0-9]{16}',
    'xox[bpsa]-[a-zA-Z0-9-]+',
    '-----BEGIN (RSA |EC )?PRIVATE KEY-----'
  )

  foreach ($pattern in $secretPatterns) {
    if ($prompt -match $pattern) {
      [Console]::Error.WriteLine("[Catalog security] Potential secret detected in the prompt.")
      [Console]::Error.WriteLine("[Catalog security] Remove tokens and keys before submitting.")
      break
    }
  }
}

[Console]::Out.Write($raw)
exit 0
