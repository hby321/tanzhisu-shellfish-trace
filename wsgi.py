# -*- coding: utf-8 -*-
"""
滩智溯 - 生产环境 WSGI 入口
============================================================
将主业务后端(Flask)与软著AI调度中枢(agent_server)合并为单进程，
适配 Render.com 等免费云平台单服务部署限制。

挂载策略：
  - 主业务后端：根路径 /
  - 软著AI调度中枢：/ai-server/*
    （原 agent_server 的 /agent/run → /ai-server/agent/run）

环境变量：
  PORT              Render 自动注入的监听端口
  AGENT_SERVER_URL  agent_client 调用地址（云端自动指向 /ai-server）
  DATABASE_URL      可选，覆盖默认 SQLite 路径
============================================================
"""
import os
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# 导入主应用工厂
from app import create_app
# 导入软著AI调度中枢应用
from agent_server import app as agent_app

# 创建主应用
application = create_app()

# 将软著AI调度中枢挂载到 /ai-server 路径下
# 原 agent_server 的路由 /agent/run → /ai-server/agent/run
# 原 agent_server 的路由 /health     → /ai-server/health
application.wsgi_app = DispatcherMiddleware(application.wsgi_app, {
    '/ai-server': agent_app,
})


# 供 gunicorn 直接调用
app = application


if __name__ == '__main__':
    # 本地调试用：gunicorn 启动时不会执行此分支
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, debug=False)
