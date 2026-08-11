"""
水质可视化路由
支持真实天气数据驱动的实时水质推算
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import TidalFlat, WaterQualityData, HardwareDevice
from datetime import datetime, timedelta
from sqlalchemy import func
from services.qweather import (
    get_weather_now, get_water_quality_from_weather,
    weather_to_water_quality, LIAONING_COASTAL_CITIES
)

water_bp = Blueprint('water_quality', __name__)

@water_bp.route('/quality-trend-page/<int:flat_id>')
@login_required
def quality_trend_page(flat_id):
    """水质趋势图页面（含实时天气推算水质）"""
    flat = TidalFlat.query.get_or_404(flat_id)
    
    # 获取最新水质数据
    latest = WaterQualityData.query.filter_by(flat_id=flat_id)\
        .order_by(WaterQualityData.timestamp.desc()).first()
    
    # 尝试获取实时天气推算的水质
    realtime_wq = None
    if flat.latitude and flat.longitude:
        realtime_wq = get_water_quality_from_weather(flat.latitude, flat.longitude, flat_id)
    
    return render_template('water_quality/trend.html',
                         flat=flat,
                         latest_data=latest,
                         realtime_wq=realtime_wq)

@water_bp.route('/quality-map')
@login_required
def quality_map():
    """全域水质热力地图（含实时天气推算水质）"""
    flats = TidalFlat.query.filter_by(farmer_id=current_user.id).all() if current_user.role == 'farmer' else TidalFlat.query.all()
    
    # 获取每个滩涂最新的水质数据 + 实时天气推算水质
    flat_data = []
    for flat in flats:
        latest = WaterQualityData.query.filter_by(flat_id=flat.id)\
            .order_by(WaterQualityData.timestamp.desc()).first()
        
        # 获取实时天气推算水质
        realtime_wq = None
        if flat.latitude and flat.longitude:
            realtime_wq = get_water_quality_from_weather(flat.latitude, flat.longitude, flat.id)
        
        flat_data.append({
            'id': flat.id,
            'name': flat.name,
            'latitude': flat.latitude,
            'longitude': flat.longitude,
            'area': flat.area,
            'status': flat.status,
            'farmer_id': flat.farmer_id,
            'water_data': {
                'temperature': latest.temperature if latest else None,
                'salinity': latest.salinity if latest else None,
                'oxygen': latest.dissolved_oxygen if latest else None,
                'ph': latest.ph if latest else None,
                'timestamp': latest.timestamp.strftime('%Y-%m-%d %H:%M') if latest else None
            } if latest else None,
            'realtime_wq': realtime_wq
        })
    
    return render_template('water_quality/map.html', 
                         flat_data=flat_data,
                         user_role=current_user.role)

@water_bp.route('/quality-trend/<int:flat_id>')
@login_required
def quality_trend(flat_id):
    """单滩涂水质趋势图（含实时天气推算数据点）"""
    flat = TidalFlat.query.get_or_404(flat_id)
    
    # 获取时间范围参数
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    # 获取历史数据
    data = WaterQualityData.query.filter(
        WaterQualityData.flat_id == flat_id,
        WaterQualityData.timestamp >= start_date
    ).order_by(WaterQualityData.timestamp.asc()).all()
    
    # 获取实时天气推算水质作为最新数据点
    realtime_point = None
    if flat.latitude and flat.longitude:
        wq = get_water_quality_from_weather(flat.latitude, flat.longitude, flat_id)
        if wq:
            realtime_point = {
                'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M'),
                'temperature': wq['water_temperature'],
                'salinity': wq['salinity'],
                'oxygen': wq['dissolved_oxygen'],
                'ph': wq['ph']
            }
    
    # 准备图表数据（使用ISO 8601格式，JS可解析）
    chart_data = {
        'dates': [d.timestamp.strftime('%Y-%m-%dT%H:%M') for d in data],
        'temperature': [d.temperature for d in data],
        'salinity': [d.salinity for d in data],
        'oxygen': [d.dissolved_oxygen for d in data],
        'ph': [d.ph for d in data]
    }
    
    # 在末尾添加实时数据点
    if realtime_point:
        chart_data['dates'].append(realtime_point['timestamp'])
        chart_data['temperature'].append(realtime_point['temperature'])
        chart_data['salinity'].append(realtime_point['salinity'])
        chart_data['oxygen'].append(realtime_point['oxygen'])
        chart_data['ph'].append(realtime_point['ph'])
    
    return jsonify({
        'success': True,
        'flat_name': flat.name,
        'chart_data': chart_data,
        'realtime_data': realtime_point
    })

@water_bp.route('/quality-stats')
@login_required
def quality_stats():
    """水质统计数据（含实时天气推算值）"""
    user = current_user
    
    if user.role == 'farmer':
        flat_ids = [f.id for f in TidalFlat.query.filter_by(farmer_id=user.id).all()]
    else:
        flat_ids = [f.id for f in TidalFlat.query.all()]
    
    # 最近7天数据统计
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    stats = db.session.query(
        func.avg(WaterQualityData.temperature),
        func.avg(WaterQualityData.salinity),
        func.avg(WaterQualityData.dissolved_oxygen),
        func.avg(WaterQualityData.ph)
    ).filter(
        WaterQualityData.flat_id.in_(flat_ids) if flat_ids else WaterQualityData.flat_id == -1,
        WaterQualityData.timestamp >= seven_days_ago
    ).first()
    
    # 尝试获取实时天气推算的当前水质
    realtime_wq = None
    if flat_ids:
        flat = TidalFlat.query.get(flat_ids[0])
        if flat and flat.latitude and flat.longitude:
            realtime_wq = get_water_quality_from_weather(flat.latitude, flat.longitude, flat.id)
    
    return jsonify({
        'success': True,
        'avg_temperature': round(stats[0], 2) if stats[0] else 0,
        'avg_salinity': round(stats[1], 2) if stats[1] else 0,
        'avg_oxygen': round(stats[2], 2) if stats[2] else 0,
        'avg_ph': round(stats[3], 2) if stats[3] else 0,
        'realtime_wq': realtime_wq
    })

@water_bp.route('/quality-data')
@login_required
def quality_data():
    """水质数据详情页面（含实时天气推算水质）"""
    user = current_user
    
    if user.role == 'farmer':
        flats = TidalFlat.query.filter_by(farmer_id=user.id).all()
    else:
        flats = TidalFlat.query.all()
    
    flat_id = request.args.get('flat_id', type=int)
    selected_flat = TidalFlat.query.get(flat_id) if flat_id else (flats[0] if flats else None)
    
    quality_records = []
    realtime_wq = None
    if selected_flat:
        quality_records = WaterQualityData.query.filter_by(flat_id=selected_flat.id)\
            .order_by(WaterQualityData.timestamp.desc()).limit(100).all()
        # 获取实时天气推算水质
        if selected_flat.latitude and selected_flat.longitude:
            realtime_wq = get_water_quality_from_weather(selected_flat.latitude, selected_flat.longitude, selected_flat.id)
    
    return render_template('water_quality/data.html',
                         flats=flats,
                         selected_flat=selected_flat,
                         quality_records=quality_records,
                         realtime_wq=realtime_wq)


@water_bp.route('/realtime-quality')
@login_required
def realtime_quality():
    """
    API: 获取实时天气推算的水质数据
    GET /water_quality/realtime-quality?flat_id=1
    """
    flat_id = request.args.get('flat_id', type=int)
    if not flat_id:
        return jsonify({'success': False, 'message': '缺少滩涂ID'}), 400
    
    flat = TidalFlat.query.get(flat_id)
    if not flat:
        return jsonify({'success': False, 'message': '滩涂不存在'}), 404
    
    if not flat.latitude or not flat.longitude:
        return jsonify({'success': False, 'message': '滩涂坐标缺失'}), 400
    
    # 获取实时天气
    weather = get_weather_now(flat.latitude, flat.longitude)
    
    # 推算水质
    wq = weather_to_water_quality(weather, flat_id)
    
    # 查询历史最新数据
    latest = WaterQualityData.query.filter_by(flat_id=flat_id)\
        .order_by(WaterQualityData.timestamp.desc()).first()
    
    return jsonify({
        'success': True,
        'flat_id': flat_id,
        'flat_name': flat.name,
        'realtime_weather': weather,
        'derived_water_quality': wq,
        'historical_latest': {
            'temperature': latest.temperature,
            'salinity': latest.salinity,
            'oxygen': latest.dissolved_oxygen,
            'ph': latest.ph,
            'timestamp': latest.timestamp.strftime('%Y-%m-%d %H:%M')
        } if latest else None,
        'data_source': 'qweather_real_time'
    })
