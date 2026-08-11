"""
仪表板路由 - 登录后首页
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import (
    TidalFlat, HardwareDevice, WaterQualityData, 
    AlertRecord, TraceabilityNode, User,
    SeedlingRecord, DailyLog, PredictionRecord, KnowledgeArticle
)
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """主仪表板"""
    user = current_user
    role = user.role
    
    # 根据角色获取不同的仪表板数据
    if role == 'farmer':
        # 农户仪表板
        flats = TidalFlat.query.filter_by(farmer_id=user.id).all()
        flat_ids = [f.id for f in flats]
        
        # 今日预警
        today_alerts = AlertRecord.query.filter(
            AlertRecord.flat_id.in_(flat_ids) if flat_ids else AlertRecord.flat_id == -1,
            AlertRecord.resolved == False
        ).count()
        
        # 设备状态
        online_devices = HardwareDevice.query.filter(
            HardwareDevice.flat_id.in_(flat_ids) if flat_ids else HardwareDevice.flat_id == -1,
            HardwareDevice.status == 'online'
        ).count()
        
        # 溯源记录
        trace_count = TraceabilityNode.query.filter_by(farmer_id=user.id).count()
        
        # 最新水质
        latest_quality = []
        for flat in flats:
            latest = WaterQualityData.query.filter_by(flat_id=flat.id)\
                .order_by(WaterQualityData.timestamp.desc()).first()
            if latest:
                status = latest.get_quality_status()
                latest_quality.append({
                    'flat_name': flat.name,
                    'temperature': latest.temperature,
                    'oxygen': latest.dissolved_oxygen,
                    'status': status['status']
                })
        
        stats = {
            'flat_count': len(flats),
            'alert_count': today_alerts,
            'device_online': online_devices,
            'trace_count': trace_count,
            'latest_quality': latest_quality
        }
        
        # 新增统计
        seed_count = SeedlingRecord.query.filter(
            SeedlingRecord.flat_id.in_(flat_ids) if flat_ids else SeedlingRecord.flat_id == -1
        ).count()
        log_count = DailyLog.query.filter(
            DailyLog.flat_id.in_(flat_ids) if flat_ids else DailyLog.flat_id == -1
        ).count()
        predict_count = PredictionRecord.query.filter_by(user_id=user.id).count()
        
        stats['seed_count'] = seed_count
        stats['log_count'] = log_count
        stats['predict_count'] = predict_count
        stats['knowledge_count'] = KnowledgeArticle.query.count()
        
        # 近期活动
        recent_logs = DailyLog.query.filter(
            DailyLog.flat_id.in_(flat_ids) if flat_ids else DailyLog.flat_id == -1
        ).order_by(DailyLog.created_at.desc()).limit(5).all()
        recent_traces = TraceabilityNode.query.filter_by(farmer_id=user.id)\
            .order_by(TraceabilityNode.created_at.desc()).limit(3).all()
        
        stats['recent_logs'] = recent_logs
        stats['recent_traces'] = recent_traces
        
        return render_template('dashboard/farmer_dashboard.html', stats=stats)
    
    elif role == 'cooperative':
        # 合作社仪表板
        # 获取所有社员
        members = User.query.filter_by(role='farmer', area=user.area).all()
        member_ids = [m.id for m in members]
        
        # 所有滩涂
        all_flats = TidalFlat.query.filter(TidalFlat.farmer_id.in_(member_ids) if member_ids else TidalFlat.farmer_id == -1).all()
        flat_ids = [f.id for f in all_flats]
        
        # 预警统计
        total_alerts = AlertRecord.query.filter(
            AlertRecord.flat_id.in_(flat_ids) if flat_ids else AlertRecord.flat_id == -1
        ).count()
        
        unresolved_alerts = AlertRecord.query.filter(
            AlertRecord.flat_id.in_(flat_ids) if flat_ids else AlertRecord.flat_id == -1,
            AlertRecord.resolved == False
        ).count()
        
        # 设备统计
        total_devices = HardwareDevice.query.filter(
            HardwareDevice.flat_id.in_(flat_ids) if flat_ids else HardwareDevice.flat_id == -1
        ).count()
        online_devices = HardwareDevice.query.filter(
            HardwareDevice.flat_id.in_(flat_ids) if flat_ids else HardwareDevice.flat_id == -1,
            HardwareDevice.status == 'online'
        ).count()
        
        # 溯源记录
        trace_count = TraceabilityNode.query.filter(
            TraceabilityNode.farmer_id.in_(member_ids) if member_ids else TraceabilityNode.farmer_id == -1
        ).count()
        
        stats = {
            'member_count': len(members),
            'flat_count': len(all_flats),
            'total_alerts': total_alerts,
            'unresolved_alerts': unresolved_alerts,
            'total_devices': total_devices,
            'online_devices': online_devices,
            'trace_count': trace_count
        }
        return render_template('dashboard/cooperative_dashboard.html', stats=stats)
    
    elif role == 'enterprise':
        # 企业仪表板
        # 溯源核验统计（当前企业用户的溯源记录）
        trace_count = TraceabilityNode.query.filter_by(enterprise_id=user.id).count()
        
        # 近期采购
        from models import PurchaseOrder
        recent_orders = PurchaseOrder.query.filter_by(enterprise_id=user.id)\
            .order_by(PurchaseOrder.created_at.desc()).limit(5).all()
        
        # 产品统计（当前企业用户的溯源产品）
        products = db.session.query(
            TraceabilityNode.product_name,
            func.count(TraceabilityNode.id).label('count')
        ).filter(
            TraceabilityNode.enterprise_id == user.id
        ).group_by(TraceabilityNode.product_name).all()
        
        # 近30天采购金额
        thirty_days_ago = datetime.now() - timedelta(days=30)
        monthly_total = db.session.query(
            func.coalesce(func.sum(PurchaseOrder.agreed_price * PurchaseOrder.quantity), 0)
        ).filter(
            PurchaseOrder.enterprise_id == user.id,
            PurchaseOrder.status.in_(['confirmed', 'completed']),
            PurchaseOrder.created_at >= thirty_days_ago
        ).scalar() or 0
        
        # 订单总数
        order_count = PurchaseOrder.query.filter_by(enterprise_id=user.id).count()
        
        # 合作产品数（当前企业用户的不同产品名数量）
        product_count = len(set(TraceabilityNode.query.filter_by(enterprise_id=user.id).with_entities(TraceabilityNode.product_name).distinct().all()))
        
        stats = {
            'trace_total': trace_count,
            'recent_orders': recent_orders,
            'product_stats': products,
            'monthly_total': monthly_total,
            'order_count': order_count,
            'product_count': product_count,
            'now': datetime.now()
        }
        return render_template('dashboard/enterprise_dashboard.html', stats=stats)
    
    elif role == 'regulator':
        # 监管仪表板 - 全域数据
        # 滩涂统计
        total_flats = TidalFlat.query.count()
        normal_flats = TidalFlat.query.filter_by(status='normal').count()
        warning_flats = TidalFlat.query.filter_by(status='warning').count()
        
        # 预警统计
        today = datetime.now().date()
        today_alerts = AlertRecord.query.filter(
            func.date(AlertRecord.timestamp) == today
        ).count()
        
        unresolved_alerts = AlertRecord.query.filter_by(resolved=False).count()
        
        # 禁养区监测
        forbidden_flats = TidalFlat.query.filter_by(is_fishing_allowed=False).count()
        
        # 设备统计
        total_devices = HardwareDevice.query.count()
        offline_devices = HardwareDevice.query.filter_by(status='offline').count()
        
        stats = {
            'total_flats': total_flats,
            'normal_flats': normal_flats,
            'warning_flats': warning_flats,
            'today_alerts': today_alerts,
            'unresolved_alerts': unresolved_alerts,
            'forbidden_flats': forbidden_flats,
            'total_devices': total_devices,
            'offline_devices': offline_devices
        }
        return render_template('dashboard/regulator_dashboard.html', stats=stats)
    
    return render_template('dashboard/index.html')

@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """获取统计数据API"""
    user = current_user
    data = {
        'user_role': user.role,
        'user_name': user.real_name
    }
    return jsonify(data)
