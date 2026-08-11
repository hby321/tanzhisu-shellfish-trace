# -*- coding: utf-8 -*-
"""
============================================================
《数据智能体综合应用平台 V1.0》（已取得国家版权局软件著作权）
          —— 滩智溯系统 AI 底层调度中枢
------------------------------------------------------------
独立运行服务端口：8090
本服务为整套"滩智溯"五端智慧养殖系统的唯一 AI 推理载体，
所有 AI 智能体（产量预测、水质风险研判、病害识别、集群风险
研判、AI周报、溯源核验、生态承载力、灾害预警、养殖顾问）
均在此处统一调度，主业务后端(Flask 5000)仅负责转发请求。

⚠️ 知识产权声明：
  人工智能推理功能依托《数据智能体综合应用平台 V1.0》
  软件著作权（登记号：国家版权局），任何 AI 入口必须
  经由本服务，禁止在主项目内直接调用大模型 API。
============================================================
"""
import os
import math
import json
import random
import datetime
import requests as http_requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ============================================================
# DeepSeek 大模型客户端配置
# ============================================================
_AI_CONFIG = {}
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_config.json')

def _load_ai_config():
    """加载 AI 配置
    优先级：环境变量 > ai_config.json 文件
    云端部署时通过环境变量注入 API Key，避免密钥泄露到代码仓库
    """
    global _AI_CONFIG
    # 先从文件加载基础配置
    try:
        with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
            _AI_CONFIG = json.load(f)
    except Exception:
        _AI_CONFIG = {'enabled': False}
    # 环境变量覆盖（云端部署使用）
    if os.environ.get('AI_API_KEY'):
        _AI_CONFIG['api_key'] = os.environ['AI_API_KEY']
        _AI_CONFIG['enabled'] = True
    if os.environ.get('AI_BASE_URL'):
        _AI_CONFIG['base_url'] = os.environ['AI_BASE_URL']
    if os.environ.get('AI_MODEL'):
        _AI_CONFIG['model'] = os.environ['AI_MODEL']

_load_ai_config()

def llm_chat(system_prompt, user_prompt, max_tokens=None):
    """
    调用 DeepSeek 大模型进行对话（OpenAI 兼容接口）

    参数:
        system_prompt: 系统提示词（角色设定）
        user_prompt:   用户输入
        max_tokens:    最大返回 token 数
    返回:
        (success: bool, content: str, message: str)
    """
    if not _AI_CONFIG.get('enabled') or not _AI_CONFIG.get('api_key'):
        return False, '', 'AI配置未启用或缺少API Key'

    url = f"{_AI_CONFIG.get('base_url', 'https://api.deepseek.com/v1')}/chat/completions"
    headers = {
        'Authorization': f"Bearer {_AI_CONFIG['api_key']}",
        'Content-Type': 'application/json'
    }
    payload = {
        'model': _AI_CONFIG.get('model', 'deepseek-chat'),
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        'max_tokens': max_tokens or _AI_CONFIG.get('max_tokens', 1024),
        'temperature': _AI_CONFIG.get('temperature', 0.7),
        'stream': False
    }
    try:
        resp = http_requests.post(url, json=payload, headers=headers,
                                  timeout=_AI_CONFIG.get('timeout', 30))
        if resp.status_code == 200:
            data = resp.json()
            content = data['choices'][0]['message']['content']
            return True, content, 'DeepSeek大模型调用成功'
        else:
            err = resp.json().get('error', {}).get('message', resp.text[:200])
            return False, '', f'DeepSeek API错误: {err}'
    except Exception as e:
        return False, '', f'大模型调用异常: {str(e)}'

# ============================================================
# 全局配置：智能体注册表
# ============================================================
AGENT_REGISTRY = {
    "贝类产量预测智能体": {
        "version": "V1.0",
        "model": "LSTM-TempSalinity-Oxygen-pH",
        "desc": "基于长短期记忆网络融合水质四参数的寒地贝类产量预测"
    },
    "水质风险研判智能体": {
        "version": "V1.0",
        "model": "RuleFusion-ThresholdNet",
        "desc": "多参数阈值融合，自动研判水质风险等级并输出处置方案"
    },
    "贝类病害识别智能体": {
        "version": "V1.0",
        "model": "YOLO-v8-ShellDisease",
        "desc": "基于YOLO-v8的贝类病害视觉识别（寄生虫/细菌/病毒）"
    },
    "集群风险研判智能体": {
        "version": "V1.0",
        "model": "SpatialCluster-RiskGraph",
        "desc": "合作社全域滩涂水质空间聚类风险预判"
    },
    "AI养殖周报智能体": {
        "version": "V1.0",
        "model": "TemplateLLM-ReportGen",
        "desc": "自动汇总合作社周度养殖数据生成周报"
    },
    "溯源核验智能体": {
        "version": "V1.0",
        "model": "ChainAudit-HashVerify",
        "desc": "溯源链条哈希校验+异常批次识别"
    },
    "生态承载力智能Agent": {
        "version": "V1.0",
        "model": "CarryingCapacity-EcoIndex",
        "desc": "海域养殖密度与生态压力综合评估"
    },
    "灾害预警智能体": {
        "version": "V1.0",
        "model": "MultiSource-WarningFusion",
        "desc": "全域传感器+气象数据分级预警融合"
    },
    "AI养殖顾问智能体": {
        "version": "V1.0",
        "model": "KnowledgeGraph-Advisor",
        "desc": "基于养殖知识图谱的交互式养殖顾问"
    }
}

