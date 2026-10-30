# Live Meta acceptance check. Refuses unless --i-have-credit is passed.
# Sends ONE billable request when allowed. Never prints the API key.
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$python = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }
$pyArgs = @()
if ($python -eq 'py') { $pyArgs += '-3' }
& $python @pyArgs scripts/check_meta.py @args
exit $LASTEXITCODE
