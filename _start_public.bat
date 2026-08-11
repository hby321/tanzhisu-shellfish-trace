@echo off
chcp 65001 >nul
title 滩智溯 - 公网演示服务器
echo ============================================================
echo   滩智溯 - 一键公网演示（ngrok 内网穿透）
echo ============================================================
echo.

REM 检查 ngrok 是否已安装
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未检测到 ngrok！
    echo.
    echo 请先安装 ngrok：
    echo   1. 访问 https://ngrok.com 注册账号（免费，无需信用卡）
    echo   2. 下载 Windows 版 ngrok
    echo   3. 解压后将 ngrok.exe 放到任意目录
    echo   4. 在该目录执行：ngrok config add-authtoken 你的token
    echo      （token 在 ngrok.com 注册后进入 Dashboard 获取）
    echo.
    echo 安装完成后重新运行本脚本。
    pause
    exit /b 1
)

REM 启动 Flask 后端
echo [1/2] 启动 Flask 后端...
start "滩智溯Flask" cmd /c "cd /d %~dp0 && .venv\Scripts\python.exe app.py"

REM 等待 Flask 启动
timeout /t 3 /nobreak >nul

REM 启动 ngrok 映射 5000 端口
echo [2/2] 启动 ngrok 公网映射...
echo.
echo ============================================================
echo   ngrok 启动后会显示公网地址，格式类似：
echo   https://xxxxx-xxxxx-xxxxx.ngrok-free.app
echo.
echo   演示时请分享此地址（手机微信直接访问）：
echo     平台主页：https://你的ngrok地址/
echo     小程序H5：https://你的ngrok地址/m/
echo     AI健康检查：https://你的ngrok地址/ai-server/health
echo ============================================================
echo.
echo 注意：ngrok 免费版每次重启 URL 会变化，比赛演示前请重启一次。
echo.

ngrok http 5000

pause
