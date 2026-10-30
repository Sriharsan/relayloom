# Start the Relayloom rehearsal workroom on loopback and open it in a browser.
# Rehearsal mode: invented records, deterministic outputs, no model calls.
# Usage: .\demo.ps1 [-Port 8800] [-NoBrowser]   Stop with Ctrl+C.
param([int]$Port = 8800, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }
$arguments = @()
if ($python -eq 'py') { $arguments += '-3' }
$arguments += @('-m', 'relayloom', '--port', "$Port")
$server = Start-Process -FilePath $python -ArgumentList $arguments -NoNewWindow -PassThru
$url = "http://127.0.0.1:$Port"
try {
  $ready = $false
  for ($i = 0; $i -lt 50 -and -not $ready; $i++) {
    try { Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1 | Out-Null; $ready = $true }
    catch { Start-Sleep -Milliseconds 200 }
  }
  if (-not $ready) { throw "The workroom did not start on $url" }
  if (-not $NoBrowser) { Start-Process $url }
  Write-Host "Relayloom rehearsal is running at $url. Press Ctrl+C to stop."
  Wait-Process -Id $server.Id
} finally {
  # Stop the launcher and its Python child together.
  if (-not $server.HasExited) { & taskkill.exe /PID $server.Id /T /F | Out-Null }
}
