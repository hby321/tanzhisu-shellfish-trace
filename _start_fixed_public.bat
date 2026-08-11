@echo off
chcp 65001 >nul
title 滩智溯 - Cloudflare Tunnel（固定URL）
echo 正在启动滩智溯固定公网演示...
echo.
.venv\Scripts\python.exe start_public.py --fixed
echo.
echo 服务已停止
pause
