"""
小程序专属路由 - 供微信小程序调用
"""
from flask import Blueprint, jsonify, request, render_template
from extensions import db
from models import (
    User, TidalFlat, WaterQualityData, AlertRecord,
    TraceabilityNode, DailyLog, WeatherWarning
)
from datetime import datetime, timedelta

mini_bp = Blueprint('mini_program', __name__)

@mini_bp.route('/')
def mini_index():
    """小程序入口页（可扫码跳转到小程序）"""
    return render_template('mini/index.html')

@mini_bp.route('/home')
def mini_home():
    """小程序首页数据"""
    farmer_id = request.args.get('farmer_id', type=int)
    
    if not farmer_id:
        return jsonify({'success': False, 'message': '缺少农户ID'})
    
    farmer = User.query.filter_by(id=farmer_id, role='farmer').first()
    if not farmer:
        return jsonify({'success': False, 'message': '农户不存在'})
    
    # 获取该农户的滩涂
    flats = TidalFlat.query.filter_by(farmer_id=farmer_id).all()
    
    # 获取最新预警
    alerts = AlertRecord.query.join(TidalFlat).filter(
        TidalFlat.farmer_id == farmer_id,
        AlertRecord.resolved == False
    ).order_by(AlertRecord.timestamp.desc()).limit(5).all()
    
    # 获取气象预警
    weather = WeatherWarning.query.filter(
        WeatherWarning.area == farmer.area
    ).order_by(WeatherWarning.forecast_date).limit(3).all()
    
    # 溯源统计
    trace_count = TraceabilityNode.query.filter_by(farmer_id=farmer_id).count()
    
    return jsonify({
        'success': True,
        'farmer': {
            'name': farmer.real_name,
            'area': farmer.area
        },
        'flats_count': len(flats),
        'alert_count': len(alerts),
        'trace_count': trace_count,
        'alerts': [{
            'id': a.id,
            'level': a.level,
            'level_name': a.level_info['name'],
            'message': a.message,
            'flat_name': a.flat.name if a.flat else '未知',
            'time': a.timestamp.strftime('%m-%d %H:%M')
        } for a in alerts],
        'weather': [{
            'type': w.warning_type,
            'level': w.level,
            'content': w.content,
            'date': w.forecast_date.strftime('%m-%d')
        } for w in weather]
    })

@mini_bp.route('/flats')
def mini_flats():
    """我的滩涂列表"""
    farmer_id = request.args.get('farmer_id', type=int)
    
    if not farmer_id:
        return jsonify({'success': False, 'message': '缺少农户ID'})
    
    flats = TidalFlat.query.filter_by(farmer_id=farmer_id).all()
    
    result = []
    for flat in flats:
        latest = WaterQualityData.query.filter_by(flat_id=flat.id)\
            .order_by(WaterQualityData.timestamp.desc()).first()
        
        alert = AlertRecord.query.filter_by(
            flat_id=flat.id,
            resolved=False
        ).order_by(AlertRecord.timestamp.desc()).first()
        
        result.append({
            'id': flat.id,
            'name': flat.name,
            'area': flat.area,
            'status': flat.status,
            'latest_water': {
                'temperature': latest.temperature if latest else None,
                'oxygen': latest.dissolved_oxygen if latest else None,
                'timestamp': latest.timestamp.strftime('%m-%d %H:%M') if latest else None
            } if latest else None,
            'alert': {
                'level': alert.level,
                'message': alert.message
            } if alert else None
        })
    
    return jsonify({'success': True, 'flats': result})

@mini_bp.route('/alerts')
def mini_alerts():
    """预警列表"""
    farmer_id = request.args.get('farmer_id', type=int)
    level = request.args.get('level')  # blue/orange/red
    
    if not farmer_id:
        return jsonify({'success': False, 'message': '缺少农户ID'})
    
    query = AlertRecord.query.join(TidalFlat).filter(
        TidalFlat.farmer_id == farmer_id
    )
    
    if level:
        query = query.filter(AlertRecord.level == level)
    
    alerts = query.order_by(AlertRecord.timestamp.desc()).limit(20).all()
    
    return jsonify({
        'success': True,
        'alerts': [{
            'id': a.id,
            'level': a.level,
            'level_name': a.level_info['name'],
            'level_color': a.level_info['color'],
            'flat_name': a.flat.name if a.flat else '未知',
            'message': a.message,
            'advice': a.advice,
            'resolved': a.resolved,
            'time': a.timestamp.strftime('%Y-%m-%d %H:%M')
        } for a in alerts]
    })

@mini_bp.route('/resolve-alert/<int:alert_id>', methods=['POST'])
def mini_resolve_alert(alert_id):
    """处理预警"""
    alert = AlertRecord.query.get_or_404(alert_id)
    
    alert.resolved = True
    alert.resolved_at = datetime.now()
    db.session.commit()
    
    return jsonify({'success': True, 'message': '预警已处理'})

