# 滩智溯平台部署指南（Render.com 免费层）

## 一、部署方案说明

| 项目 | 说明 |
|------|------|
| 部署平台 | Render.com 免费层 |
| 费用 | 免费（750 小时/月，足够 1 个服务 24 小时运行） |
| 服务数量 | 1 个 Web Service（主应用 + AI 智能体 + 小程序 H5 合并部署） |
| 数据库 | SQLite（临时存储，重启后自动重建演示数据，适合比赛演示） |
| 有效期 | 长期免费，适合 2 个月比赛演示 |
| 冷启动 | 15 分钟无访问会休眠，下次访问需 30-50 秒唤醒 |

### 访问地址
- 平台主页：`https://你的应用名.onrender.com/`
- 小程序 H5：`https://你的应用名.onrender.com/m/`
- AI 健康检查：`https://你的应用名.onrender.com/ai-server/health`

---

## 二、部署前准备

### 1. 注册账号
- GitHub 账号：https://github.com（用于托管代码）
- Render 账号：https://render.com（用 GitHub 账号登录）

### 2. 安装 Git
- 下载地址：https://git-scm.com/downloads
- 安装后在终端验证：`git --version`

---

## 三、部署步骤

### 步骤 1：初始化 Git 仓库并推送到 GitHub

在项目根目录 `c:\Users\ASUS\Desktop\平台` 下打开终端（PowerShell）：

```powershell
# 1. 初始化 Git 仓库
git init

# 2. 配置用户信息（如未配置过）
git config user.name "你的名字"
git config user.email "你的邮箱"

# 3. 添加所有文件（.gitignore 会自动排除敏感文件和依赖）
git add .

# 4. 首次提交
git commit -m "初始化：滩智溯平台部署版"

# 5. 在 GitHub 网站上新建仓库（不要勾选初始化 README）
#    仓库地址类似：https://github.com/你的用户名/tanzhi-su

# 6. 关联远程仓库并推送
git remote add origin https://github.com/你的用户名/tanzhi-su.git
git branch -M main
git push -u origin main
```

> **注意**：`.gitignore` 已排除 `ai_config.json`（含 API Key）、`instance/`（数据库）、`.venv/`、`node_modules/` 等文件，不会推送到 GitHub。

### 步骤 2：在 Render 创建 Web Service

1. 登录 https://dashboard.render.com
2. 点击右上角 **New +** → 选择 **Web Service**
3. 选择 **Build and deploy from a Git repository**
4. 连接你的 GitHub 账号，选择刚才推送的仓库 `tanzhi-su`
5. 填写配置：

| 配置项 | 值 |
|--------|-----|
| Name | `tanzhi-su`（自定义，决定访问域名） |
| Runtime | Python 3 |
| Region | Singapore（或离你最近的） |
| Branch | main |
| Build Command | `./build.sh` |
| Start Command | `gunicorn wsgi:application --config gunicorn.conf.py` |
| Instance Type | Free |

6. 点击 **Advanced** 展开高级设置，添加环境变量：

| Key | Value | 说明 |
|-----|-------|------|
| `DEPLOY_MODE` | `render` | 部署模式标识 |
| `AI_API_KEY` | `sk-cf236fba5bed47d392bd842a027f3864` | DeepSeek API Key |
| `AI_BASE_URL` | `https://api.deepseek.com/v1` | 大模型接口地址 |
| `AI_MODEL` | `deepseek-chat` | 模型名称 |
| `AGENT_SERVER_URL` | `http://127.0.0.1:5000/ai-server` | AI 服务挂载地址 |

> `SECRET_KEY` 会在 render.yaml 中自动生成，无需手动填写。
> 如果使用 render.yaml 蓝图部署，环境变量会自动配置，只需手动填写 `AI_API_KEY`。

7. 点击 **Create Web Service** 开始部署

### 步骤 3：使用 Blueprint 快速部署（推荐）

项目根目录已包含 `render.yaml` 蓝图配置，可一键部署：

1. 登录 https://dashboard.render.com
2. 点击右上角 **New +** → 选择 **Blueprint**
3. 选择你的 GitHub 仓库 `tanzhi-su`
4. Render 会自动识别 `render.yaml` 并创建服务
5. 在环境变量列表中找到 `AI_API_KEY`，填入：`sk-cf236fba5bed47d392bd842a027f3864`
6. 点击 **Apply** 开始部署

### 步骤 4：等待构建完成

