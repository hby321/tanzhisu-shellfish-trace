# -*- coding: utf-8 -*-
"""
滩智溯 - Cloudflare Tunnel 固定URL 配置向导
============================================================
此脚本帮助用户一步步完成 Cloudflare 命名隧道的创建，
获取 trycloudflare.com 固定公网 URL。

使用方法：
  python setup_tunnel.py

前置条件：
  1. 已注册 Cloudflare 账号（https://dash.cloudflare.com）
  2. cloudflared 已下载（首次运行会自动下载）
============================================================
"""
import os
import sys
import json
import time
import subprocess
import re
import urllib.request
from pathlib import Path

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED_DIR = os.path.join(PROJECT_DIR, 'cloudflared')
CLOUDFLARED_EXE = os.path.join(CLOUDFLARED_DIR, 'cloudflared.exe')
CLOUDFLARED_LOG = os.path.join(PROJECT_DIR, 'cloudflared_setup.log')
CONFIG_FILE = os.path.join(PROJECT_DIR, 'cloudflared_config.yml')
STATE_FILE = os.path.join(PROJECT_DIR, 'tunnel_state.json')

CF_DOWNLOAD_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/"
    "download/cloudflared-windows-amd64.exe"
)


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(num, total, text):
    print(f"\n{'─'*40}")
    print(f"  步骤 {num}/{total}: {text}")
    print(f"{'─'*40}")


def download_cloudflared():
    os.makedirs(CLOUDFLARED_DIR, exist_ok=True)
    if os.path.exists(CLOUDFLARED_EXE):
        print(f"  ✓ cloudflared 已存在")
        return True
    print(f"  正在下载 cloudflared...")
    try:
        urllib.request.urlretrieve(CF_DOWNLOAD_URL, CLOUDFLARED_EXE)
        print(f"  ✓ 下载完成")
        return True
    except Exception as e:
        print(f"  ✗ 下载失败: {e}")
        return False


def run_cf_command(args, check_output=False, timeout=120):
    """运行 cloudflared 命令"""
    cmd = [CLOUDFLARED_EXE] + args
    print(f"  执行: {' '.join(cmd)}")
    
    try:
        if check_output:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        else:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return proc
    except subprocess.TimeoutExpired:
        return "", "Timeout", -1
    except Exception as e:
        return "", str(e), -1


def check_login_status():
    """检查是否已登录 Cloudflare"""
    home = os.path.expanduser("~")
    cf_dir = os.path.join(home, ".cloudflared")
    if os.path.exists(cf_dir):
        for f in os.listdir(cf_dir):
            if f.endswith(".pem"):
                return True
    return False