@mini_bp.route('/log', methods=['GET', 'POST'])
def mini_log():
    """养殖台账"""
    if request.method == 'POST':
        farmer_id = request.form.get('farmer_id', type=int)
        flat_id = request.form.get('flat_id', type=int)
        log_date = request.form.get('log_date')
        work_type = request.form.get('work_type')
        content = request.form.get('content', '')
        
        if not farmer_id or not flat_id or not log_date or not work_type:
            return jsonify({'success': False, 'message': '请填写完整信息'})
        
        log = DailyLog(
            flat_id=flat_id,
            log_date=datetime.strptime(log_date, '%Y-%m-%d'),
            work_type=work_type,
            content=content,
            operator=User.query.get(farmer_id).real_name
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '台账已保存'})
    
    # 获取台账列表
    farmer_id = request.args.get('farmer_id', type=int)
    if not farmer_id:
        return jsonify({'success': False, 'message': '缺少农户ID'})
    
    flat_ids = [f.id for f in TidalFlat.query.filter_by(farmer_id=farmer_id).all()]
    
    logs = DailyLog.query.filter(
        DailyLog.flat_id.in_(flat_ids) if flat_ids else DailyLog.flat_id == -1
    ).order_by(DailyLog.log_date.desc()).limit(20).all()
    
    return jsonify({
        'success': True,
        'logs': [{
            'id': l.id,
            'date': l.log_date.strftime('%Y-%m-%d'),
            'work_type': l.work_type,
            'content': l.content,
            'flat_name': l.flat.name if l.flat else '未知'
        } for l in logs]
    })

@mini_bp.route('/generate-trace', methods=['POST'])
def mini_generate_trace():
    """小程序生成溯源码"""
    farmer_id = request.form.get('farmer_id', type=int)
    product_name = request.form.get('product_name', '')
    product_category = request.form.get('product_category', '')
    
    if not farmer_id or not product_name:
        return jsonify({'success': False, 'message': '请填写完整信息'})
    
    # 生成批次码
    import random
    batch_code = f"{product_category[:2].upper()}{datetime.now().strftime('%Y%m%d%H%M%S')}{farmer_id}{random.randint(100, 999)}"
    
    from routes.traceability import blockchain
    chain_data = {
        'batch_code': batch_code,
        'product': product_name,
        'farmer_id': farmer_id,
        'timestamp': datetime.now().isoformat()
    }
    blockchain.add_data(chain_data)
    block = blockchain.new_block()
    
    node = TraceabilityNode(
        batch_code=batch_code,
        product_name=product_name,
        product_category=product_category,
        farmer_id=farmer_id,
        blockchain_hash=block['hash'],
        status='processing'
    )
    db.session.add(node)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'batch_code': batch_code,
        'qr_code_url': f'/mini/qr/{batch_code}',
        'blockchain_hash': block['hash']
    })

@mini_bp.route('/qr/<string:batch_code>')
def mini_qr_code(batch_code):
    """展示二维码页面"""
    trace = TraceabilityNode.query.filter_by(batch_code=batch_code).first_or_404()
    return render_template('mini/qr.html', trace=trace)

@mini_bp.route('/knowledge')
def mini_knowledge():
    """农技知识库"""
    knowledge = [
        {
            'id': 1,
            'category': '冬季育苗',
            'title': '东北寒地贝类冬季育苗技术要点',
            'content': '1. 水温控制在5-8℃最适宜\n2. 饵料投喂量减少至夏季1/3\n3. 每周进行一次水质检测\n4. 发现病害及时隔离治疗'
        },
        {
            'id': 2,
            'category': '生态混养',
            'title': '贝类+海带生态混养模式',
            'content': '贝类滤食浮游生物，海带吸收营养盐，形成互利共生体系。建议贝类密度60kg/亩，海带间距30cm。'
        },
        {
            'id': 3,
            'category': '寒潮应对',
            'title': '寒潮来临前的五项准备',
            'content': '1. 检查保温设施\n2. 加深养殖水位\n3. 准备应急增氧设备\n4. 减少投喂量\n5. 关注气象预警'
        },
        {
            'id': 4,
            'category': '政策解读',
            'title': '辽宁省滩涂养殖"三年两养一休"政策',
            'content': '为保护海洋生态环境，实施三年两养一休制度。养殖期结束后需进行至少一年的生态修复，期间可申请政府补贴。'
        }
    ]
    
    return jsonify({'success': True, 'knowledge': knowledge})

@mini_bp.route('/market')
def mini_market():
    """产销信息"""
    from models import TransactionPost
    
    posts = TransactionPost.query.filter_by(status='open')\
        .order_by(TransactionPost.created_at.desc()).limit(20).all()
    
    return jsonify({
        'success': True,
        'posts': [{
            'id': p.id,
            'product_name': p.product_name,
            'category': p.product_category,
            'quantity': p.quantity,
            'price': p.expected_price,
            'listing_date': p.listing_date.strftime('%Y-%m-%d') if p.listing_date else None,
            'farmer_area': p.farmer.area if p.farmer else '未知'
        } for p in posts]
    })
