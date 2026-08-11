# 滩智溯平台部署指南

## 方案总览

| 方案 | 固定URL | 需要信用卡 | 难度 | 适用场景 |
|------|---------|-----------|------|---------|
| **ngrok 内网穿透** | ❌ 每次重启变 | ❌ 不需要 | ⭐ 最简单 | 快速演示 |
| **Cloudflare Tunnel** | ✅ 固定 | ❌ 不需要 | ⭐⭐ 中等 | 长期固定URL |
| Render.com | ✅ 固定 | ✅ 需要 | ⭐⭐ 中等 | 云端部署 |
| PythonAnywhere | ✅ 固定 | ⚠️ 可能需要 | ⭐⭐ 中等 | Python 托管 |

---

## 方案一：ngrok 内网穿透（最简单，推荐）

### 特点
- 零配置，5 分钟搞定
- 不需要信用卡
- URL 每次重启会变（比赛前重启一次即可）
- 本地电脑需要保持运行

### 步骤

#### 1. 安装 ngrok
1. 访问 https://ngrok.com 注册账号（**免费，无需信用卡**）
2. 下载 Windows 版：https://ngrok.com/download
3. 解压到任意目录（如 `C:\ngrok\`）

#### 2. 配置 ngrok
1. 登录 ngrok.com，进入 Dashboard 获取你的 **Authtoken**
2. 打开命令提示符（cmd 或 PowerShell），执行：
```
cd C:\ngrok
ngrok config add-authtoken 你的token
```

#### 3. 启动演示
直接双击运行项目根目录的 **`_start_public.bat`**

启动成功后会显示公网地址，例如：
```
https://a1b2c3d4e5f6.ngrok-free.app
```

分享给评委时使用：
- 平台主页：`https://你的地址/`
- 小程序 H5：`https://你的地址/m/`
- AI 健康检查：`https://你的地址/ai-server/health`

#### 4. 注意事项
- ngrok 免费版有 8 小时会话限制，到期需重启
- 比赛演示前建议提前 1 分钟启动
- 电脑不能关机/休眠

---

## 方案二：Cloudflare Tunnel（固定 URL，无需信用卡）

### 特点
- 固定 URL（永不变化）
- 不需要信用卡
- 免费 HTTPS
- 本地电脑需要保持运行

### 步骤

#### 1. 注册 Cloudflare
1. 访问 https://dash.cloudflare.com 注册账号（**免费，无需信用卡**）
2. 登录后进入 **Zero Trust** 面板

#### 2. 安装 cloudflared
1. 下载 Windows 版：https://github.com/cloudflare/cloudflared/releases
2. 下载 `cloudflared-windows-amd64.exe`，重命名为 `cloudflared.exe`
3. 放到任意目录（如 `C:\cloudflared\`）

#### 3. 创建隧道
```bash
# 1. 登录 Cloudflare
cloudflared tunnel login

# 2. 创建隧道（名称自定义）
cloudflared tunnel create tanzhisu

# 3. 配置 DNS 域名
# 在 Cloudflare Dashboard > Zero Trust > Tunnels > tanzhisu > Public Hostname
# 设置子域名（如 tanzhisu），选择你的域名
# 或使用 cloudflared 提供的 trycloudflare.com 临时域名

# 4. 配置 Tunnel 指向本地 5000 端口
# 创建配置文件 C:\cloudflared\config.yml
```

配置文件 `config.yml` 内容：
```yaml
tunnel: tanzhisu
credentials-file: C:\Users\你的用户名\.cloudflared\<隧道ID>.json

ingress:
  - hostname: tanzhisu.trycloudflare.com
    service: http://localhost:5000
  - service: http_status:404
```

#### 4. 启动演示
双击运行项目根目录的 **`_start_fixed_public.bat`**

固定公网地址：`https://tanzhisu.trycloudflare.com`

---

## 方案三：Render.com 云端部署（需要信用卡）

> ⚠️ Render 需要绑定信用卡验证，即使是免费层。如无信用卡请使用方案一或二。

### 访问地址
- 平台主页：`https://你的应用名.onrender.com/`
- 小程序 H5：`https://你的应用名.onrender.com/m/`
- AI 健康检查：`https://你的应用名.onrender.com/ai-server/health`

### 步骤

#### 1. 注册账号
- GitHub 账号：https://github.com
- Render 账号：https://render.com（用 GitHub 账号登录）

#### 2. 推送到 GitHub
在项目根目录执行：
```bash
git init
git add .
git commit -m "初始化：滩智溯平台部署版"
git remote add origin https://github.com/你的用户名/tanzhi-su.git
git push -u origin main
```

#### 3. 创建 Web Service
1. 登录 https://dashboard.render.com
2. 点击 **New +** → **Web Service**
3. 选择 **Build and deploy from a Git repository**
4. 连接 GitHub，选择仓库
5. 配置：

| 配置项 | 值 |
|--------|-----|
| Name | `tanzhi-su-platform` |
| Runtime | Python 3 |
| Region | Singapore |
| Branch | main |
| Build Command | `bash build.sh` |
| Start Command | `gunicorn wsgi:application --config gunicorn.conf.py` |
| Instance Type | Free |

6. 添加环境变量：

| Key | Value |
|-----|-------|
| `DEPLOY_MODE` | `render` |
| `AI_API_KEY` | `sk-cf236fba5bed47d392bd842a027f3864` |
| `AI_BASE_URL` | `https://api.deepseek.com/v1` |
| `AI_MODEL` | `deepseek-chat` |
| `AGENT_SERVER_URL` | `http://127.0.0.1:5000/ai-server` |
| `SECRET_KEY` | 点击 Generate 自动生成 |

7. Health Check Path 填 `/ai-server/health`
8. 点击 **Create Web Service**

#### 4. 使用 Blueprint 快速部署（推荐）
项目根目录已包含 `render.yaml` 蓝图配置：
1. 点击 **New +** → **Blueprint**
2. 选择 GitHub 仓库
3. 手动填写 `AI_API_KEY`
4. 点击 **Apply**

---

## 验证测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 农户 | farmer001 | 123456 |
| 合作社 | coop001 | 123456 |
| 企业 | ent001 | 123456 |
| 监管 | reg001 | 123456 |

---

## 常见问题

### 问题：H5 构建失败（Render 内存不足）
本地构建后提交：
```bash
npm install --legacy-peer-deps
npm run build:h5
git add dist/h5/
git commit -m "构建H5"
git push
```

### 问题：AI 功能返回降级提示
1. 检查环境变量 `AI_API_KEY` 是否正确
2. 访问 `/ai-server/health` 确认 AI 服务在线

### 问题：ngrok URL 每次重启都变
这是免费版正常行为。比赛前重启一次，整个比赛期间 URL 不变。

### 问题：电脑关机后无法访问
ngrok 和 Cloudflare Tunnel 都是本地映射，电脑必须开机运行。如需 24/7 运行，建议使用 Render 云端部署。
