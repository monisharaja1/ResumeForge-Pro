$ErrorActionPreference = "Stop"

$frontendRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $frontendRoot
$pythonFromVenv = Join-Path $repoRoot ".venv\Scripts\python.exe"
$pythonExe = if (Test-Path $pythonFromVenv) { $pythonFromVenv } else { "python" }

$backendWasStarted = $false
$backendProcess = $null

function Test-BackendPortListening {
  return [bool](netstat -ano | Select-String "^\s*TCP\s+\S+:5000\s+\S+\s+LISTENING\s+\d+\s*$")
}

if (-not (Test-BackendPortListening)) {
  Write-Host "Starting backend on http://127.0.0.1:5000 ..."
  $backendProcess = Start-Process -FilePath $pythonExe -ArgumentList "app.py" -WorkingDirectory $repoRoot -PassThru -WindowStyle Hidden
  $backendWasStarted = $true

  $ready = $false
  for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 300
    if (Test-BackendPortListening) {
      $ready = $true
      break
    }
    if ($backendProcess.HasExited) {
      break
    }
  }

  if (-not $ready) {
    if ($backendProcess -and -not $backendProcess.HasExited) {
      Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
    }
    throw "Backend failed to start on port 5000. Run python app.py in the repo root to inspect backend errors."
  }
} else {
  Write-Host "Backend already running on port 5000."
}

try {
  & npm.cmd run dev:vite
} finally {
  if ($backendWasStarted -and $backendProcess -and -not $backendProcess.HasExited) {
    Write-Host "Stopping backend process..."
    Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
  }
}