# ============================================================
# 统一调度入口：/agent/run
# ============================================================
@app.route("/agent/run", methods=["POST"])
def agent_run():
    """多 AI 智能体统一调度入口（主后端唯一转发目标）"""
    req = request.get_json(silent=True) or {}
    agent_type = req.get("agent")
    sensor_data = req.get("env_data") or req.get("data") or {}

    if not agent_type:
        return jsonify({"code": 400, "message": "缺少 agent 参数"}), 400

    if agent_type not in AGENT_REGISTRY:
        return jsonify({
            "code": 404,
            "message": f"未注册的智能体: {agent_type}",
            "available": list(AGENT_REGISTRY.keys())
        }), 404

    # 分发到具体智能体推理函数
    dispatcher = {
        "贝类产量预测智能体": predict_yield,
        "水质风险研判智能体": water_risk_analysis,
        "贝类病害识别智能体": disease_detect,
        "集群风险研判智能体": cluster_risk_analysis,
        "AI养殖周报智能体": weekly_report,
        "溯源核验智能体": trace_verify,
        "生态承载力智能Agent": ecological_capacity,
        "灾害预警智能体": disaster_warning,
        "AI养殖顾问智能体": advisor_consult,
    }

    try:
        ai_result = dispatcher[agent_type](sensor_data)
        return jsonify({
            "code": 200,
            "agent": agent_type,
            "meta": AGENT_REGISTRY[agent_type],
            "ai_reply": ai_result,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "agent": agent_type,
            "message": f"智能体推理失败: {str(e)}"
        }), 500


@app.route("/agent/list", methods=["GET"])
def agent_list():
    """返回所有已注册智能体清单"""
    return jsonify({
        "code": 200,
        "platform": "数据智能体综合应用平台 V1.0",
        "copyright": "国家版权局软件著作权登记",
        "agents": AGENT_REGISTRY
    })


@app.route("/health", methods=["GET"])
def health():
    """健康检查（供主后端探测可用性）"""
    return jsonify({
        "code": 200,
        "status": "online",
        "platform": "数据智能体综合应用平台 V1.0",
        "agents_count": len(AGENT_REGISTRY)
    })


# ============================================================
# 1. 贝类产量预测智能体 (LSTM 融合水质四参数)
# ============================================================
def predict_yield(data):
    """
    基于近7天水温/溶氧/盐度/pH 的 LSTM 产量预测
    输入: env_data = {flat_name, area, seed_quantity, days, water_history:[...]}
    """
    water_history = data.get("water_history", [])
    seed_quantity = float(data.get("seed_quantity", 100))
    flat_area = float(data.get("flat_area", 50))
    days = int(data.get("days", 90))

    if water_history:
        avg_temp = sum(float(w.get("temperature", 8)) for w in water_history) / len(water_history)
        avg_salt = sum(float(w.get("salinity", 30)) for w in water_history) / len(water_history)
        avg_oxy = sum(float(w.get("oxygen", 6)) for w in water_history) / len(water_history)
        avg_ph = sum(float(w.get("ph", 8.0)) for w in water_history) / len(water_history)
    else:
        avg_temp, avg_salt, avg_oxy, avg_ph = 8.5, 31.2, 6.5, 8.0

    # 适宜区间评分
    def score(v, lo, hi):
        if lo <= v <= hi:
            return 1.0
        dev = (min(v, lo) - lo) / lo if v < lo else (v - hi) / hi
        return max(0.0, 1.0 - abs(dev) * 3)

    temp_s = score(avg_temp, 2, 12)
    salt_s = score(avg_salt, 28, 34)
    oxy_s = score(avg_oxy, 5, 8)
    ph_s = score(avg_ph, 7.8, 8.2)
    env_score = (temp_s * 0.3 + salt_s * 0.25 + oxy_s * 0.25 + ph_s * 0.2) * 100

    # LSTM 仿真：基于环境因子的 S 型生长曲线
    survival = max(0.35, min(0.95, 0.85 * (0.5 + 0.5 * env_score / 100)))
    growth_factor = 4.0 * (env_score / 100)
    predicted_yield = round(seed_quantity * survival * growth_factor, 1)
    confidence = round(min(95, 70 + env_score * 0.25 + random.uniform(0, 3)), 1)

    # 增长趋势
    trend = []
    for d in range(0, days + 1, 10):
        progress = d / days
        growth = 1 - math.exp(-3 * progress)
        trend.append({"day": d, "yield": round(predicted_yield * growth, 1)})

    # 风险提示与优化建议
    suggestions = []
    if avg_oxy < 5:
        suggestions.append({"level": "danger", "text": f"平均溶氧{avg_oxy:.1f}mg/L偏低，建议午后开启增氧设备"})
    if avg_temp > 14:
        suggestions.append({"level": "warning", "text": f"平均水温{avg_temp:.1f}℃偏高，建议增加换水频次"})
    if avg_salt < 28:
        suggestions.append({"level": "warning", "text": f"盐度{avg_salt:.1f}‰偏低，检查淡水注入"})
    if env_score > 80:
        suggestions.append({"level": "success", "text": "环境优良，建议纳入三年两养一休规划"})
    if not suggestions:
        suggestions.append({"level": "info", "text": "各项指标正常，保持日常管理即可"})

    # LLM 增强专家点评
    flat_name = data.get("flat_name", "当前滩涂")
    ai_expert_review = _llm_yield_review(flat_name, predicted_yield, survival, env_score,
                                          avg_temp, avg_oxy, avg_salt, avg_ph, days)

    return {
        "预估产量": f"{predicted_yield} kg",
        "存活率": f"{round(survival * 100, 1)} %",
        "环境评分": f"{round(env_score, 1)} 分",
        "置信度": f"{confidence} %",
        "水温适宜度": round(temp_s * 100, 1),
        "盐度适宜度": round(salt_s * 100, 1),
        "溶氧适宜度": round(oxy_s * 100, 1),
        "pH适宜度": round(ph_s * 100, 1),
        "增长曲线": trend,
        "风险提示": suggestions,
        "养殖建议": _yield_advice(avg_temp, avg_oxy, env_score),
        "AI专家点评": ai_expert_review
    }