- 构建过程约 5-10 分钟（首次需安装 Python 和 Node.js 依赖）
- 构建日志可在 Render 控制台实时查看
- 构建成功后，状态会显示为 **Live**
- 访问 `https://你的应用名.onrender.com/` 即可看到登录页面

---

## 四、部署后验证

### 1. 平台功能验证
访问以下地址，确认功能正常：

| 功能 | 访问地址 | 预期结果 |
|------|---------|---------|
| 登录页 | `https://域名/` | 显示登录页面 |
| AI 健康 | `https://域名/ai-server/health` | 返回 `{"code":200,"status":"online"}` |
| 小程序 H5 | `https://域名/m/` | 显示小程序首页 |

### 2. 登录测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 农户 | farmer001 | 123456 |
| 合作社 | coop001 | 123456 |
| 企业 | ent001 | 123456 |
| 监管 | reg001 | 123456 |

### 3. AI 智能体验证
登录监管端后，访问 AI 生态评估或灾害预警页面，确认 AI 功能正常。

---

## 五、常见问题处理

### 问题 1：H5 构建失败（内存不足）
**现象**：构建日志显示 `JavaScript heap out of memory`

**解决方案**：本地构建后提交
```powershell
# 在项目根目录执行
npm run build:h5
git add dist/h5/
git commit -m "构建H5"
git push
```
Render 会自动重新部署。

### 问题 2：首次访问很慢
**原因**：免费层 15 分钟无访问会休眠，冷启动需 30-50 秒

**解决方案**：比赛前 1 分钟先访问一次唤醒服务

### 问题 3：AI 功能返回降级提示
**现象**：显示"AI智能体平台未启动"

**解决方案**：
1. 检查 Render 控制台环境变量 `AI_API_KEY` 是否正确
2. 访问 `https://域名/ai-server/health` 确认返回 online
3. 检查 `AGENT_SERVER_URL` 是否为 `http://127.0.0.1:5000/ai-server`

### 问题 4：数据库数据丢失
**原因**：Render 免费层为临时文件系统，重启后 SQLite 数据丢失

**说明**：这是预期行为，应用启动时会自动调用 `init_demo_data` 重建完整演示数据，不影响比赛演示

### 问题 5：git push 报错文件过大
**解决方案**：确保 `.gitignore` 正确排除了 `node_modules/` 和 `.venv/`
```powershell
git rm -r --cached node_modules .venv  # 清除缓存
git commit -m "清理缓存"
git push
```

---

## 六、本地构建 H5（可选，推荐）

为避免云端构建失败，建议本地构建 H5 后提交：

```powershell
# 1. 确保已安装 Node.js（https://nodejs.org）
node --version  # 需要 16+

# 2. 安装依赖（首次需要）
npm install --legacy-peer-deps

# 3. 构建 H5
npm run build:h5

# 4. 提交构建产物
git add dist/h5/
git commit -m "构建H5（本地）"
git push
```

构建成功后，Render 部署时 `build.sh` 会检测到 `dist/h5` 已存在，跳过 H5 构建（如 Node.js 不可用）。

---

## 七、更新部署代码

后续如需修改代码并重新部署：

```powershell
# 1. 修改代码后提交
git add .
git commit -m "描述你的修改"
git push

# 2. Render 会自动检测到新提交，自动重新部署
#    也可在 Render 控制台手动触发 Manual Deploy
```

---

## 八、停止/删除服务

比赛结束后，如需停止服务避免占用免费时长：

1. 登录 Render 控制台
2. 进入服务设置
3. 选择 **Suspend**（暂停）或 **Delete**（删除）

---

## 九、部署文件清单

本次部署新增/修改的文件：

| 文件 | 作用 |
|------|------|
| `wsgi.py` | WSGI 入口，合并主应用与 AI 服务到单进程 |
| `Procfile` | Render 启动命令 |
| `render.yaml` | Render 蓝图配置 |
| `runtime.txt` | Python 版本 |
| `gunicorn.conf.py` | Gunicorn 生产环境配置 |
| `build.sh` | 构建脚本（Python 依赖 + H5 构建） |
| `.gitignore` | Git 忽略规则 |
| `requirements.txt` | 新增 gunicorn 依赖 |
| `app.py` | 支持环境变量配置数据库和端口 |
| `agent_server.py` | 支持环境变量配置 API Key |
| `services/agent_client.py` | 支持环境变量配置 AI 服务地址 |
