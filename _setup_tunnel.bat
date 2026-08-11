@echo off
chcp 65001 >nul
title 滩智溯 - Cloudflare Tunnel 配置向导
echo 正在启动配置向导...
echo.
.venv\Scripts\python.exe setup_tunnel.py
echo.
pause
