$ErrorActionPreference = "Stop"

$ProjectRoot = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$PythonExe = "C:\Users\Aaishiki\AppData\Local\Programs\Python\Python312\python.exe"
$FrontendPort = 5173
$BackendPort = 8001

function Test-PortListening {
  param([int]$Port)
  return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-Http {
  param(
    [string]$Url,
    [int]$MaxSeconds = 30
  )
  $deadline = (Get-Date).AddSeconds($MaxSeconds)
  while ((Get-Date) -lt $deadline) {
    try {
      $res = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
      if ($res.StatusCode -ge 200 -and $res.StatusCode -lt 500) { return $true }
    } catch {}
    Start-Sleep -Milliseconds 500
  }
  return $false
}

Set-Location $ProjectRoot

if (-not (Test-Path (Join-Path $ProjectRoot "package.json"))) {
  throw "package.json not found in $ProjectRoot. Run this script from your SmartSpend project folder."
}

if (-not (Test-PortListening -Port $BackendPort)) {
  Start-Process -WindowStyle Hidden -FilePath $PythonExe -ArgumentList @(
    "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "$BackendPort"
  ) -WorkingDirectory $ProjectRoot | Out-Null
}

if (-not (Test-PortListening -Port $FrontendPort)) {
  # Start frontend via cmd so Next.js child process spawn works reliably on Windows.
  Start-Process -WindowStyle Hidden -FilePath "cmd.exe" -ArgumentList @(
    "/c", "cd /d $ProjectRoot && npm run dev -- --port $FrontendPort"
  ) -WorkingDirectory $ProjectRoot | Out-Null
}

$backendReady = Wait-Http -Url "http://127.0.0.1:$BackendPort/health" -MaxSeconds 40
$frontendReady = Wait-Http -Url "http://127.0.0.1:$FrontendPort" -MaxSeconds 60

Write-Host ""
Write-Host "SmartSpend local startup status:"
Write-Host "Backend : $backendReady  -> http://127.0.0.1:$BackendPort/health"
Write-Host "Frontend: $frontendReady -> http://127.0.0.1:$FrontendPort"
Write-Host ""
Write-Host "Open in browser: http://127.0.0.1:$FrontendPort"
