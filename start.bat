@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

title TanZhiSu Launcher

echo ========================================================
echo   TanZhiSu - One Click Start
echo   AI Agent Platform V1.0 Integrated
echo ========================================================
echo.

REM ---- Find Python ----
if exist ".venv\Scripts\python.exe" (
    echo [OK] Python venv found
    goto :py_ok
)
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] System Python found
    goto :py_ok
)
echo [ERROR] Python not found! Install Python 3.8+
pause
exit /b 1

:py_ok
echo.

REM ---- Check deps ----
echo [INFO] Checking Python deps...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import flask, flask_sqlalchemy, flask_login, flask_cors, requests" 2>nul
) else (
    python -c "import flask, flask_sqlalchemy, flask_login, flask_cors, requests" 2>nul
)
if %ERRORLEVEL% neq 0 (
    echo [INFO] Installing deps...
    if exist ".venv\Scripts\python.exe" (
        ".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
    ) else (
        python -m pip install -r requirements.txt -q
    )
) else (
    echo [OK] Deps ready
)
echo.

REM ---- Check Node.js ----
where node >nul 2>&1
if %ERRORLEVEL% neq 0 goto :no_node

echo [OK] Node.js:
node --version
echo.

REM ---- Install mini program deps ----
if not exist "node_modules\@tarojs\taro" (
    echo [INFO] Installing mini program deps...
    call npm install
) else (
    echo [OK] Mini program deps ready
)
echo.

REM ---- Clean ports ----
echo [INFO] Cleaning ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000.*LISTENING" 2^>nul') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8090.*LISTENING" 2^>nul') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":10086.*LISTENING" 2^>nul') do taskkill /F /PID %%a >nul 2>&1
echo [OK] Ports cleaned
echo.

REM ---- Start services ----
echo [INFO] Starting Flask backend (port 5000)...
start "TZS-Backend-5000" "%~dp0_run_flask.bat"

echo [INFO] Starting AI Agent (port 8090)...
start "TZS-AI-8090" "%~dp0_run_ai.bat"

echo [INFO] Starting Mini Program H5 (port 10086)...
start "TZS-H5-10086" "%~dp0_run_h5.bat"

REM ---- Open browser ----
echo.
echo [INFO] Waiting for services... (8s)
timeout /t 8 /nobreak >nul

echo [INFO] Opening platform...
start "" "http://127.0.0.1:5000"

echo [INFO] Waiting for H5 compile... (20s)
timeout /t 20 /nobreak >nul
echo [INFO] Opening mini program H5...
start "" "http://127.0.0.1:10086"

echo.
echo ========================================================
echo   All services started!
echo.
echo   Backend:     http://127.0.0.1:5000
echo   AI Agent:    http://127.0.0.1:8090
echo   Mini H5:     http://127.0.0.1:10086
echo.
echo   Accounts (pwd: 123456):
echo     farmer001 / coop001 / ent001 / reg001
echo.
echo   Close window to stop service
echo ========================================================
echo.
pause
goto :eof

:no_node
echo [WARN] Node.js not found, skip mini program
echo.

REM ---- Clean ports ----
echo [INFO] Cleaning ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000.*LISTENING" 2^>nul') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8090.*LISTENING" 2^>nul') do taskkill /F /PID %%a >nul 2>&1
echo [OK] Ports cleaned
echo.

REM ---- Start services ----
echo [INFO] Starting Flask backend (port 5000)...
start "TZS-Backend-5000" "%~dp0_run_flask.bat"

echo [INFO] Starting AI Agent (port 8090)...
start "TZS-AI-8090" "%~dp0_run_ai.bat"

REM ---- Open browser ----
echo.
echo [INFO] Waiting for services... (8s)
timeout /t 8 /nobreak >nul

echo [INFO] Opening platform...
start "" "http://127.0.0.1:5000"

echo.
echo ========================================================
echo   Services started! (No Node.js, mini program skipped)
echo.
echo   Backend:     http://127.0.0.1:5000
echo   AI Agent:    http://127.0.0.1:8090
echo.
echo   Accounts (pwd: 123456):
echo     farmer001 / coop001 / ent001 / reg001
echo ========================================================
echo.
pause