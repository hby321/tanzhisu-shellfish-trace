"""
灾害预警路由
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import AlertRecord, TidalFlat, WaterQualityData, WeatherWarning
from datetime import datetime, timedelta
from services.qweather import (
    has_api_key, get_all_coastal_weather, get_all_coastal_warnings,
    get_mock_weather, get_mock_warnings, LIAONING_COASTAL_CITIES
)
import random

alert_bp = Blueprint('alert', __name__)

@alert_bp.route('/list')
@login_required
def alert_list():
    """预警列表"""
    user = current_user
    
    if user.role == 'farmer':
        flat_ids = [f.id for f in TidalFlat.query.filter_by(farmer_id=user.id).all()]
    elif user.role == 'cooperative':
        from models import User as UserModel
        member_ids = [m.id for m in UserModel.query.filter_by(role='farmer', area=user.area).all()]
        flat_ids = [f.id for f in TidalFlat.query.filter(TidalFlat.farmer_id.in_(member_ids) if member_ids else TidalFlat.farmer_id == -1).all()]
    else:
        flat_ids = [f.id for f in TidalFlat.query.all()]
    
    alerts = AlertRecord.query.filter(
        AlertRecord.flat_id.in_(flat_ids) if flat_ids else AlertRecord.flat_id == -1
    ).order_by(AlertRecord.timestamp.desc()).all()
    
    return render_template('alert/list.html', alerts=alerts)

@alert_bp.route('/detail/<int:alert_id>')
@login_required
def alert_detail(alert_id):
    """预警详情"""
    alert = AlertRecord.query.get_or_404(alert_id)
    return render_template('alert/detail.html', alert=alert)

@alert_bp.route('/handle/<int:alert_id>', methods=['POST'])
@login_required
def handle_alert(alert_id):
    """处理预警"""
    alert = AlertRecord.query.get_or_404(alert_id)
    action = request.form.get('action')
    
    if action == 'resolve':
        alert.resolved = True
        alert.resolved_at = datetime.now()
        db.session.commit()
        return jsonify({'success': True, 'message': '预警已处理'})
    
    return jsonify({'success': False, 'message': '无效操作'})

@alert_bp.route('/check')
@login_required
def check_alerts():
    """检查并生成预警（模拟实时监测）"""
    # 遍历所有滩涂的最新水质数据，检查是否需要生成预警
    flats = TidalFlat.query.all()
    new_alerts = []
    
    for flat in flats:
        latest = WaterQualityData.query.filter_by(flat_id=flat.id)\
            .order_by(WaterQualityData.timestamp.desc()).first()
        
        if not latest:
            continue
        
        status = latest.get_quality_status()
        
        if status['status'] == 'danger':
            # 检查是否已有未解决的同类预警
            existing = AlertRecord.query.filter_by(
                flat_id=flat.id,
                resolved=False,
                level='red'
            ).first()
            
            if not existing:
                alert = AlertRecord(
                    flat_id=flat.id,
                    level='red',
                    alert_type='other',
                    message=f'水质危险：{", ".join(status["issues"])}',
                    advice='立即采取应急措施：增加增氧设备，检查水源交换，联系水产专家'
                )
                db.session.add(alert)
                new_alerts.append(alert)
                
        elif status['status'] == 'warning':
            existing = AlertRecord.query.filter_by(
                flat_id=flat.id,
                resolved=False,
                level='orange'
            ).first()
            
            if not existing:
                alert = AlertRecord(
                    flat_id=flat.id,
                    level='orange',
                    alert_type='other',
                    message=f'水质异常：{", ".join(status["issues"])}',
                    advice='密切关注水质变化，准备应对措施'
                )
                db.session.add(alert)
                new_alerts.append(alert)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'new_alerts': len(new_alerts),
        'alerts': [{
            'flat': a.flat.name if a.flat else '未知',
            'level': a.level_info['name'],
            'message': a.message
        } for a in new_alerts]
    })

@alert_bp.route('/history')
@login_required
def alert_history():
    """预警历史档案"""
    user = current_user
    
    if user.role == 'farmer':
        flat_ids = [f.id for f in TidalFlat.query.filter_by(farmer_id=user.id).all()]
    else:
        flat_ids = [f.id for f in TidalFlat.query.all()]
    
    # 按月统计
    months = []
    now = datetime.now()
    for i in range(12):
        month_start = now.replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        
        month_alerts = AlertRecord.query.filter(
            AlertRecord.flat_id.in_(flat_ids) if flat_ids else AlertRecord.flat_id == -1,
            AlertRecord.timestamp >= month_start,
            AlertRecord.timestamp < month_end
        ).all()
        
        # 统计受灾时长（假设每个预警平均持续2小时）
        disaster_hours = len([a for a in month_alerts if a.level == 'red']) * 2
        
        months.append({
            'month': month_start.strftime('%Y-%m'),
            'total': len(month_alerts),
            'red_count': len([a for a in month_alerts if a.level == 'red']),
            'orange_count': len([a for a in month_alerts if a.level == 'orange']),
            'blue_count': len([a for a in month_alerts if a.level == 'blue']),
            'disaster_hours': disaster_hours
        })
    
    months.reverse()
    
    return render_template('alert/history.html', months=months)

@alert_bp.route('/weather')
@login_required
def weather_warnings():
    """气象预警 - 集成和风天气实时数据"""
    api_ready = has_api_key()

    if api_ready:
        # 获取和风天气实时预警
        realtime_warnings = get_all_coastal_warnings()
        # 获取辽宁沿海实时天气
        coastal_weather = get_all_coastal_weather()
        # 数据来源标记
        data_source = '和风天气实时数据'
    else:
        # 未配置API Key
        realtime_warnings = []
        coastal_weather = []
        data_source = '未配置和风天气API Key，请联系管理员'

    # 同时获取数据库中的历史预警记录
    db_warnings = WeatherWarning.query.order_by(WeatherWarning.created_at.desc()).limit(20).all()

    return render_template('alert/weather.html',
                           realtime_warnings=realtime_warnings,
                           coastal_weather=coastal_weather,
                           db_warnings=db_warnings,
                           api_ready=api_ready,
                           data_source=data_source,
                           coastal_cities=LIAONING_COASTAL_CITIES)


@alert_bp.route('/weather/refresh')
@login_required
def weather_refresh():
    """手动刷新天气数据"""
    from services.qweather import _cache
    _cache.clear()
    return jsonify({'success': True, 'message': '天气数据缓存已刷新'})


@alert_bp.route('/weather/realtime')
@login_required
def weather_realtime():
    """辽宁沿海实时天气API"""
    api_ready = has_api_key()

    if api_ready:
        weather_list = get_all_coastal_weather()
        warnings = get_all_coastal_warnings()
        return jsonify({
            'success': True,
            'source': 'qweather',
            'weather': weather_list,
            'warnings': warnings,
            'warning_count': len(warnings),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    else:
        return jsonify({
            'success': False,
            'source': 'none',
            'message': '未配置和风天气API Key',
            'weather': [],
            'warnings': [],
            'warning_count': 0,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
