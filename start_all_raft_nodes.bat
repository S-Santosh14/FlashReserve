@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run setup.bat first.
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$root=(Get-Location).Path; $envFile=Join-Path $root '.env';" ^
  "if (-not (Test-Path $envFile)) { throw '.env is required.' };" ^
  "$cfg=@{}; Get-Content $envFile | ForEach-Object { if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') { $cfg[$Matches[1]]=$Matches[2].Trim() } };" ^
  "if ($cfg['RAFT_CLUSTER_SIZE'] -ne '7') { throw 'RAFT_CLUSTER_SIZE must be 7 for this script.' }; $missing=@(); $ports=@(); $local=[System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() | ForEach-Object { $_.GetIPProperties().UnicastAddresses | ForEach-Object { $_.Address.ToString() } };" ^
  "foreach ($n in 1..7) { foreach ($suffix in @('HOST','PORT','MONGO_URI')) { $key='RAFT_NODE_{0}_{1}' -f $n,$suffix; if (-not $cfg[$key] -or $cfg[$key] -match 'replace-with') { $missing += $key } }; if ($cfg[('RAFT_NODE_{0}_HOST' -f $n)]) { $addresses=[System.Net.Dns]::GetHostAddresses($cfg[('RAFT_NODE_{0}_HOST' -f $n)]) | ForEach-Object { $_.ToString() }; if ($addresses | Where-Object { $_ -notin $local -and $_ -notin @('127.0.0.1','::1') }) { throw 'All seven nodes are not configured on this host. Run start_raft_node.bat on each node host instead.' } }; if ($cfg[('RAFT_NODE_{0}_PORT' -f $n)]) { $ports += [int]$cfg[('RAFT_NODE_{0}_PORT' -f $n)] } };" ^
  "if ($missing.Count) { throw ('Missing or placeholder settings: ' + ($missing -join ', ')) }; if (($ports | Select-Object -Unique).Count -ne 7) { throw 'Raft RPC ports must be unique.' }; foreach ($port in $ports) { $listener=[System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any,$port); try { $listener.Start() } catch { throw ('Raft RPC port ' + $port + ' is already in use.') } finally { $listener.Stop() } };" ^
  "$rootKey=$root -replace '[^A-Za-z0-9]','_'; $pidDir=Join-Path $env:TEMP ('FlashReserve-Raft-' + $rootKey); New-Item -ItemType Directory -Force $pidDir | Out-Null; $pidFile=Join-Path $pidDir 'nodes.txt'; if (Test-Path $pidFile) { throw 'A local Raft start record already exists. Run stop_raft_nodes.bat first.' };" ^
  "$python=Join-Path $root '.venv\Scripts\python.exe'; $ids=@(); foreach ($n in 1..7) { $id='node-{0}' -f $n; $p=Start-Process -FilePath $python -ArgumentList @('-m','backend.raft.node_runner','--node',$id) -WorkingDirectory $root -PassThru; $ids += ('{0} {1}' -f $p.Id,$id) }; Set-Content -Path $pidFile -Value $ids; Write-Output 'Started seven local Raft node processes.'"
if errorlevel 1 exit /b 1
