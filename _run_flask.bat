@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title TZS-Backend (port 5000)
echo Starting Flask backend...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
) else (
    python app.py
)
pause