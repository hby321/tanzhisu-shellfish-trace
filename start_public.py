# -*- coding: utf-8 -*-
"""
滩智溯 - Cloudflare Tunnel 一键启动器
============================================================
功能：
  1. 自动检测/下载 cloudflared
  2. 启动 Flask 后端（端口 5000）
  3. 启动 Cloudflare Tunnel 映射公网
  4. 从日志中提取公网 URL 并显示

两种模式：
  - 临时模式：trycloudflare.com 域名，URL 每次重启会变
  - 固定模式：命名隧道 + 自定义域名，URL 永久不变

Windows 下 bat 脚本处理 cloudflared 输出不稳定，
本脚本用 Python + 日志文件解析，确保 URL 提取可靠。
============================================================
"""
import os
import sys
import time
import subprocess
import re
import urllib.request
import json
from pathlib import Path

# ============================================================
# 配置
# ============================================================
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(PROJECT_DIR, '.venv', 'Scripts', 'python.exe')
CLOUDFLARED_DIR = os.path.join(PROJECT_DIR, 'cloudflared')
CLOUDFLARED_EXE = os.path.join(CLOUDFLARED_DIR, 'cloudflared.exe')
CLOUDFLARED_LOG = os.path.join(PROJECT_DIR, 'cloudflared.log')
CLOUDFLARED_URL_FILE = os.path.join(PROJECT_DIR, 'public_url.txt')
STATE_FILE = os.path.join(PROJECT_DIR, 'tunnel_state.json')
FLASK_PORT = 5000

# cloudflared 下载地址（Windows AMD64）
CF_DOWNLOAD_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/"
    "download/cloudflared-windows-amd64.exe"
)

# ============================================================
# 工具函数
# ============================================================
def print_banner(text):
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(num, total, text):
    print(f"\n[{num}/{total}] {text}")


def download_cloudflared():
    """下载 cloudflared"""
    os.makedirs(CLOUDFLARED_DIR, exist_ok=True)
    if os.path.exists(CLOUDFLARED_EXE):
        print(f"  cloudflared 已存在: {CLOUDFLARED_EXE}")
        return True
    
    print(f"  正在下载 cloudflared...")
    print(f"  下载地址: {CF_DOWNLOAD_URL}")
    try:
        urllib.request.urlretrieve(CF_DOWNLOAD_URL, CLOUDFLARED_EXE)
        print(f"  下载完成: {CLOUDFLARED_EXE}")
        return True
    except Exception as e:
        print(f"  [ERROR] 下载失败: {e}")
        print(f"  请手动下载: {CF_DOWNLOAD_URL}")
        print(f"  保存到: {CLOUDFLARED_EXE}")
        return False


def check_flask():
    """检查 Flask 是否正在运行"""
    try:
        import urllib.request
        req = urllib.request.Request(f"http://127.0.0.1:{FLASK_PORT}/")
        urllib.request.urlopen(req, timeout=2)
        return True
    except Exception:
        return False


