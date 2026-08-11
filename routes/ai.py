# -*- coding: utf-8 -*-
"""
============================================================
滩智溯 AI 路由蓝图
------------------------------------------------------------
本蓝图为滩智溯五端（农户/合作社/企业/监管/小程序）提供统一的
AI 智能体入口，所有请求经由 services/agent_client 转发至
《数据智能体综合应用平台 V1.0》(端口8090)。

⚠️ 知识产权声明：
  本文件仅做请求转发与数据组装，不做任何 AI 推理。
  人工智能推理功能依托《数据智能体综合应用平台 V1.0》
  软件著作权，主后端禁止内嵌大模型调用。
============================================================
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from services.agent_client import call_agent, is_agent_online
from models import (
    User, TidalFlat, WaterQualityData, AlertRecord,
    TraceabilityNode, SeedlingRecord, WeatherWarning, TransactionPost
)

ai_bp = Blueprint('ai', __name__)


# ============================================================
# 通用：状态探测（供前端展示软著平台在线状态）
# ============================================================
@ai_bp.route('/status')
def agent_status():
    """软著智能体平台在线状态"""
    online = is_agent_online()
    return jsonify({
        'success': True,
        'online': online,
        'platform': '数据智能体综合应用平台 V1.0',
        'message': 'AI智能体平台在线' if online else 'AI智能体平台未启动(8090端口)'
    })


# ============================================================
# 页面路由
# ============================================================
@ai_bp.route('/advisor')
@login_required
def advisor_page():
    """农户端 - AI养殖顾问页面"""
    if current_user.role != 'farmer':
        return render_template('errors/404.html'), 403
    # 获取农户滩涂及最新水质
    flats = TidalFlat.query.filter_by(farmer_id=current_user.id).all()
    flat_list = []
    for flat in flats:
        latest = WaterQualityData.query.filter_by(flat_id=flat.id)\
            .order_by(WaterQualityData.timestamp.desc()).first()
        flat_list.append({
            'id': flat.id,
            'name': flat.name,
            'temperature': latest.temperature if latest else None,
            'oxygen': latest.dissolved_oxygen if latest else None,
            'salinity': latest.salinity if latest else None,
            'ph': latest.ph if latest else None,
            'status': (latest.get_quality_status()['status'] if latest else 'normal')
        })
    agent_online = is_agent_online()
    return render_template('ai/advisor.html', flats=flat_list, agent_online=agent_online)


@ai_bp.route('/coop-ai')
@login_required
def coop_ai_page():
    """合作社端 - AI集群风险研判+周报页面"""
    if current_user.role != 'cooperative':
        return render_template('errors/404.html'), 403
    # 获取本合作社下辖全部滩涂的最新水质
    member_ids = [m.id for m in User.query.filter_by(role='farmer', area=current_user.area).all()]
    if member_ids:
        flats = TidalFlat.query.filter(TidalFlat.farmer_id.in_(member_ids)).all()
    else:
        flats = []
    flat_list = []
    for flat in flats:
        latest = WaterQualityData.query.filter_by(flat_id=flat.id)\
            .order_by(WaterQualityData.timestamp.desc()).first()
        flat_list.append({
            'id': flat.id, 'name': flat.name,
            'temperature': latest.temperature if latest else 0,
            'oxygen': latest.dissolved_oxygen if latest else 0,
            'salinity': latest.salinity if latest else 0,
            'ph': latest.ph if latest else 0,
            'status': (latest.get_quality_status()['status'] if latest else 'normal')
        })
    # 近7天预警
    week_ago = datetime.now() - timedelta(days=7)
    alerts = AlertRecord.query.filter(AlertRecord.timestamp >= week_ago).order_by(AlertRecord.timestamp.desc()).all()
    agent_online = is_agent_online()
    return render_template('ai/coop_ai.html', flats=flat_list,
                           alert_count=len(alerts), agent_online=agent_online)


@ai_bp.route('/trace-ai')
@login_required
def trace_ai_page():
    """企业端 - AI溯源核验页面"""
    if current_user.role != 'enterprise':
        return render_template('errors/404.html'), 403
    # 获取企业可核验的溯源批次
    traces = TraceabilityNode.query.filter_by(enterprise_id=current_user.id)\
        .order_by(TraceabilityNode.created_at.desc()).limit(50).all()
    # 若企业无关联批次，则取全部溯源批次供演示核验
    if not traces:
        traces = TraceabilityNode.query.order_by(TraceabilityNode.created_at.desc()).limit(50).all()
    agent_online = is_agent_online()
    return render_template('ai/trace_ai.html', traces=traces, agent_online=agent_online)


@ai_bp.route('/regulator-ai')
@login_required
def regulator_ai_page():
    """监管端 - AI生态评估+灾害预警页面"""
    if current_user.role != 'regulator':
        return render_template('errors/404.html'), 403
    # 全域滩涂及最新水质
    flats = TidalFlat.query.all()
    flat_list = []
    for flat in flats:
        latest = WaterQualityData.query.filter_by(flat_id=flat.id)\
            .order_by(WaterQualityData.timestamp.desc()).first()
        # 苗种投放量
        seedling_total = db_sum_seedling(flat.id)
        flat_list.append({
            'id': flat.id, 'name': flat.name, 'area': flat.area,
            'farmer': flat.owner.real_name if flat.owner else '未知',
            'temperature': latest.temperature if latest else 0,
            'oxygen': latest.dissolved_oxygen if latest else 0,
            'salinity': latest.salinity if latest else 0,
            'ph': latest.ph if latest else 0,
            'status': (latest.get_quality_status()['status'] if latest else 'normal'),
            'seed_quantity': seedling_total
        })
    # 当前生效气象预警
    weather_warnings = WeatherWarning.query.filter(
        WeatherWarning.forecast_date >= datetime.now().date()
    ).order_by(WeatherWarning.forecast_date).all()
    agent_online = is_agent_online()
    return render_template('ai/regulator_ai.html', flats=flat_list,
                           weather_warnings=weather_warnings, agent_online=agent_online)


def db_sum_seedling(flat_id):
    """统计滩涂累计苗种投放量"""
    from extensions import db
    from sqlalchemy import func
    result = db.session.query(func.sum(SeedlingRecord.quantity))\
        .filter_by(flat_id=flat_id).scalar()
    return float(result) if result else 0.0


# ============================================================
# API 路由：转发至软著智能体平台(8090)
# ============================================================

@ai_bp.route('/api/predict-output', methods=['POST'])
@login_required
def api_predict_output():
    """【农户端】AI产量预测 → 贝类产量预测智能体"""
    data = request.get_json(silent=True) or request.form.to_dict()
    flat_id = data.get('flat_id', type=int) if isinstance(data.get('flat_id'), int) else int(data.get('flat_id', 0))
    seed_quantity = float(data.get('seed_quantity', 100))
    days = int(data.get('days', 90))

    flat = TidalFlat.query.get(flat_id) if flat_id else None
    if not flat:
        return jsonify({'success': False, 'message': '滩涂不存在'})

    # 取近7天水质数据传入智能体
    week_ago = datetime.now() - timedelta(days=7)
    water_data = WaterQualityData.query.filter(
        WaterQualityData.flat_id == flat_id,
        WaterQualityData.timestamp >= week_ago
    ).order_by(WaterQualityData.timestamp.asc()).all()
    water_history = [{
        'temperature': w.temperature, 'salinity': w.salinity,
        'oxygen': w.dissolved_oxygen, 'ph': w.ph
    } for w in water_data]

    env_data = {
        'flat_name': flat.name, 'flat_area': flat.area,
        'seed_quantity': seed_quantity, 'days': days,
        'water_history': water_history
    }
    result = call_agent('贝类产量预测智能体', env_data)
    return jsonify(result)


@ai_bp.route('/api/water-risk', methods=['POST'])
@login_required
def api_water_risk():
    """【农户/小程序/监管】水质风险研判 → 水质风险研判智能体"""
    data = request.get_json(silent=True) or request.form.to_dict()
    flat_id = data.get('flat_id')
    try:
        flat_id = int(flat_id)
    except (TypeError, ValueError):
        flat_id = 0

    flat = TidalFlat.query.get(flat_id) if flat_id else None
    latest = WaterQualityData.query.filter_by(flat_id=flat_id)\
        .order_by(WaterQualityData.timestamp.desc()).first() if flat_id else None

    env_data = {
        'flat_name': flat.name if flat else '当前滩涂',
        'temperature': float(latest.temperature if latest and latest.temperature else data.get('temperature', 8)),
        'salinity': float(latest.salinity if latest and latest.salinity else data.get('salinity', 30)),
        'oxygen': float(latest.dissolved_oxygen if latest and latest.dissolved_oxygen else data.get('oxygen', 6)),
        'ph': float(latest.ph if latest and latest.ph else data.get('ph', 8.0)),
    }
    result = call_agent('水质风险研判智能体', env_data)
    return jsonify(result)


@ai_bp.route('/api/disease-detect', methods=['POST'])
def api_disease_detect():
    """【小程序】病害识别 → 贝类病害识别智能体（公开接口供小程序调用）"""
    data = request.get_json(silent=True) or request.form.to_dict()
    env_data = {
        'symptom': data.get('symptom', ''),
        'description': data.get('description', ''),
        'image_uploaded': data.get('image_uploaded', False)
    }
    result = call_agent('贝类病害识别智能体', env_data)
    return jsonify(result)


@ai_bp.route('/api/mini-water-risk', methods=['POST', 'GET'])
def api_mini_water_risk():
    """【小程序】水质风险研判公开接口（红色预警触发应急方案，免登录）"""
    if request.method == 'GET':
        data = request.args.to_dict()
    else:
        data = request.get_json(silent=True) or request.form.to_dict()
    env_data = {
        'flat_name': data.get('flat_name', '当前滩涂'),
        'temperature': float(data.get('temperature', 8)),
        'salinity': float(data.get('salinity', 30)),
        'oxygen': float(data.get('oxygen', 6)),
        'ph': float(data.get('ph', 8.0)),
    }
    result = call_agent('水质风险研判智能体', env_data)
    return jsonify(result)


@ai_bp.route('/api/advisor', methods=['POST'])
@login_required
def api_advisor():
    """【农户端】AI养殖顾问问答 → AI养殖顾问智能体"""
    data = request.get_json(silent=True) or request.form.to_dict()
    question = data.get('question', '')
    flat_id = data.get('flat_id')

    flat_data = {}
    try:
        flat_id = int(flat_id) if flat_id else None
    except (TypeError, ValueError):
        flat_id = None
    if flat_id:
        latest = WaterQualityData.query.filter_by(flat_id=flat_id)\
            .order_by(WaterQualityData.timestamp.desc()).first()
        if latest:
            flat_data = {
                'temperature': latest.temperature,
                'oxygen': latest.dissolved_oxygen,
                'salinity': latest.salinity,
                'ph': latest.ph
            }
    env_data = {'question': question, 'flat_data': flat_data}
    result = call_agent('AI养殖顾问智能体', env_data)
    return jsonify(result)


@ai_bp.route('/api/cluster-risk', methods=['POST'])
@login_required
def api_cluster_risk():
    """【合作社端】集群风险研判 → 集群风险研判智能体"""
    if current_user.role not in ('cooperative', 'regulator'):
        return jsonify({'success': False, 'message': '权限不足'}), 403
    flats_data = _collect_flats_data(current_user)
    result = call_agent('集群风险研判智能体', {'flats': flats_data})
    return jsonify(result)


@ai_bp.route('/api/weekly-report', methods=['POST'])
@login_required
def api_weekly_report():
    """【合作社端】AI周报 → AI养殖周报智能体"""
    if current_user.role != 'cooperative':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    flats_data = _collect_flats_data(current_user)
    week_ago = datetime.now() - timedelta(days=7)
    alerts = AlertRecord.query.filter(AlertRecord.timestamp >= week_ago).all()
    trades = TransactionPost.query.filter(TransactionPost.created_at >= week_ago).all()
    env_data = {
        'period': f"{datetime.now().year}年第{datetime.now().isocalendar()[1]}周",
        'flats': flats_data,
        'alerts': [{'message': a.message} for a in alerts],
        'trades': [{'id': t.id} for t in trades]
    }
    result = call_agent('AI养殖周报智能体', env_data)
    return jsonify(result)


@ai_bp.route('/api/trace-verify', methods=['POST'])
@login_required
def api_trace_verify():
    """【企业端】溯源核验 → 溯源核验智能体"""
    if current_user.role != 'enterprise':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    data = request.get_json(silent=True) or request.form.to_dict()
    # 支持指定批次核验 / 全量核验
    batch_codes = data.get('batch_codes', [])
    if batch_codes:
        traces = TraceabilityNode.query.filter(TraceabilityNode.batch_code.in_(batch_codes)).all()
    else:
        traces = TraceabilityNode.query.filter_by(enterprise_id=current_user.id).all()
        if not traces:
            traces = TraceabilityNode.query.limit(50).all()
    traces_data = [{
        'batch_code': t.batch_code,
        'blockchain_hash': t.blockchain_hash or '',
        'status': t.status,
        'quality_check': t.quality_check or '',
        'seed_date': t.seed_date.strftime('%Y-%m-%d') if t.seed_date else '',
        'harvest_date': t.harvest_date.strftime('%Y-%m-%d') if t.harvest_date else ''
    } for t in traces]
    result = call_agent('溯源核验智能体', {'traces': traces_data})
    return jsonify(result)


@ai_bp.route('/api/ecological', methods=['POST'])
@login_required
def api_ecological():
    """【监管端】生态承载力评估 → 生态承载力智能Agent"""
    if current_user.role != 'regulator':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    flats_data = _collect_flats_data(current_user, include_seedling=True)
    result = call_agent('生态承载力智能Agent', {'flats': flats_data})
    return jsonify(result)


@ai_bp.route('/api/disaster-warning', methods=['POST'])
@login_required
def api_disaster_warning():
    """【监管端】灾害预警 → 灾害预警智能体"""
    if current_user.role != 'regulator':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    flats_data = _collect_flats_data(current_user)
    weather_warnings = WeatherWarning.query.filter(
        WeatherWarning.forecast_date >= datetime.now().date()
    ).all()
    weather_data = [{
        'level': w.level, 'content': w.content,
        'area': w.area, 'type': w.warning_type
    } for w in weather_warnings]
    env_data = {'flats': flats_data, 'weather_warnings': weather_data}
    result = call_agent('灾害预警智能体', env_data)
    return jsonify(result)


# ============================================================
# 工具函数
# ============================================================
def _collect_flats_data(user, include_seedling=False):
    """收集当前用户权限范围内的滩涂最新水质数据"""
    if user.role == 'cooperative':
        member_ids = [m.id for m in User.query.filter_by(role='farmer', area=user.area).all()]
        if member_ids:
            flats = TidalFlat.query.filter(TidalFlat.farmer_id.in_(member_ids)).all()
        else:
            flats = []
    else:
        flats = TidalFlat.query.all()

    flats_data = []
    for flat in flats:
        latest = WaterQualityData.query.filter_by(flat_id=flat.id)\
            .order_by(WaterQualityData.timestamp.desc()).first()
        item = {
            'id': flat.id, 'name': flat.name, 'area': flat.area or 50,
            'temperature': latest.temperature if latest else 8,
            'oxygen': latest.dissolved_oxygen if latest else 6,
            'salinity': latest.salinity if latest else 30,
            'ph': latest.ph if latest else 8.0,
            'status': (latest.get_quality_status()['status'] if latest else 'normal')
        }
        if include_seedling:
            item['seed_quantity'] = db_sum_seedling(flat.id)
        flats_data.append(item)
    return flats_data
