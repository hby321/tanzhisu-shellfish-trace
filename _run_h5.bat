@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title TZS-MiniH5 (port 10086)
echo Starting Mini Program H5...
npx taro build --type h5 --watch --port 10086
pause