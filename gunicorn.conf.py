# -*- coding: utf-8 -*-
"""
Gunicorn 生产环境配置
适配 Render.com 免费层（512MB 内存）
"""
import os

# 绑定端口：Render 自动注入 PORT 环境变量
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Worker 数量：免费层内存有限，2 个 worker 保证 AI 自调用不死锁
workers = 2

# Worker 类型：sync 适合 I/O 密集型（AI 调用为 HTTP 请求）
worker_class = 'sync'

# 超时设置：AI 智能体调用 LLM 需要较长时间
timeout = 120
graceful_timeout = 30
keepalive = 5

# 预加载应用：减少内存占用，加快启动
preload_app = True

# 日志
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# 最大请求数：防止内存泄漏，定期重启 worker
max_requests = 500
max_requests_jitter = 50
