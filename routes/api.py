"""
API接口路由 - 供小程序和前端AJAX调用
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import (
    User, TidalFlat, HardwareDevice, WaterQualityData,
    AlertRecord, TraceabilityNode, WeatherWarning, RevenueRecord
)
from datetime import datetime, timedelta
from services.qweather import has_api_key, get_all_coastal_weather, get_all_coastal_warnings, get_mock_weather, LIAONING_COASTAL_CITIES

api_bp = Blueprint('api', __name__)

@api_bp.route('/water-quality/<int:flat_id>')
def get_water_quality(flat_id):
    """获取滩涂水质数据"""
    hours = request.args.get('hours', 24, type=int)
    start_time = datetime.now() - timedelta(hours=hours)
    
    data = WaterQualityData.query.filter(
        WaterQualityData.flat_id == flat_id,
        WaterQualityData.timestamp >= start_time
    ).order_by(WaterQualityData.timestamp.desc()).all()
    
    return jsonify({
        'success': True,
        'flat_id': flat_id,
        'data': [{
            'timestamp': d.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': d.temperature,
            'salinity': d.salinity,
            'oxygen': d.dissolved_oxygen,
            'ph': d.ph
        } for d in data]
    })

@api_bp.route('/latest-water')
def get_latest_water():
    """获取所有滩涂最新水质"""
    flats = TidalFlat.query.all()
    result = []
    
    for flat in flats:
        latest = WaterQualityData.query.filter_by(flat_id=flat.id)\
            .order_by(WaterQualityData.timestamp.desc()).first()
        if latest:
            status = latest.get_quality_status()
            result.append({
                'flat_id': flat.id,
                'flat_name': flat.name,
                'temperature': latest.temperature,
                'oxygen': latest.dissolved_oxygen,
                'salinity': latest.salinity,
                'ph': latest.ph,
                'status': status['status'],
                'issues': status['issues'],
                'timestamp': latest.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
    
    return jsonify({'success': True, 'data': result})

@api_bp.route('/alerts')
def get_alerts():
    """获取预警列表"""
    resolved = request.args.get('resolved', type=bool)
    
    query = AlertRecord.query
    if resolved is not None:
        query = query.filter_by(resolved=resolved)
    
    alerts = query.order_by(AlertRecord.timestamp.desc()).limit(50).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'id': a.id,
            'level': a.level,
            'level_name': a.level_info['name'],
            'level_color': a.level_info['color'],
            'flat_name': a.flat.name if a.flat else '未知',
            'message': a.message,
            'advice': a.advice,
            'resolved': a.resolved,
            'timestamp': a.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for a in alerts]
    })

@api_bp.route('/devices/status')
def get_devices_status():
    """获取设备状态"""
    status = request.args.get('status')
    
    query = HardwareDevice.query
    if status:
        query = query.filter_by(status=status)
    
    devices = query.all()
    
    return jsonify({
        'success': True,
        'total': len(devices),
        'devices': [{
            'device_id': d.device_id,
            'model': d.model,
            'flat_name': d.flat.name if d.flat else '未知',
            'status': d.status,
            'battery': d.battery_level,
            'last_sync': d.last_sync.strftime('%Y-%m-%d %H:%M:%S') if d.last_sync else None
        } for d in devices]
    })

@api_bp.route('/trace/<string:batch_code>')
def get_traceability(batch_code):
    """获取溯源详情（公开接口）"""
    trace = TraceabilityNode.query.filter_by(batch_code=batch_code).first()
    
    if not trace:
        return jsonify({'success': False, 'message': '溯源码不存在'}), 404
    
    farmer = User.query.get(trace.farmer_id) if trace.farmer_id else None
    enterprise = User.query.get(trace.enterprise_id) if trace.enterprise_id else None
    
    return jsonify({
        'success': True,
        'data': {
            'batch_code': trace.batch_code,
            'product_name': trace.product_name,
            'product_category': trace.product_category,
            'status': trace.status_name,
            'farmer': farmer.real_name if farmer else '未知',
            'farmer_area': farmer.area if farmer else '未知',
            'seed_source': trace.seed_source,
            'seed_date': trace.seed_date.strftime('%Y-%m-%d') if trace.seed_date else None,
            'harvest_date': trace.harvest_date.strftime('%Y-%m-%d') if trace.harvest_date else None,
            'quality_check': trace.quality_check,
            'enterprise': enterprise.real_name if enterprise else None,
            'processing_info': trace.processing_info,
            'blockchain_hash': trace.blockchain_hash,
            'created_at': trace.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@api_bp.route('/weather')
def get_weather_warnings():
    """获取气象预警（数据库历史记录）"""
    warnings = WeatherWarning.query.filter(
        WeatherWarning.forecast_date >= datetime.now().date()
    ).order_by(WeatherWarning.forecast_date).all()

    return jsonify({
        'success': True,
        'data': [{
            'id': w.id,
            'type': w.warning_type,
            'type_name': {
                'cold': '寒潮预警',
                'gale': '大风预警',
                'snow': '暴雪预警'
            }.get(w.warning_type, '其他'),
            'level': w.level,
            'area': w.area,
            'content': w.content,
            'forecast_date': w.forecast_date.strftime('%Y-%m-%d')
        } for w in warnings]
    })


@api_bp.route('/weather/realtime')
def get_realtime_weather():
    """获取辽宁沿海实时天气和预警（和风天气API）"""
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

@api_bp.route('/stats/overview')
def get_overview_stats():
    """获取全域概览统计"""
    total_flats = TidalFlat.query.count()
    normal_flats = TidalFlat.query.filter_by(status='normal').count()
    warning_flats = TidalFlat.query.filter_by(status='warning').count()
    total_devices = HardwareDevice.query.count()
    online_devices = HardwareDevice.query.filter_by(status='online').count()
    total_alerts = AlertRecord.query.count()
    unresolved_alerts = AlertRecord.query.filter_by(resolved=False).count()
    total_traces = TraceabilityNode.query.count()
    
    return jsonify({
        'success': True,
        'data': {
            'total_flats': total_flats,
            'normal_flats': normal_flats,
            'warning_flats': warning_flats,
            'total_devices': total_devices,
            'online_devices': online_devices,
            'device_online_rate': round(online_devices / max(total_devices, 1) * 100, 1),
            'total_alerts': total_alerts,
            'unresolved_alerts': unresolved_alerts,
            'alert_resolution_rate': round((total_alerts - unresolved_alerts) / max(total_alerts, 1) * 100, 1),
            'total_traces': total_traces
        }
    })

@api_bp.route('/simulate/upload', methods=['POST'])
def simulate_device_upload():
    """设备数据上传（基于和风天气实时数据推算水质）"""
    from models import WaterQualityData, TidalFlat
    from services.qweather import get_water_quality_from_weather

    data = request.get_json(silent=True)
    if not data:
        data = request.form

    flat_id = data.get('flat_id') or request.form.get('flat_id', type=int)
    if not flat_id:
        return jsonify({'success': False, 'message': '缺少滩涂ID'})

    flat = TidalFlat.query.get(flat_id)
    if not flat:
        return jsonify({'success': False, 'message': '滩涂不存在'})

    # 如果提供了完整数据则直接使用，否则用天气推算
    if data.get('temperature') and data.get('salinity') and data.get('oxygen') and data.get('ph'):
        temp = data.get('temperature')
        salinity = data.get('salinity')
        oxygen = data.get('oxygen')
        ph = data.get('ph')
        source = 'manual'
    else:
        # 基于实时天气推算水质
        if flat.latitude and flat.longitude:
            wq = get_water_quality_from_weather(flat.latitude, flat.longitude, flat_id)
            temp = wq['water_temperature']
            salinity = wq['salinity']
            oxygen = wq['dissolved_oxygen']
            ph = wq['ph']
            source = 'qweather_realtime'
        else:
            return jsonify({'success': False, 'message': '滩涂坐标缺失，无法推算水质'})

    new_data = WaterQualityData(
        flat_id=int(flat_id),
        temperature=float(temp),
        salinity=float(salinity),
        dissolved_oxygen=float(oxygen),
        ph=float(ph)
    )
    db.session.add(new_data)
    db.session.commit()

    # 检查是否需要生成预警
    status = new_data.get_quality_status()
    if status['status'] == 'danger':
        alert = AlertRecord(
            flat_id=int(flat_id),
            level='red',
            alert_type='other',
            message=f'水质危险：{", ".join(status["issues"])}',
            advice='立即采取应急措施'
        )
        db.session.add(alert)
        db.session.commit()

    return jsonify({
        'success': True,
        'source': source,
        'data': {
            'id': new_data.id,
            'temperature': new_data.temperature,
            'salinity': new_data.salinity,
            'oxygen': new_data.dissolved_oxygen,
            'ph': new_data.ph,
            'status': status['status'],
            'issues': status['issues']
        }
    })

@api_bp.route('/water-quality')
def get_all_water_quality():
    """获取所有滩涂最新水质聚合接口"""
    flats = TidalFlat.query.all()
    result = []
    for flat in flats:
        latest = WaterQualityData.query.filter_by(flat_id=flat.id)\
            .order_by(WaterQualityData.timestamp.desc()).first()
        if latest:
            status = latest.get_quality_status()
            result.append({
                'flat_id': flat.id,
                'flat_name': flat.name,
                'area': flat.area,
                'temperature': latest.temperature,
                'oxygen': latest.dissolved_oxygen,
                'salinity': latest.salinity,
                'ph': latest.ph,
                'status': status['status'],
                'issues': status['issues'],
                'timestamp': latest.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
    return jsonify({'success': True, 'data': result, 'total': len(result)})

@api_bp.route('/devices')
def get_all_devices():
    """获取所有设备列表"""
    status = request.args.get('status')
    query = HardwareDevice.query
    if status:
        query = query.filter_by(status=status)
    devices = query.all()
    return jsonify({
        'success': True,
        'total': len(devices),
        'devices': [{
            'id': d.id,
            'device_id': d.device_id,
            'model': d.model,
            'flat_id': d.flat_id,
            'flat_name': d.flat.name if d.flat else '未知',
            'status': d.status,
            'battery': d.battery_level,
            'last_sync': d.last_sync.strftime('%Y-%m-%d %H:%M:%S') if d.last_sync else None
        } for d in devices]
    })

@api_bp.route('/trace/list')
def get_trace_list():
    """获取溯源码列表"""
    farmer_id = request.args.get('farmer_id', type=int)
    status = request.args.get('status')
    query = TraceabilityNode.query
    if farmer_id:
        query = query.filter_by(farmer_id=farmer_id)
    if status:
        query = query.filter_by(status=status)
    traces = query.order_by(TraceabilityNode.created_at.desc()).limit(100).all()
    return jsonify({
        'success': True,
        'total': len(traces),
        'data': [{
            'id': t.id,
            'batch_code': t.batch_code,
            'product_name': t.product_name,
            'product_category': t.product_category,
            'status': t.status_name,
            'farmer_id': t.farmer_id,
            'blockchain_hash': t.blockchain_hash,
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for t in traces]
    })

@api_bp.route('/farmer/login', methods=['POST'])
def farmer_login():
    """农户登录接口（小程序用）"""
    data = request.get_json(silent=True)
    if not data:
        data = request.form
    
    username = data.get('username', '')
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '请输入用户名和密码'})
    
    user = User.query.filter_by(username=username, role='farmer').first()
    
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': '用户名或密码错误'})
    
    if not user.is_active:
        return jsonify({'success': False, 'message': '账号已被禁用'})
    
    return jsonify({
        'success': True,
        'token': f'farmer_token_{user.id}',
        'user': {
            'id': user.id,
            'username': user.username,
            'name': user.real_name,
            'phone': user.phone,
            'area': user.area
        }
    })