def check_existing_tunnel():
    """检查是否已有命名隧道"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return None


def login_cloudflare():
    """登录 Cloudflare（会打开浏览器）"""
    print("\n  即将打开浏览器进行 Cloudflare 授权...")
    print("  如果没有自动打开，请手动打开以下 URL：")
    
    # 运行 tunnel login，它会输出授权 URL
    proc = subprocess.Popen(
        [CLOUDFLARED_EXE, 'tunnel', 'login'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    
    # 读取输出获取授权 URL
    output_lines = []
    start_time = time.time()
    while time.time() < start_time + 30:
        try:
            line = proc.stdout.readline()
            if line:
                decoded = line.decode('utf-8', errors='ignore').strip()
                if decoded:
                    output_lines.append(decoded)
                    print(f"  {decoded}")
        except Exception:
            break
        time.sleep(0.1)
    
    # 等待用户完成授权
    print("\n  请在浏览器中完成授权，然后按回车键继续...")
    input()
    
    # 检查是否授权成功
    if check_login_status():
        print("  ✓ Cloudflare 登录成功")
        return True
    else:
        print("  ✗ 登录失败，请重试")
        return False


def create_tunnel(name='tanzhisu'):
    """创建命名隧道"""
    state = check_existing_tunnel()
    if state and state.get('tunnel_id'):
        print(f"  检测到已有隧道: {state.get('tunnel_name')}")
        return state
    
    print(f"\n  正在创建命名隧道 '{name}'...")
    stdout, stderr, rc = run_cf_command(['tunnel', 'create', name], check_output=True)
    
    # 解析输出获取隧道 ID
    tunnel_id = None
    credentials_file = None
    
    # 输出格式:
    # Created tunnel <name> with id <TUNNEL_ID>
    # +---------------------------------------------------------+
    # |  Your tunnel credentials are stored at:                 |
    # |  /path/to/credentials.json                              |
    # +---------------------------------------------------------+
    
    for line in stdout.split('\n') + stderr.split('\n'):
        match = re.search(r'id\s+([a-f0-9]+)', line)
        if match:
            tunnel_id = match.group(1)
        match = re.search(r'stored at:\s*(.+\.json)', line)
        if match:
            credentials_file = match.group(1).strip()
    
    if not tunnel_id:
        # 尝试另一种格式
        for line in stdout.split('\n'):
            match = re.search(r'([a-f0-9]{32,})', line)
            if match:
                tunnel_id = match.group(1)
                break
    
    if not tunnel_id:
        print(f"  输出: {stdout}")
        print(f"  错误: {stderr}")
        print("  ✗ 无法解析隧道 ID")
        return None
    
    # 如果没有找到 credentials_file，尝试查找
    if not credentials_file:
        home = os.path.expanduser("~")
        cf_dir = os.path.join(home, ".cloudflared")
        if os.path.exists(cf_dir):
            for f in os.listdir(cf_dir):
                if f.endswith('.json') and tunnel_id in f:
                    credentials_file = os.path.join(cf_dir, f)
                    break
            # 如果没找到特定的，找最新的
            if not credentials_file:
                json_files = [(os.path.join(cf_dir, f), os.path.getmtime(os.path.join(cf_dir, f))) 
                             for f in os.listdir(cf_dir) if f.endswith('.json')]
                if json_files:
                    credentials_file = max(json_files, key=lambda x: x[1])[0]
    
    state = {
        'tunnel_name': name,
        'tunnel_id': tunnel_id,
        'credentials_file': credentials_file,
        'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"  ✓ 隧道创建成功")
    print(f"    隧道 ID: {tunnel_id}")
    print(f"    凭证文件: {credentials_file}")
    return state


def setup_dns_routing(state):
    """配置 DNS 路由获取固定 URL"""
    if not state:
        return None
    
    # 检查是否已有固定 URL
    state_data = check_existing_tunnel()
    if state_data and state_data.get('fixed_url'):
        print(f"  已有固定 URL: {state_data['fixed_url']}")
        return state_data['fixed_url']
    
    tunnel_name = state['tunnel_name']
    print(f"\n  正在配置 DNS 路由...")
    print(f"  即将打开浏览器，请在 Cloudflare Dashboard 中配置：")
    print(f"    Zero Trust > Tunnels > {tunnel_name} > Public Hostname")
    print(f"    设置子域名（如 tanzhisu），选择 trycloudflare.com")
    print()
    
    # 尝试用命令行配置路由
    # cloudflared tunnel route dns <name> <hostname>
    hostname = input("  请输入你想要的固定域名前缀（如 tanzhisu，将生成 xxx.trycloudflare.com）: ").strip()
    if not hostname:
        hostname = 'tanzhisu'
    
    full_domain = f"{hostname}.trycloudflare.com"
    
    stdout, stderr, rc = run_cf_command(
        ['tunnel', 'route', 'dns', tunnel_name, full_domain],
        check_output=True, timeout=30
    )
    
    print(f"  输出: {stdout}")
    if stderr:
        print(f"  提示: {stderr}")
    
    # 如果命令行方式不行，提示用户手动配置
    print(f"\n  如果命令行配置成功，固定 URL 为: https://{full_domain}")
    print(f"  如果失败，请在 Cloudflare Dashboard 手动配置：")
    print(f"    1. 打开 https://dash.cloudflare.com")
    print(f"    2. 进入 Zero Trust > Tunnels > {tunnel_name}")
    print(f"    3. 点击 Public Hostname > 添加")
    print(f"       Hostname: {full_domain}")
    print(f"       Service: http://localhost:5000")
    
    # 更新状态
    state['fixed_url'] = f"https://{full_domain}"
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    return state['fixed_url']


def create_config(state):
    """创建 cloudflared 配置文件"""
    if not state:
        return None
    
    if os.path.exists(CONFIG_FILE):
        print(f"  ✓ 配置文件已存在: {CONFIG_FILE}")
        return CONFIG_FILE
    
    credentials_file = state.get('credentials_file', '')
    tunnel_id = state.get('tunnel_id', '')
    
    config = f"""# 滩智溯 Cloudflare Tunnel 配置
tunnel: {tunnel_id}
credentials-file: {credentials_file}

ingress:
  - hostname: {state.get('fixed_url', '').replace('https://', '').replace('/', '')}
    service: http://localhost:5000
  - service: http_status:404
"""
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(config)
    
    print(f"  ✓ 配置文件已创建: {CONFIG_FILE}")
    return CONFIG_FILE


def main():
    os.chdir(PROJECT_DIR)
    
    print_header("滩智溯 - Cloudflare Tunnel 固定URL 配置向导")
    
    print("""
  本向导将帮助你：
    1. 下载 cloudflared（如未安装）
    2. 登录 Cloudflare 账号
    3. 创建命名隧道
    4. 获取 trycloudflare.com 固定 URL
    5. 生成配置文件

  前置条件：已注册 Cloudflare 账号（https://dash.cloudflare.com）
    """)
    
    # 步骤 1：下载 cloudflared
    print_step(1, 5, "准备 cloudflared")
    if not download_cloudflared():
        return
    
    # 步骤 2：登录 Cloudflare
    print_step(2, 5, "登录 Cloudflare")
    if check_login_status():
        print("  ✓ 已登录")
    else:
        if not login_cloudflare():
            return
    
    # 步骤 3：创建命名隧道
    print_step(3, 5, "创建命名隧道")
    state = create_tunnel('tanzhisu')
    if not state:
        return
    
    # 步骤 4：配置 DNS 路由
    print_step(4, 5, "配置 DNS 路由（获取固定 URL）")
    fixed_url = setup_dns_routing(state)
    
    # 步骤 5：生成配置文件
    print_step(5, 5, "生成配置文件")
    create_config(state)
    
    print_header("配置完成！")
    
    if fixed_url:
        print(f"""
  固定公网地址：{fixed_url}

  启动固定 URL 演示：
    python start_public.py --fixed
    或双击 _start_fixed_public.bat

  演示链接：
    平台主页：{fixed_url}/
    小程序H5：{fixed_url}/m/
        """)
    else:
        print(f"\n  固定 URL 配置可能未完成，请检查上方提示。")
    
    # 保存状态供 start_public.py 使用
    state_data = check_existing_tunnel()
    if state_data:
        print(f"\n  隧道状态已保存，下次启动会自动读取。")


if __name__ == '__main__':
    main()
