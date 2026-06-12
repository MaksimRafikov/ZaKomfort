param()

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
  exit 0
}

$filePath = ""
try {
  $payload = $raw | ConvertFrom-Json
  if ($payload.PSObject.Properties.Name -contains "path" -and $null -ne $payload.path) {
    $filePath = [string]$payload.path
  } elseif ($payload.PSObject.Properties.Name -contains "file" -and $null -ne $payload.file) {
    $filePath = [string]$payload.file
  }
} catch {
  [Console]::Out.Write($raw)
  exit 0
}

if ($filePath -match '(?i)\.(env|key|pem)$|\.env\.|credentials|secret') {
  [Console]::Error.WriteLine("[Catalog security] Reading a sensitive file: $filePath")
  [Console]::Error.WriteLine("[Catalog security] Do not paste secrets into chat, commits, or js/data.js.")
}

[Console]::Out.Write($raw)
exit 0
