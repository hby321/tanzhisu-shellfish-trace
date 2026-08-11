@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title TZS-AI-Agent (port 8090)
echo Starting AI Agent...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" agent_server.py
) else (
    python agent_server.py
)
pause