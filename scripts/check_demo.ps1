# Rehearsal demo check: invented records, deterministic outputs, no model calls.
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$python = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }
$pyArgs = @()
if ($python -eq 'py') { $pyArgs += '-3' }
& $python @pyArgs scripts/check_demo.py @args
exit $LASTEXITCODE
