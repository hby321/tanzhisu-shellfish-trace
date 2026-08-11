#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# ============================================================
# Render.com 构建脚本
# ------------------------------------------------------------
# 执行内容：
#   1. 安装 Python 依赖
#   2. 安装 Node.js 依赖（小程序 H5）
#   3. 构建小程序 H5 版本到 dist/h5
# ============================================================
set -e

echo "========== [1/3] 安装 Python 依赖 =========="
pip install --upgrade pip
pip install -r requirements.txt

echo "========== [2/3] 安装小程序 H5 依赖 =========="
# 检测 Node.js 是否可用
if command -v node >/dev/null 2>&1; then
    echo "Node.js 版本: $(node --version)"
    npm install --legacy-peer-deps
    echo "========== [3/3] 构建小程序 H5 =========="
    npm run build:h5
    echo "H5 构建完成，输出目录: dist/h5"
else
    echo "[WARN] 未检测到 Node.js，跳过小程序 H5 构建"
    echo "       小程序入口 /m/ 将不可用，其他功能不受影响"
fi

echo "========== 构建完成 =========="