def start_flask():
    """启动 Flask 后端"""
    if check_flask():
        print(f"  Flask 已在运行 (端口 {FLASK_PORT})")
        return True
    
    print(f"  启动 Flask 后端 (端口 {FLASK_PORT})...")
    env = os.environ.copy()
    env['DEPLOY_MODE'] = 'cloudflared'
    env['AI_API_KEY'] = os.environ.get('AI_API_KEY', 'sk-cf236fba5bed47d392bd842a027f3864')
    env['AI_BASE_URL'] = os.environ.get('AI_BASE_URL', 'https://api.deepseek.com/v1')
    env['AI_MODEL'] = os.environ.get('AI_MODEL', 'deepseek-chat')
    env['AGENT_SERVER_URL'] = os.environ.get('AGENT_SERVER_URL', f'http://127.0.0.1:{FLASK_PORT}/ai-server')
    
    if os.path.exists(VENV_PYTHON):
        python = VENV_PYTHON
    else:
        python = sys.executable
    
    proc = subprocess.Popen(
        [python, 'app.py'],
        cwd=PROJECT_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    
    # 等待 Flask 启动
    for i in range(15):
        time.sleep(1)
        if check_flask():
            print(f"  Flask 启动成功！")
            return True
        print(f"  等待 Flask 启动... ({i+1}/15)")
    
    print(f"  [WARN] Flask 启动超时，但继续尝试")
    return True


def extract_url_from_log():
    """从 cloudflared 日志中提取公网 URL"""
    if not os.path.exists(CLOUDFLARED_LOG):
        return None
    
    try:
        with open(CLOUDFLARED_LOG, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 搜索 trycloudflare.com URL
        for line in reversed(lines):
            match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', line)
            if match:
                return match.group(0)
    except Exception:
        pass
    return None


def run_temporary_tunnel():
    """临时隧道模式：trycloudflare.com（URL 每次重启会变）"""
    print_step(3, 3, "启动 Cloudflare 临时隧道...")
    
    # 清空旧日志
    if os.path.exists(CLOUDFLARED_LOG):
        os.remove(CLOUDFLARED_LOG)
    
    # 启动 cloudflared
    proc = subprocess.Popen(
        [CLOUDFLARED_EXE, 'tunnel', '--url', f'http://127.0.0.1:{FLASK_PORT}',
         '--logfile', CLOUDFLARED_LOG, '--no-autoupdate'],
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    
    print(f"  cloudflared 进程 PID: {proc.pid}")
    
    # 等待 URL 出现
    print("  等待公网 URL...")
    public_url = None
    for i in range(30):
        time.sleep(1)
        public_url = extract_url_from_log()
        if public_url:
            break
        if i % 5 == 0 and i > 0:
            print(f"  等待中... ({i+1}/30)")
    
    if public_url:
        # 保存 URL
        with open(CLOUDFLARED_URL_FILE, 'w') as f:
            f.write(public_url)
        
        print(f"\n{'='*60}")
        print(f"  公网访问地址：")
        print(f"  {public_url}")
        print(f"{'='*60}")
        print(f"\n  演示链接：")
        print(f"    平台主页：{public_url}/")
        print(f"    小程序H5：{public_url}/m/")
        print(f"    AI健康检查：{public_url}/ai-server/health")
        print(f"\n  提示：此 URL 为临时地址，重启后会变化")
        print(f"  如需固定 URL，请使用命名隧道模式（见 --fixed 参数）")
    else:
        # 显示日志帮助排查
        print("\n  [WARN] 未能自动提取 URL，查看日志：")
        if os.path.exists(CLOUDFLARED_LOG):
            with open(CLOUDFLARED_LOG, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()[-2000:]
                print(content)
        else:
            print("  (日志文件不存在)")
    
    return proc


def run_named_tunnel():
    """命名隧道模式：固定 URL"""
    config_path = os.path.join(PROJECT_DIR, 'cloudflared_config.yml')
    state_file = os.path.join(PROJECT_DIR, 'tunnel_state.json')
    
    # 检查配置
    state = None
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
        except Exception:
            pass
    
    if not os.path.exists(config_path) or not state:
        print_banner("Cloudflare 固定URL 未配置")
        print("""
  请先运行配置向导：

    python setup_tunnel.py
    或双击 _setup_tunnel.bat

  配置向导会自动：
    1. 登录 Cloudflare
    2. 创建命名隧道
    3. 获取 trycloudflare.com 固定 URL
    4. 生成配置文件
        """)
        return None
    
    print_step(3, 3, "启动 Cloudflare 命名隧道（固定 URL）...")
    
    if os.path.exists(CLOUDFLARED_LOG):
        os.remove(CLOUDFLARED_LOG)
    
    proc = subprocess.Popen(
        [CLOUDFLARED_EXE, 'tunnel', 'run', '--config', config_path],
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    
    print(f"  cloudflared 进程 PID: {proc.pid}")
    
    # 读取固定 URL
    fixed_url = state.get('fixed_url', '')
    
    print(f"\n{'='*60}")
    print(f"  固定公网地址：{fixed_url}")
    print(f"{'='*60}")
    print(f"\n  演示链接：")
    print(f"    平台主页：{fixed_url}/")
    print(f"    小程序H5：{fixed_url}/m/")
    
    return proc


def main():
    import argparse
    parser = argparse.ArgumentParser(description='滩智溯 - Cloudflare Tunnel 启动器')
    parser.add_argument('--fixed', action='store_true', help='使用命名隧道（固定 URL，需预先配置）')
    parser.add_argument('--download-only', action='store_true', help='仅下载 cloudflared')
    args = parser.parse_args()
    
    os.chdir(PROJECT_DIR)
    
    print_banner("滩智溯 - Cloudflare Tunnel 公网部署")
    
    # 步骤 1：确保 cloudflared 存在
    print_step(1, 3, "检查 cloudflared...")
    if not download_cloudflared():
        print("\n  下载失败，请手动下载后重新运行")
        input("\n按回车键退出...")
        return
    
    if args.download_only:
        print("\n  cloudflared 下载完成！")
        return
    
    # 步骤 2：启动 Flask
    print_step(2, 3, "启动 Flask 后端...")
    if not start_flask():
        print("\n  Flask 启动失败，请检查 app.py 日志")
        input("\n按回车键退出...")
        return
    
    # 步骤 3：启动 Tunnel
    if args.fixed:
        cf_proc = run_named_tunnel()
    else:
        cf_proc = run_temporary_tunnel()
    
    if cf_proc is None:
        input("\n按回车键退出...")
        return
    
    # 保持运行
    print(f"\n  Tunnel 运行中，按 Ctrl+C 停止...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  正在停止...")
        cf_proc.terminate()
        print("  已停止")


if __name__ == '__main__':
    main()
