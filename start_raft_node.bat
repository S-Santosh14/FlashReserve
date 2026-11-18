@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
    echo Usage: start_raft_node.bat node-1
    exit /b 2
)
if not exist ".venv\Scripts\python.exe" (
    echo Run setup.bat first.
    exit /b 1
)
".venv\Scripts\python.exe" -m backend.raft.node_runner --node "%~1"