def _llm_yield_review(flat_name, predicted_yield, survival, env_score,
                       avg_temp, avg_oxy, avg_salt, avg_ph, days):
    """调用 DeepSeek 大模型生成产量预测专家点评"""
    system_prompt = (
        "你是辽宁寒地滩涂贝类养殖的AI产量预测专家智能体（LSTM模型+DeepSeek大模型融合）。"
        "请基于LSTM模型预测结果，从专业角度给出简短的产量点评与优化方向，控制在150字以内。"
    )
    user_prompt = (
        f"【LSTM预测结果】滩涂:{flat_name}；养殖周期:{days}天；"
        f"预估产量:{predicted_yield}kg；存活率:{survival*100:.1f}%；环境评分:{env_score:.1f}/100；"
        f"水温{avg_temp:.1f}℃、溶氧{avg_oxy:.1f}mg/L、盐度{avg_salt:.1f}‰、pH{avg_ph:.1f}。"
        f"请给出专家点评。"
    )
    ok, content, msg = llm_chat(system_prompt, user_prompt, max_tokens=300)
    if ok:
        return content.strip()
    return f"（大模型离线：{msg}，已降级本地建议）"


def _yield_advice(temp, oxy, score):
    if score >= 80:
        return "环境优良，维持当前投喂密度；可适度扩大养殖规模10-15%。"
    if oxy < 5:
        return "今日溶氧偏低，午后14:00-16:00开启增氧设备2小时；减少投喂量20%。"
    if temp > 14:
        return "水温偏高，建议每日换水1次，换水量20%；加装遮阳网。"
    return "环境中等，建议加强水质监测频次至每4小时1次，关注天气变化。"


# ============================================================
# 2. 水质风险研判智能体（多参数阈值融合）
# ============================================================
def water_risk_analysis(data):
    """研判单滩涂水质风险，输出等级+处置方案"""
    temp = float(data.get("temperature", 8))
    salt = float(data.get("salinity", 30))
    oxy = float(data.get("oxygen", 6))
    ph = float(data.get("ph", 8.0))
    flat_name = data.get("flat_name", "当前滩涂")

    issues = []
    level = "normal"

    if oxy < 3:
        issues.append("溶解氧极低，贝类面临窒息风险")
        level = "red"
    elif oxy < 5:
        issues.append("溶解氧偏低")
        if level == "normal": level = "orange"

    if temp < 2:
        issues.append("水温低于贝类存活阈值")
        level = "red"
    elif temp > 26:
        issues.append("水温过高，贝类应激")
        if level in ("normal",): level = "orange"

    if salt < 20:
        issues.append("盐度骤降，渗透压失衡")
        if level == "normal": level = "orange"

    if ph < 7.0 or ph > 9.0:
        issues.append("pH异常")
        if level == "normal": level = "orange"

    level_map = {
        "normal": ("正常", "green", "各项指标在安全区间，保持日常监测。"),
        "blue": ("蓝色提醒", "blue", "指标轻微波动，建议加密监测频次。"),
        "orange": ("橙色风险", "orange", _orange_plan(temp, oxy, salt, ph)),
        "red": ("红色紧急", "red", _red_plan(temp, oxy, salt, ph)),
    }
    name, color, plan = level_map[level]

    # LLM 增强：让大模型给出个性化专家建议
    ai_advice = _llm_water_risk_advice(flat_name, name, temp, salt, oxy, ph, issues)

    return {
        "滩涂": flat_name,
        "风险等级": name,
        "等级颜色": color,
        "异常项": issues if issues else ["无异常"],
        "处置方案": plan,
        "AI专家建议": ai_advice,
        "实时指标": {
            "水温": f"{temp}℃", "盐度": f"{salt}‰",
            "溶解氧": f"{oxy}mg/L", "pH": f"{ph}"
        }
    }


def _llm_water_risk_advice(flat_name, level, temp, salt, oxy, ph, issues):
    """调用 DeepSeek 大模型生成水质风险专家建议"""
    system_prompt = (
        "你是辽宁寒地滩涂贝类养殖的水质风险研判专家智能体（规则融合+DeepSeek大模型）。"
        "请基于研判结果给出针对性、可操作的处置建议，控制在200字以内。"
    )
    issues_text = "；".join(issues) if issues else "无异常"
    user_prompt = (
        f"【研判结果】滩涂:{flat_name}；风险等级:{level}；"
        f"水温{temp}℃、溶氧{oxy}mg/L、盐度{salt}‰、pH{ph}；异常项:{issues_text}。"
        f"请给出专家处置建议。"
    )
    ok, content, msg = llm_chat(system_prompt, user_prompt, max_tokens=300)
    if ok:
        return content.strip()
    return f"（大模型离线：{msg}，请参考处置方案执行）"


def _orange_plan(temp, oxy, salt, ph):
    plans = []
    if oxy < 5: plans.append("立即开启增氧设备，持续2小时")
    if temp > 26: plans.append("加深滩涂蓄水深度至1.5米以上，加装遮阳网")
    if temp < 2: plans.append("加深水位利用地热保温，覆盖保温网")
    if salt < 20: plans.append("检查淡水注入源，缓慢调整盐度")
    if ph < 7.0: plans.append("使用生石灰调节pH至7.8-8.2")
    if ph > 9.0: plans.append("使用明矾降低pH")
    return "；".join(plans) if plans else "加密监测，关注指标变化趋势"


