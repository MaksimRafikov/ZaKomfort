param()

function Remove-QuotedStrings {
  param([string]$Text)

  $result = [regex]::Replace($Text, "(?s)'([^']|'')*'", "''")
  $result = [regex]::Replace($result, '(?s)"([^"]|"")*"', '""')
  return $result
}

function Test-GitHookBypass {
  param([string]$Command)

  if ($Command -notmatch '(?i)\bgit\s+(commit|push|merge|cherry-pick|rebase|am)\b') {
    return $false
  }

  $stripped = Remove-QuotedStrings -Text $Command

  if ($stripped -match '(?i)(?:^|\s)--no-verify(?:\s|$)') { return $true }
  if ($stripped -match '(?i)(?:^|\s)-c\s+core\.hookspath\b') { return $true }
  if ($stripped -match '(?i)core\.hookspath\s*=') { return $true }

  return $false
}

$raw = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($raw)) {
  Write-Output '{ "permission": "allow" }'
  exit 0
}

try {
  $payload = $raw | ConvertFrom-Json
} catch {
  Write-Output '{ "permission": "allow" }'
  exit 0
}

$command = ""
if ($payload.PSObject.Properties.Name -contains "command" -and $null -ne $payload.command) {
  $command = [string]$payload.command
}

if ([string]::IsNullOrWhiteSpace($command)) {
  Write-Output '{ "permission": "allow" }'
  exit 0
}

if (Test-GitHookBypass -Command $command) {
  $response = @{
    permission    = "deny"
    user_message  = "Обход git-хуков запрещен. Не используйте --no-verify и core.hooksPath."
    agent_message = "Shell hook blocked a git hook-bypass flag."
  } | ConvertTo-Json -Compress
  Write-Output $response
  exit 0
}

$dangerPatterns = @(
  '(?i)\bgit\s+reset\s+--hard\b',
  '(?i)\bgit\s+checkout\s+--\b',
  '(?i)\brm\s+-rf\b',
  '(?i)\bdel\s+/f\b',
  '(?i)\bformat\s+[a-z]:\b',
  '(?i)\bRemove-Item\b.*\b-Recurse\b.*\b-Force\b'
)

foreach ($pattern in $dangerPatterns) {
  if ($command -match $pattern) {
    $response = @{
      permission   = "ask"
      user_message = "Команда выглядит потенциально разрушительной. Проверьте ее перед запуском."
      agent_message = "Shell hook requested confirmation for a high-risk command."
    } | ConvertTo-Json -Compress
    Write-Output $response
    exit 0
  }
}

Write-Output '{ "permission": "allow" }'
exit 0
