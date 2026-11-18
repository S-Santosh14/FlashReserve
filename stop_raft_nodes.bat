@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $root=(Get-Location).Path; $rootKey=$root -replace '[^A-Za-z0-9]','_'; $pidDir=Join-Path $env:TEMP ('FlashReserve-Raft-' + $rootKey); $pidFile=Join-Path $pidDir 'nodes.txt';" ^
  "if (-not (Test-Path $pidFile)) { Write-Output 'No local start_all_raft_nodes.bat process record was found.'; exit 0 };" ^
  "$python=(Join-Path $root '.venv\Scripts\python.exe'); foreach ($line in Get-Content $pidFile) { $parts=$line -split ' ',2; $process=Get-CimInstance Win32_Process -Filter ('ProcessId = ' + $parts[0]) -ErrorAction SilentlyContinue; if ($process -and $process.ExecutablePath -eq $python -and $process.CommandLine -like ('*backend.raft.node_runner --node ' + $parts[1] + '*')) { Stop-Process -Id ([int]$parts[0]) } }; Remove-Item -LiteralPath $pidFile -Force; Write-Output 'Stopped recorded local Raft node processes.'"
