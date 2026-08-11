"""
硬件设备管理路由
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import HardwareDevice, TidalFlat
from datetime import datetime, timedelta

hardware_bp = Blueprint('hardware', __name__)

@hardware_bp.route('/list')
@login_required
def device_list():
    """设备列表"""
    user = current_user
    
    if user.role == 'farmer':
        flat_ids = [f.id for f in TidalFlat.query.filter_by(farmer_id=user.id).all()]
    elif user.role == 'cooperative':
        from models import User as UserModel
        member_ids = [m.id for m in UserModel.query.filter_by(role='farmer', area=user.area).all()]
        flat_ids = [f.id for f in TidalFlat.query.filter(TidalFlat.farmer_id.in_(member_ids) if member_ids else TidalFlat.farmer_id == -1).all()]
    else:
        flat_ids = [f.id for f in TidalFlat.query.all()]
    
    devices = HardwareDevice.query.filter(
        HardwareDevice.flat_id.in_(flat_ids) if flat_ids else HardwareDevice.flat_id == -1
    ).order_by(HardwareDevice.device_id).all()
    
    # 统计
    total = len(devices)
    online = len([d for d in devices if d.status == 'online'])
    offline = len([d for d in devices if d.status == 'offline'])
    fault = len([d for d in devices if d.status == 'fault'])
    low_battery = len([d for d in devices if d.battery_level < 20])
    
    stats = {
        'total': total,
        'online': online,
        'offline': offline,
        'fault': fault,
        'low_battery': low_battery
    }
    
    return render_template('hardware/list.html', devices=devices, stats=stats)

@hardware_bp.route('/detail/<int:device_id>')
@login_required
def device_detail(device_id):
    """设备详情"""
    device = HardwareDevice.query.get_or_404(device_id)
    return render_template('hardware/detail.html', device=device)

@hardware_bp.route('/calibrate/<int:device_id>', methods=['POST'])
@login_required
def calibrate_device(device_id):
    """远程校准设备"""
    device = HardwareDevice.query.get_or_404(device_id)
    
    if device.status == 'offline':
        return jsonify({'success': False, 'message': '设备离线，无法下发指令'})
    
    # 模拟校准
    import random
    success = random.random() > 0.1  # 90%成功率
    
    if success:
        device.last_sync = datetime.now()
        device.firmware_version = 'v1.0.1'  # 模拟固件更新
        db.session.commit()
        return jsonify({'success': True, 'message': '校准指令已下发，设备已同步'})
    else:
        return jsonify({'success': False, 'message': '校准失败，请检查设备状态'})

@hardware_bp.route('/rental')
@login_required
def rental_list():
    """硬件租赁台账"""
    user = current_user
    
    if user.role == 'farmer':
        flat_ids = [f.id for f in TidalFlat.query.filter_by(farmer_id=user.id).all()]
    elif user.role == 'cooperative':
        from models import User as UserModel
        member_ids = [m.id for m in UserModel.query.filter_by(role='farmer', area=user.area).all()]
        flat_ids = [f.id for f in TidalFlat.query.filter(TidalFlat.farmer_id.in_(member_ids) if member_ids else TidalFlat.farmer_id == -1).all()]
    else:
        flat_ids = [f.id for f in TidalFlat.query.all()]
    
    devices = HardwareDevice.query.filter(
        HardwareDevice.flat_id.in_(flat_ids) if flat_ids else HardwareDevice.flat_id == -1
    ).filter(HardwareDevice.rental_start.isnot(None)).all()
    
    return render_template('hardware/rental.html', devices=devices)

@hardware_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_device():
    """添加新设备"""
    if request.method == 'POST':
        device_id = request.form.get('device_id', '').strip()
        model = request.form.get('model', 'LC-Sensor-A')
        flat_id = request.form.get('flat_id', type=int)
        
        if not device_id or not flat_id:
            return jsonify({'success': False, 'message': '请填写完整信息'})
        
        if HardwareDevice.query.filter_by(device_id=device_id).first():
            return jsonify({'success': False, 'message': '设备ID已存在'})
        
        device = HardwareDevice(
            device_id=device_id,
            model=model,
            flat_id=flat_id,
            status='online',
            battery_level=100,
            last_sync=datetime.now()
        )
        db.session.add(device)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '设备添加成功'})
    
    user = current_user
    if user.role == 'farmer':
        flats = TidalFlat.query.filter_by(farmer_id=user.id).all()
    else:
        flats = TidalFlat.query.all()
    
    return render_template('hardware/add.html', flats=flats)

@hardware_bp.route('/simulate', methods=['POST'])
@login_required
def simulate_data():
    """设备数据上传（基于和风天气实时数据推算水质）"""
    from models import WaterQualityData
    from services.qweather import get_water_quality_from_weather

    flat_id = request.form.get('flat_id', type=int)
    if not flat_id:
        return jsonify({'success': False, 'message': '缺少滩涂ID'})

    flat = TidalFlat.query.get(flat_id)
    if not flat:
        return jsonify({'success': False, 'message': '滩涂不存在'})

    # 基于实时天气推算水质
    if flat.latitude and flat.longitude:
        wq = get_water_quality_from_weather(flat.latitude, flat.longitude, flat_id)
    else:
        return jsonify({'success': False, 'message': '滩涂坐标缺失，无法推算水质'})

    data = WaterQualityData(
        flat_id=flat_id,
        timestamp=datetime.now(),
        temperature=wq['water_temperature'],
        salinity=wq['salinity'],
        dissolved_oxygen=wq['dissolved_oxygen'],
        ph=wq['ph']
    )
    db.session.add(data)
    db.session.commit()

    # 更新设备同步时间
    device = HardwareDevice.query.filter_by(flat_id=flat_id).first()
    if device:
        device.last_sync = datetime.now()
        db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'temperature': data.temperature,
            'salinity': data.salinity,
            'oxygen': data.dissolved_oxygen,
            'ph': data.ph
        },
        'source': 'qweather_realtime'
    })
