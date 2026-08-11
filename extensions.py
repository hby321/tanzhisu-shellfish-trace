"""
Flask扩展初始化文件
用于解决循环导入问题
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# 初始化扩展实例
db = SQLAlchemy()
login_manager = LoginManager()

# 配置登录视图
login_manager.login_view = 'auth.login'
login_manager.login_message = ''
login_manager.login_message_category = 'info'
