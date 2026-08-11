@echo off
chcp 65001 >nul
title 滩智溯 - Cloudflare Tunnel 固定公网
echo ============================================================
echo   滩智溯 - Cloudflare Tunnel 固定公网演示
echo ============================================================
echo.

REM 检查 cloudflared 是否已安装
where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未检测到 cloudflared！
    echo.
    echo 安装步骤：
    echo   1. 访问 https://dash.cloudflare.com 注册账号（免费，无需信用卡）
    echo   2. 进入 Zero Trust ^> Access ^> Tunnels
    echo   3. 创建 Tunnel ^> 选择 "Cloudflared"
    echo   4. 下载 Windows 版 cloudflared
    echo   5. 执行以下命令登录并创建隧道：
    echo      cloudflared tunnel login
    echo      cloudflared tunnel create tanzhisu
    echo      cloudflared tunnel route dns tanzhisu 你的域名
    echo.
    echo   详细步骤见 DEPLOY.md 中 Cloudflare Tunnel 章节
    echo.
    pause
    exit /b 1
)

REM 启动 Flask 后端
echo [1/2] 启动 Flask 后端...
start "滩智溯Flask" cmd /c "cd /d %~dp0 && .venv\Scripts\python.exe app.py"

REM 等待 Flask 启动
timeout /t 3 /nobreak >nul

REM 启动 Cloudflare Tunnel
echo [2/2] 启动 Cloudflare Tunnel...
echo.
echo ============================================================
echo   固定公网地址：
echo     平台主页：https://你的域名/
echo     小程序H5：https://你的域名/m/
echo   （域名在 Tunnel 创建时配置，不会变化）
echo ============================================================
echo.

cloudflared tunnel run tanzhisu

pause
