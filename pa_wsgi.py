# -*- coding: utf-8 -*-
"""
PythonAnywhere WSGI 配置文件
在 PythonAnywhere 后台设置面板中引用此文件路径
路径：/home/你的用户名/平台/pa_wsgi.py
"""
import os
import sys

# 添加项目路径
project_home = os.path.join(os.path.dirname(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 设置环境变量（云端配置）
os.environ['DEPLOY_MODE'] = 'pythonanywhere'
os.environ['AI_API_KEY'] = os.environ.get('AI_API_KEY', 'sk-cf236fba5bed47d392bd842a027f3864')
os.environ['AI_BASE_URL'] = os.environ.get('AI_BASE_URL', 'https://api.deepseek.com/v1')
os.environ['AI_MODEL'] = os.environ.get('AI_MODEL', 'deepseek-chat')
os.environ['AGENT_SERVER_URL'] = os.environ.get('AGENT_SERVER_URL', 'http://127.0.0.1:8090')

# 导入主应用
from app import create_app
application = create_app()

# 供 PythonAnywhere WSGI 引用
app = application