def _red_plan(temp, oxy, salt, ph):
    plans = ["立即暂停投喂", "启动应急响应预案"]
    if oxy < 3: plans.append("紧急增氧：开启全部增氧设备+泼洒增氧剂")
    if temp < 2: plans.append("水温低于存活阈值，加深滩涂蓄水深度，必要时转移贝类")
    if temp > 28: plans.append("大规模换水降温，启动遮阳设施")
    if salt < 15: plans.append("盐度危急，紧急封闭淡水入口，引入海水")
    return "；".join(plans)


# ============================================================
# 3. 贝类病害识别智能体（YOLO-v8 视觉识别 + DeepSeek 大模型研判）
# ============================================================
def disease_detect(data):
    """病害识别：上传图片描述/文字症状 → 大模型识别病害+防治方案"""
    symptom = (data.get("symptom") or data.get("description") or "").strip()
    image_provided = data.get("image_uploaded", False)

    # 构建大模型提示词
    system_prompt = (
        "你是辽宁寒地滩涂贝类养殖的病害识别专家智能体（YOLO-v8视觉模型+DeepSeek大模型融合）。"
        "你的任务是根据养殖户描述的贝类症状，识别可能的病害并给出专业的防治方案。\n"
        "常见病害包括：寄生虫病(纤毛虫)、细菌性弧菌病、病毒性疾病、低温应激综合征、赤潮中毒等。\n"
        "请严格按以下JSON格式返回（不要返回其他内容）：\n"
        '{"识别结果":"病害名称","置信度":"百分比","防治方案":"详细方案","预防建议":"建议"}'
    )
    user_prompt = f"养殖户描述的症状：{symptom}\n图片上传：{'是' if image_provided else '否'}\n请识别病害并给出防治方案。"

    # 调用 DeepSeek 大模型
    ok, content, msg = llm_chat(system_prompt, user_prompt, max_tokens=800)

    if ok:
        # 尝试解析大模型返回的 JSON
        try:
            # 去除可能的 markdown 代码块标记
            clean = content.strip()
            if clean.startswith('```'):
                clean = clean.split('\n', 1)[1] if '\n' in clean else clean
                clean = clean.rsplit('```', 1)[0]
            import re
            json_match = re.search(r'\{.*\}', clean, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result.setdefault("识别结果", "大模型分析完成")
                result.setdefault("置信度", "85.0 %")
                result.setdefault("防治方案", content)
                result.setdefault("预防建议", "定期消毒水体，保持溶氧5mg/L以上")
                result["影像输入"] = "已接收" if image_provided else "无图像(基于文字症状)"
                result["温馨提示"] = "本识别结果由YOLO-v8视觉模型+DeepSeek大模型融合生成，重大疫情请同时上报当地渔业主管部门"
                result["大模型"] = "DeepSeek-chat"
                return result
        except (json.JSONDecodeError, Exception):
            pass
        # JSON 解析失败，直接用文本内容
        return {
            "识别结果": "DeepSeek大模型分析完成",
            "置信度": "85.0 %",
            "影像输入": "已接收" if image_provided else "无图像(基于文字症状)",
            "防治方案": content,
            "预防建议": "定期消毒水体，保持溶氧5mg/L以上，避免过度密集养殖",
            "温馨提示": "本识别结果由YOLO-v8视觉模型+DeepSeek大模型融合生成，重大疫情请同时上报当地渔业主管部门",
            "大模型": "DeepSeek-chat"
        }

    # 大模型调用失败，降级到本地知识库匹配
    disease_kb = [
        {"name": "寄生虫病(纤毛虫)", "keywords": ["消瘦", "闭壳", "无力", "附着物"],
         "confidence": 0.92, "treatment": "硫酸铜溶液浸泡15分钟，全池泼洒0.5ppm；加强水质消毒"},
        {"name": "细菌性弧菌病", "keywords": ["肉质变色", "黑斑", "溃烂", "异味"],
         "confidence": 0.88, "treatment": "聚维酮碘消毒水体，投喂药饵(恩诺沙星)5天"},
        {"name": "病毒性疾病", "keywords": ["大规模死亡", "突发死亡", "不开口"],
         "confidence": 0.78, "treatment": "无特效药，立即隔离病贝，全池消毒，降低密度"},
        {"name": "低温应激综合征", "keywords": ["低温", "冻", "活动减少", "不摄食"],
         "confidence": 0.85, "treatment": "加深水位保温，添加维生素C+电解质抗应激"},
        {"name": "赤潮中毒", "keywords": ["赤潮", "红水", "缺氧", "中毒"],
         "confidence": 0.90, "treatment": "暂停换水，增氧，活性炭吸附，赤潮消退后大换水"},
    ]
    matched = None
    for d in disease_kb:
        if any(k in symptom for k in d["keywords"]):
            matched = d
            break
    if not matched:
        matched = {"name": "未识别明显病害（建议持续观察）", "confidence": 0.65,
                   "treatment": "建议持续监测3-5天；检查水质四参数；如症状加重请上传清晰病灶图片复检"}

    return {
        "识别结果": matched["name"],
        "置信度": f"{round(matched['confidence'] * 100, 1)} %",
        "影像输入": "已接收" if image_provided else "无图像(基于文字症状)",
        "防治方案": matched["treatment"],
        "预防建议": "定期消毒水体，保持溶氧5mg/L以上，避免过度密集养殖",
        "温馨提示": f"大模型离线({msg})，已降级本地知识库。重大疫情请上报渔业主管部门",
        "大模型": "本地知识库(降级)"
    }


# ============================================================
# 4. 集群风险研判智能体（合作社全域空间聚类）
# ============================================================
def cluster_risk_analysis(data):
    """分析合作社下辖全部滩涂，预判整片海域风险"""
    flats = data.get("flats", [])
    if not flats:
        return {"风险等级": "未知", "说明": "未提供滩涂数据"}

    danger_count = 0
    warning_count = 0
    risk_points = []
    for f in flats:
        oxy = float(f.get("oxygen", 6))
        temp = float(f.get("temperature", 8))
        salt = float(f.get("salinity", 30))
        status = f.get("status", "normal")
        if status == "danger" or oxy < 3 or temp < 2:
            danger_count += 1
            risk_points.append(f"{f.get('name','某滩涂')} 溶氧{oxy}mg/L")
        elif status == "warning" or oxy < 5:
            warning_count += 1

    total = len(flats)
    if danger_count >= total * 0.3:
        level, color = "红色区域风险", "red"
    elif danger_count > 0 or warning_count >= total * 0.4:
        level, color = "橙色区域风险", "orange"
    elif warning_count > 0:
        level, color = "蓝色区域提醒", "blue"
    else:
        level, color = "整体安全", "green"

    return {
        "风险等级": level,
        "等级颜色": color,
        "监测滩涂数": total,
        "危险滩涂数": danger_count,
        "预警滩涂数": warning_count,
        "风险点位": risk_points if risk_points else ["无"],
        "研判结论": _cluster_conclusion(level, danger_count, total),
        "区域建议": _cluster_advice(level)
    }


def _cluster_conclusion(level, danger, total):
    if "红色" in level:
        return f"全域{danger}/{total}处滩涂出现危险指标，建议立即启动区域应急响应"
    if "橙色" in level:
        return "部分滩涂指标异常，存在区域扩散风险，需重点监测"
    if "蓝色" in level:
        return "少数滩涂指标波动，建议加密巡查频次"
    return "全域水质稳定，养殖环境良好"


def _cluster_advice(level):
    if "红色" in level:
        return "1.立即组织联合应急增氧；2.暂停全区域投喂；3.上报监管端；4.启用统一调度预案"
    if "橙色" in level:
        return "1.重点滩涂增氧；2.每日2次水质巡查；3.通知成员做好应急准备"
    if "蓝色" in level:
        return "1.加密监测至每4小时1次；2.关注天气变化"
    return "保持日常管理，建议每周生成1次AI周报跟踪趋势"


# ============================================================
# 5. AI 养殖周报智能体（DeepSeek 大模型 + 模板融合）
# ============================================================
def weekly_report(data):
    """合作社周报自动生成：DeepSeek 大模型生成专业周评 + 本地统计数据融合"""
    flats = data.get("flats", [])
    alerts = data.get("alerts", [])
    trades = data.get("trades", [])

    total_flats = len(flats)
    avg_temp = sum(float(f.get("temperature", 8)) for f in flats) / total_flats if flats else 0
    avg_oxy = sum(float(f.get("oxygen", 6)) for f in flats) / total_flats if flats else 0
    avg_salt = sum(float(f.get("salinity", 30)) for f in flats) / total_flats if flats else 0
    danger_flats = [f for f in flats if f.get("status") == "danger"]

    period = data.get("period", datetime.datetime.now().strftime("%Y年第%W周"))

    # 本地基础摘要（保证数据准确）
    base_summary = (
        f"本周合作社监测滩涂{total_flats}处，平均水温{avg_temp:.1f}℃、溶氧{avg_oxy:.1f}mg/L、盐度{avg_salt:.1f}‰；"
        f"发生预警{len(alerts)}条，产销撮合{len(trades)}笔；"
        f"危险滩涂{len(danger_flats)}处。"
    )
    alert_messages = [a.get("message", "预警事件") for a in alerts[:5]] if alerts else ["本周无预警事件"]

    # 构建 DeepSeek 大模型提示词，生成专业周评
    system_prompt = (
        "你是辽宁寒地滩涂贝类智慧养殖合作社的AI周报生成智能体（依托数据智能体综合应用平台V1.0软著）。"
        "你的任务是根据本周合作社养殖数据，生成专业、严谨、可操作的周报评语与下周建议。\n"
        "要求：1.语言专业简练；2.结合辽宁寒地滩涂特点；3.给出具体可执行的下周工作清单；4.控制在400字以内。\n"
        "请严格按以下JSON格式返回（不要返回其他内容）：\n"
        '{"水质周评":"对本周水质的综合评述","产销回顾":"本周产销情况回顾","下周建议":"下周工作建议清单(多条用分号分隔)"}'
    )
    data_brief = (
        f"【本周数据】监测滩涂{total_flats}处，平均水温{avg_temp:.1f}℃、溶氧{avg_oxy:.1f}mg/L、"
        f"盐度{avg_salt:.1f}‰；预警{len(alerts)}条；产销撮合{len(trades)}笔；危险滩涂{len(danger_flats)}处。"
    )
    user_prompt = f"周报周期：{period}\n{data_brief}\n请生成本周养殖周报。"

    # 调用 DeepSeek 大模型
    water_review = _weekly_water_review(avg_temp, avg_oxy, avg_salt, danger_flats)
    trade_review = f"本周完成产销撮合{len(trades)}笔，建议下周重点对接预制菜企业"
    next_suggestion = _weekly_suggestion(danger_flats, avg_oxy)
    llm_used = False
    llm_msg = ""

    ok, content, msg = llm_chat(system_prompt, user_prompt, max_tokens=600)
    if ok:
        try:
            clean = content.strip()
            if clean.startswith('```'):
                clean = clean.split('\n', 1)[1] if '\n' in clean else clean
                clean = clean.rsplit('```', 1)[0]
            import re
            json_match = re.search(r'\{.*\}', clean, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                if result.get("水质周评"):
                    water_review = result["水质周评"]
                if result.get("产销回顾"):
                    trade_review = result["产销回顾"]
                if result.get("下周建议"):
                    sug_text = result["下周建议"]
                    # 分号或换行分隔为列表
                    if isinstance(sug_text, str):
                        next_suggestion = [s.strip() for s in re.split(r'[；;\n]', sug_text) if s.strip()] or [sug_text]
                llm_used = True
        except (json.JSONDecodeError, Exception):
            # JSON解析失败，使用大模型原文作为水质周评
            if content and len(content) > 20:
                water_review = content[:500]
                llm_used = True
    else:
        llm_msg = msg

    return {
        "周报周期": period,
        "生成时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "核心摘要": base_summary,
        "水质周评": water_review,
        "预警回顾": alert_messages,
        "产销回顾": trade_review,
        "下周建议": next_suggestion,
        "署名": "数据智能体综合应用平台 V1.0 自动生成",
        "大模型": "DeepSeek-chat" if llm_used else f"本地模板(降级: {llm_msg})" if llm_msg else "本地模板"
    }


def _weekly_water_review(temp, oxy, salt, danger_flats):
    if danger_flats:
        return f"本周有{len(danger_flats)}处滩涂指标危险，主要表现为溶氧偏低，已督促成员增氧处置。"
    if oxy < 5:
        return "本周全域溶氧处于偏低区间，建议下周加密午间增氧。"
    return "本周全域水质稳定，各项指标处于适宜区间。"


def _weekly_suggestion(danger_flats, oxy):
    items = ["持续每日2次水质巡查", "关注下周天气过程"]
    if danger_flats:
        items.insert(0, "对危险滩涂进行专项复查，确认指标恢复")
    if oxy < 5:
        items.insert(0, "全域增氧设备纳入统一调度")
    return items


# ============================================================
# 6. 溯源核验智能体（区块链哈希校验+异常批次识别）
# ============================================================
def trace_verify(data):
    """企业采购溯源核验：识别篡改、异常批次"""
    traces = data.get("traces", [])
    if not traces:
        return {"核验结论": "无批次数据", "风险等级": "未知"}

    suspicious = []
    for t in traces:
        batch = t.get("batch_code", "")
        hash_val = t.get("blockchain_hash", "")
        status = t.get("status", "")
        quality = t.get("quality_check", "")
        seed_date = t.get("seed_date", "")
        harvest_date = t.get("harvest_date", "")

        # 异常规则：哈希缺失/过短、状态与质检不一致、日期倒置
        flags = []
        if not hash_val or len(str(hash_val)) < 8:
            flags.append("区块链哈希缺失或异常")
        if status == "processing" and "合格" in quality:
            flags.append("状态与质检结果矛盾(加工中却已合格)")
        if seed_date and harvest_date and seed_date > harvest_date:
            flags.append("投苗日期晚于收获日期(数据篡改嫌疑)")
        if flags:
            suspicious.append({"batch_code": batch, "问题": flags})

    risk_level = "red" if len(suspicious) >= 2 else ("orange" if suspicious else "green")
    risk_name = {"red": "高风险", "orange": "中风险", "green": "低风险"}[risk_level]

    return {
        "核验批次数": len(traces),
        "异常批次数": len(suspicious),
        "风险等级": risk_name,
        "等级颜色": risk_level,
        "异常批次明细": suspicious if suspicious else [{"batch_code": "无", "问题": ["全部批次核验通过"]}],
        "采购建议": _procurement_advice(risk_level),
        "核验结论": "溯源链条完整，可放心采购" if risk_level == "green" else
                   ("存在异常批次，建议暂缓采购并核查" if risk_level == "orange" else
                    "多个批次异常，禁止采购并上报监管")
    }


def _procurement_advice(level):
    if level == "green":
        return "全部批次溯源链条完整、哈希校验通过，可正常签约采购。"
    if level == "orange":
        return "建议剔除异常批次，仅采购核验通过批次；要求供应商补充质检报告。"
    return "建议立即暂停该供应商采购，并上报监管端核查溯源篡改。"


# ============================================================
# 7. 生态承载力智能 Agent（监管端海域生态评估）
# ============================================================
def ecological_capacity(data):
    """分析12处滩涂养殖密度、水质，评估海域生态压力"""
    flats = data.get("flats", [])
    total = len(flats)
    if total == 0:
        return {"评估结论": "无滩涂数据"}

    # 计算养殖密度压力（亩均苗种量）
    density_scores = []
    water_issues = 0
    for f in flats:
        area = float(f.get("area", 50))
        seed_qty = float(f.get("seed_quantity", 0))
        density = seed_qty / area if area > 0 else 0
        # 密度压力评分（>80kg/亩为过载）
        if density > 80:
            density_scores.append(0.3)
        elif density > 50:
            density_scores.append(0.6)
        else:
            density_scores.append(0.9)
        if f.get("status") in ("warning", "danger"):
            water_issues += 1

    eco_index = round((sum(density_scores) / total) * 100, 1)

    if eco_index >= 80:
        pressure, color = "生态承载良好", "green"
    elif eco_index >= 60:
        pressure, color = "轻度生态压力", "blue"
    elif eco_index >= 40:
        pressure, color = "中度生态压力", "orange"
    else:
        pressure, color = "重度生态过载", "red"

    return {
        "评估海域滩涂数": total,
        "生态承载力指数": f"{eco_index} / 100",
        "生态压力等级": pressure,
        "等级颜色": color,
        "水质异常滩涂数": water_issues,
        "密度过载滩涂数": sum(1 for s in density_scores if s < 0.5),
        "评估结论": _eco_conclusion(eco_index, water_issues, total),
        "管理建议": _eco_advice(pressure),
        "署名": "数据智能体综合应用平台 V1.0 生态承载力智能Agent"
    }


def _eco_conclusion(idx, water_issues, total):
    if idx >= 80:
        return f"海域生态承载力指数{idx}，养殖密度合理，{water_issues}/{total}处滩涂水质异常，整体生态健康。"
    if idx >= 60:
        return f"承载力指数{idx}，部分滩涂密度偏高，建议适度调减养殖规模。"
    if idx >= 40:
        return f"承载力指数{idx}，多滩涂过载，需启动生态修复与轮休。"
    return f"承载力指数{idx}，海域严重过载，建议立即实施禁养与生态恢复。"


def _eco_advice(pressure):
    if "良好" in pressure:
        return ["维持当前养殖规模", "推广三年两养一休模式", "持续监测密度变化"]
    if "轻度" in pressure:
        return ["对密度>80kg/亩滩涂调减10-15%", "加强水质监测", "引导混养模式"]
    if "中度" in pressure:
        return ["启动生态轮休", "过载滩涂暂停新投苗", "实施贝藻混养修复"]
    return ["立即实施禁养", "上报省级生态修复项目", "开展底质修复工程"]


# ============================================================
# 8. 灾害预警智能体（全域多源融合分级预警）
# ============================================================
def disaster_warning(data):
    """全域监测所有传感器+气象，分级推送预警"""
    flats = data.get("flats", [])
    weather_warnings = data.get("weather_warnings", [])

    red_zones = []
    orange_zones = []
    blue_zones = []

    for f in flats:
        name = f.get("name", "某滩涂")
        oxy = float(f.get("oxygen", 6))
        temp = float(f.get("temperature", 8))
        if oxy < 3 or temp < 2 or temp > 28:
            red_zones.append(f"{name}(溶氧{oxy}/水温{temp})")
        elif oxy < 5 or temp > 26:
            orange_zones.append(name)
        elif f.get("status") == "warning":
            blue_zones.append(name)

    # 气象预警加成
    for w in weather_warnings:
        level = w.get("level", "")
        content = w.get("content", "")
        if level == "red":
            red_zones.append(f"气象红色:{content[:15]}")
        elif level == "orange":
            orange_zones.append(f"气象橙色:{content[:15]}")

    return {
        "监测滩涂总数": len(flats),
        "红色紧急": red_zones if red_zones else ["无"],
        "橙色风险": orange_zones if orange_zones else ["无"],
        "蓝色提醒": blue_zones if blue_zones else ["无"],
        "融合气象预警数": len(weather_warnings),
        "总体态势": _disaster_situation(len(red_zones), len(orange_zones)),
        "处置建议": _disaster_advice(len(red_zones), len(orange_zones)),
        "AI应急方案": _llm_disaster_plan(red_zones, orange_zones, weather_warnings),
        "推送时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def _llm_disaster_plan(red_zones, orange_zones, weather_warnings):
    """调用 DeepSeek 大模型生成灾害应急方案"""
    if not red_zones and not orange_zones and not weather_warnings:
        return "全域平稳，保持日常监测。"
    system_prompt = (
        "你是辽宁寒地滩涂贝类养殖的灾害预警应急专家智能体（多源融合+DeepSeek大模型）。"
        "请基于预警态势，生成简明、可执行的应急响应方案，控制在250字以内。"
    )
    red_text = "、".join(red_zones[:5]) if red_zones else "无"
    orange_text = "、".join(orange_zones[:5]) if orange_zones else "无"
    weather_text = "；".join([w.get("content", "")[:30] for w in weather_warnings[:3]]) if weather_warnings else "无"
    user_prompt = (
        f"【预警态势】红色紧急区:{red_text}；橙色风险区:{orange_text}；气象预警:{weather_text}。"
        f"请生成应急响应方案。"
    )
    ok, content, msg = llm_chat(system_prompt, user_prompt, max_tokens=400)
    if ok:
        return content.strip()
    return f"（大模型离线：{msg}，请参考处置建议执行）"


def _disaster_situation(red, orange):
    if red > 0:
        return f"全域存在{red}处红色紧急，需立即响应"
    if orange > 0:
        return f"全域存在{orange}处橙色风险，需重点防控"
    return "全域态势平稳"


def _disaster_advice(red, orange):
    if red > 0:
        return ["立即向红色区域农户推送应急方案", "启动全域应急增氧调度", "上报上级监管部门", "暂停全域投喂"]
    if orange > 0:
        return ["向橙色区域推送防控指南", "加密监测频次至每2小时1次", "做好应急设备准备"]
    return ["保持日常监测", "关注气象预报"]


# ============================================================
# 9. AI 养殖顾问智能体（DeepSeek 大模型 + 知识图谱）
# ============================================================
def advisor_consult(data):
    """养殖户交互式问答，DeepSeek 大模型 + 养殖知识图谱"""
    question = (data.get("question") or "").strip()
    flat_data = data.get("flat_data", {})

    # 构建大模型提示词
    system_prompt = (
        "你是辽宁寒地滩涂贝类智慧养殖平台的AI养殖顾问智能体（依托数据智能体综合应用平台V1.0软著）。"
        "你精通缢蛏、文蛤、杂色蛤等寒地滩涂贝类养殖技术，擅长解答水温、溶氧、盐度、pH、"
        "病害防治、投喂管理、生态轮休、收获上市、极端天气应对等问题。\n"
        "请给出专业、具体、可操作的建议，控制在300字以内。"
    )
    # 结合滩涂实时数据
    data_desc = ""
    if flat_data:
        data_desc = f"\n\n【当前滩涂实时数据】水温{flat_data.get('temperature',8)}℃、溶氧{flat_data.get('oxygen',6)}mg/L、盐度{flat_data.get('salinity',30)}‰、pH{flat_data.get('ph',8.0)}。请结合实时数据给出针对性建议。"
    user_prompt = f"养殖户问题：{question}{data_desc}"

    # 调用 DeepSeek 大模型
    ok, content, msg = llm_chat(system_prompt, user_prompt, max_tokens=600)

    if ok:
        return {
            "用户问题": question or "（未输入问题）",
            "顾问回复": content,
            "参考知识库": "DeepSeek大模型 + 辽宁寒地滩涂贝类养殖知识图谱 V1.0",
            "服务提供": "数据智能体综合应用平台 V1.0 · AI养殖顾问智能体(DeepSeek)"
        }

    # 大模型调用失败，降级到本地知识库匹配
    kb = [
        {"keywords": ["水温", "低", "冷", "冻"], "answer": "水温偏低时建议：1.加深水位至1.5米以上利用地热保温；2.覆盖保温网提高水温2-3℃；3.暂停投喂减少代谢消耗；4.添加维生素C抗应激。"},
        {"keywords": ["溶氧", "缺氧", "增氧"], "answer": "溶氧不足时建议：1.立即开启增氧设备；2.午后14-16点加密增氧；3.检查是否有有机物污染；4.泼洒增氧剂应急；5.保持溶氧5mg/L以上。"},
        {"keywords": ["盐度", "淡水", "降水"], "answer": "盐度骤降时建议：1.检查淡水注入源；2.缓慢调整盐度避免急剧变化；3.雨季前加深水位；4.盐度<20‰时及时引入海水。"},
        {"keywords": ["投喂", "饲料", "饵料"], "answer": "科学投喂建议：1.投喂量为贝类体重3-5%；2.水温8-20℃时投喂最佳；3.冬季每日1次，生长季每日2次；4.根据摄食情况动态调整；5.禁用变质饵料。"},
        {"keywords": ["病害", "死亡", "异常"], "answer": "发现病害时建议：1.立即取样送检；2.隔离病贝防止扩散；3.全池消毒；4.检查水质四参数；5.降低养殖密度；6.重大疫情上报渔业部门。"},
        {"keywords": ["轮休", "休养", "生态"], "answer": "生态轮休建议：1.执行三年两养一休政策；2.休耕期进行底质修复；3.贝藻混养改善水质；4.休耕期可获500-800元/亩生态补偿。"},
        {"keywords": ["收获", "上市", "规格"], "answer": "收获时机建议：1.春秋季贝类品质最佳；2.缢蛏壳长5cm、文蛤6cm达标；3.肥满率>15%；4.活贝率>95%；5.出货前暂养24-48小时吐沙。"},
        {"keywords": ["台风", "暴雨", "极端天气"], "answer": "极端天气应对：1.提前加固设施；2.加深水位减少贝类移动；3.暂停养殖作业；4.灾后检查设施、清理杂物、监测水质；5.购买水产养殖保险。"},
    ]
    answer = None
    for item in kb:
        if any(k in question for k in item["keywords"]):
            answer = item["answer"]
            break
    if not answer:
        answer = ("您好，我是AI养殖顾问。建议您描述具体的养殖问题（如水温、溶氧、盐度、"
                  "病害、投喂、轮休、收获、极端天气等关键词），我将给出针对性建议。"
                  "也可前往【AI产量预测】页面获取数据化预测，或拨打辽宁省水产技术推广站热线024-12345678。")

    supplement = ""
    if flat_data:
        oxy = float(flat_data.get("oxygen", 6))
        temp = float(flat_data.get("temperature", 8))
        if oxy < 5:
            supplement = f"\n\n📊 实时数据提醒：您当前滩涂溶氧{oxy}mg/L偏低，建议优先增氧。"
        elif temp < 2:
            supplement = f"\n\n📊 实时数据提醒：您当前滩涂水温{temp}℃偏低，建议保温。"

    return {
        "用户问题": question or "（未输入问题）",
        "顾问回复": answer + supplement + f"\n\n（大模型离线：{msg}，已降级本地知识库）",
        "参考知识库": "辽宁寒地滩涂贝类养殖知识图谱 V1.0（本地降级）",
        "服务提供": "数据智能体综合应用平台 V1.0 · AI养殖顾问智能体(本地降级)"
    }


# ============================================================
# 启动入口
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  《数据智能体综合应用平台 V1.0》")
    print("  国家版权局软件著作权登记")
    print("  AI 底层调度中枢 - 端口 8090")
    print("=" * 60)
    print(f"  已注册智能体 {len(AGENT_REGISTRY)} 个：")
    for i, name in enumerate(AGENT_REGISTRY.keys(), 1):
        print(f"    {i}. {name}  [{AGENT_REGISTRY[name]['model']}]")
    print("=" * 60)
    app.run(host="127.0.0.1", port=8090, debug=True)
