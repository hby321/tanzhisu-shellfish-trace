# -*- coding: utf-8 -*-
"""
============================================================
滩智溯主后端 → 《数据智能体综合应用平台 V1.0》转发客户端
------------------------------------------------------------
本模块为滩智溯主业务后端(Flask 5000)与软著AI调度中枢
(端口8090)之间的唯一通信桥梁。

设计原则：
  1. 主后端所有AI入口必须经过本客户端转发至8090端口
  2. 主后端代码内禁止直接调用大模型API，保证软著为AI模块唯一载体
  3. 当8090服务不可用时，提供友好降级，不影响主业务流程
============================================================
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)

# 软著智能体调度服务地址
# 本地开发：默认 http://127.0.0.1:8090（agent_server.py 独立运行）
# 云端部署：通过环境变量 AGENT_SERVER_URL 指向挂载路径（如 http://127.0.0.1:5000/ai-server）
# Render 部署时 wsgi.py 将 agent_server 挂载到 /ai-server，所以同域自调用
AGENT_SERVER_URL = os.environ.get(
    'AGENT_SERVER_URL',
    'http://127.0.0.1:8090'
).rstrip('/')

# 云端模式下使用相对路径调用（避免端口硬编码）
# 当部署在 Render 等平台时，agent_server 已通过 wsgi.py 挂载到 /ai-server
# 此时主应用和 agent_server 在同一进程同一端口
IS_CLOUD_MODE = os.environ.get('DEPLOY_MODE', '').lower() in ('cloud', 'render', 'prod', 'production')

AGENT_RUN_ENDPOINT = f"{AGENT_SERVER_URL}/agent/run"
AGENT_HEALTH_ENDPOINT = f"{AGENT_SERVER_URL}/health"

# 转发超时（秒）- LLM 调用需要更长时间
TIMEOUT = 45


def is_agent_online():
    """探测软著智能体服务是否在线"""
    try:
        r = requests.get(AGENT_HEALTH_ENDPOINT, timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def call_agent(agent_name, env_data):
    """
    调用软著智能体平台统一调度入口

    参数:
        agent_name: 智能体名称（需与 agent_server.py 中 AGENT_REGISTRY 一致）
        env_data:   传入智能体的数据字典

    返回:
        dict: {
            "success": bool,
            "ai_reply": dict,     # 智能体返回结果
            "source": str,        # "agent_server" | "fallback"
            "message": str
        }
    """
    payload = {"agent": agent_name, "env_data": env_data}
    try:
        resp = requests.post(AGENT_RUN_ENDPOINT, json=payload, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 200:
                return {
                    "success": True,
                    "source": "agent_server",
                    "ai_reply": data.get("ai_reply", {}),
                    "meta": data.get("meta", {}),
                    "message": "智能体推理成功"
                }
            return {
                "success": False,
                "source": "agent_server",
                "ai_reply": {},
                "message": data.get("message", "智能体返回异常")
            }
        return {
            "success": False,
            "source": "agent_server",
            "ai_reply": {},
            "message": f"智能体服务HTTP {resp.status_code}"
        }
    except requests.exceptions.ConnectionError:
        logger.warning("软著智能体服务(8090)未启动，启用降级响应")
        return {
            "success": False,
            "source": "fallback",
            "ai_reply": {},
            "message": "AI智能体平台未启动，请先运行 agent_server.py（端口8090）"
        }
    except requests.exceptions.Timeout:
        logger.warning("软著智能体服务响应超时")
        return {
            "success": False,
            "source": "fallback",
            "ai_reply": {},
            "message": "AI智能体响应超时，请稍后重试"
        }
    except Exception as e:
        logger.error(f"调用智能体异常: {e}")
        return {
            "success": False,
            "source": "fallback",
            "ai_reply": {},
            "message": f"智能体调用异常: {str(e)}"
        }
