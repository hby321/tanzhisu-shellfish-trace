# -*- coding: utf-8 -*-
"""
一键启动脚本 - Python版
双击 start.bat 会自动运行此文件（start.bat 优先，此文件为备用）
自动检测 Python/Node，适配任意设备
"""
import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
os.chdir(ROOT)

print("=" * 50)
print("  滩智溯 TanZhiSu - 一键启动")
print("  数据智能体综合应用平台 V1.0 (软著) 已集成")
print("=" * 50)
print()

# Step 1: Find Python (auto-detect, works on any device)
python_exe = sys.executable
print(f"[OK] Python: {python_exe}")
try:
    ver = subprocess.run([python_exe, "--version"], capture_output=True, text=True, timeout=5)
    print(f"     {ver.stdout.strip()}")
except Exception:
    pass

# Step 2: Check Python dependencies
print("[INFO] Checking Python dependencies...")
core_deps = ["flask", "flask_sqlalchemy", "flask_login", "flask_cors", "requests"]
missing = []
for dep in core_deps:
    try:
        __import__(dep)
    except ImportError:
        missing.append(dep)
if missing:
    print(f"[INFO] Installing missing: {', '.join(missing)}")
    subprocess.run([python_exe, "-m", "pip", "install", "-r", "requirements.txt", "-q"], timeout=120)
else:
    print("[OK] Core dependencies ready")

# Step 3: Check Node.js
has_node = False
try:
    result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"[OK] Node.js: {result.stdout.strip()}")
        has_node = True
    else:
        print("[WARN] Node.js not found - mini program H5 will not start")
except Exception:
    print("[WARN] Node.js not found - mini program H5 will not start")

# Step 4: Check mini program dependencies
if has_node and not (ROOT / "src" / "node_modules").exists():
    print("[INFO] Installing mini program dependencies (first time only)...")
    subprocess.run(["npm", "install"], cwd=str(ROOT / "src"), timeout=120)

# Step 5: Start Flask backend on port 5000
print("[INFO] Starting Flask backend on port 5000...")
flask_proc = subprocess.Popen(
    [python_exe, "app.py"],
    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    cwd=str(ROOT)
)

# Step 6: Start 《数据智能体综合应用平台 V1.0》软著 AI 调度服务 on port 8090
print("[INFO] Starting 数据智能体综合应用平台 V1.0 (软著 AI) on port 8090...")
agent_proc = subprocess.Popen(
    [python_exe, "agent_server.py"],
    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    cwd=str(ROOT)
)

# Step 7: Start mini program H5 on port 10086
mini_proc = None
if has_node:
    print("[INFO] Starting mini program H5 on port 10086...")
    mini_proc = subprocess.Popen(
        ["npx", "taro", "build", "--type", "h5", "--watch", "--port", "10086"],
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        cwd=str(ROOT / "src")
    )

# Step 8: Auto open browser
print("[INFO] Waiting for services to start...")
time.sleep(5)
webbrowser.open("http://127.0.0.1:5000")

if has_node:
    print("[INFO] Waiting for mini program compilation...")
    time.sleep(15)
    webbrowser.open("http://127.0.0.1:10086")

print()
print("=" * 50)
print("  服务已启动！Services started!")
print()
print("  Flask 主后端:    http://127.0.0.1:5000")
print("  AI 智能体平台:   http://127.0.0.1:8090  (软著 V1.0)")
if has_node:
    print("  小程序 H5:      http://127.0.0.1:10086")
print()
print("  账号 (密码: 123456):")
print("    农户:   farmer001")
print("    合作社: coop001")
print("    企业:   ent001")
print("    监管:   reg001")
print("=" * 50)
print()
print("  关闭对应命令行窗口即可停止服务")
print()
try:
    input("按 Enter 退出 (服务将继续运行)...")
except Exception:
    pass
