"""
合作社管理员路由
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import (
    User, TidalFlat, HardwareDevice, TraceabilityNode,
    TransactionPost, PurchaseOrder, RevenueRecord, AlertRecord
)
from datetime import datetime, timedelta
from sqlalchemy import func

coop_bp = Blueprint('cooperative', __name__)

@coop_bp.route('/members')
@login_required
def members():
    """社员管理"""
    if current_user.role != 'cooperative':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    members = User.query.filter_by(role='farmer', area=current_user.area).all()
    
    member_stats = []
    for member in members:
        flats_count = TidalFlat.query.filter_by(farmer_id=member.id).count()
        alerts_count = AlertRecord.query.join(TidalFlat).filter(
            TidalFlat.farmer_id == member.id,
            AlertRecord.resolved == False
        ).count()
        traces_count = TraceabilityNode.query.filter_by(farmer_id=member.id).count()
        
        member_stats.append({
            'member': member,
            'flats_count': flats_count,
            'alerts_count': alerts_count,
            'traces_count': traces_count
        })
    
    return render_template('cooperative/members.html', 
                         members=member_stats,
                         total_members=len(members))

@coop_bp.route('/unified-trace')
@login_required
def unified_trace():
    """统一溯源管理（批量生成溯源码）"""
    if current_user.role != 'cooperative':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 获取所有社员的溯源记录
    member_ids = [m.id for m in User.query.filter_by(role='farmer', area=current_user.area).all()]
    traces = TraceabilityNode.query.filter(
        TraceabilityNode.farmer_id.in_(member_ids) if member_ids else TraceabilityNode.farmer_id == -1
    ).order_by(TraceabilityNode.created_at.desc()).all()
    
    return render_template('cooperative/unified_trace.html', traces=traces)

@coop_bp.route('/batch-trace', methods=['POST'])
@login_required
def batch_create_trace():
    """批量创建溯源码"""
    if current_user.role != 'cooperative':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    product_name = request.form.get('product_name', '').strip()
    product_category = request.form.get('product_category', '').strip()
    farmer_ids = request.form.getlist('farmer_ids')
    seed_source = request.form.get('seed_source', '')
    quality_check = request.form.get('quality_check', '合格')
    
    if not product_name or not farmer_ids:
        return jsonify({'success': False, 'message': '请填写完整信息'})
    
    from routes.traceability import blockchain
    created_count = 0
    
    for farmer_id in farmer_ids:
        batch_code = f"{product_category[:2].upper()}{datetime.now().strftime('%Y%m%d%H%M%S')}{farmer_id}{created_count}"
        
        chain_data = {
            'batch_code': batch_code,
            'product': product_name,
            'farmer_id': farmer_id,
            'operator': current_user.real_name,
            'timestamp': datetime.now().isoformat()
        }
        blockchain.add_data(chain_data)
        block = blockchain.new_block()
        
        node = TraceabilityNode(
            batch_code=batch_code,
            product_name=product_name,
            product_category=product_category,
            farmer_id=int(farmer_id),
            seed_source=seed_source,
            quality_check=quality_check,
            blockchain_hash=block['hash'],
            status='processing'
        )
        db.session.add(node)
        created_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'成功创建 {created_count} 个溯源码',
        'count': created_count
    })

@coop_bp.route('/enterprise-contracts')
@login_required
def enterprise_contracts():
    """企业对接管理"""
    if current_user.role != 'cooperative':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 获取所有采购订单
    area_members = User.query.filter_by(role='farmer', area=current_user.area).all() if current_user.area else []
    area_member_ids = [m.id for m in area_members]
    orders = PurchaseOrder.query.join(TransactionPost).filter(
        TransactionPost.farmer_id.in_(area_member_ids) if area_member_ids else TransactionPost.farmer_id == -1
    ).order_by(PurchaseOrder.created_at.desc()).all()
    
    return render_template('cooperative/contracts.html', orders=orders)

@coop_bp.route('/area-stats')
@login_required
def area_stats():
    """区域数据统计"""
    if current_user.role != 'cooperative':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    member_ids = [m.id for m in User.query.filter_by(role='farmer', area=current_user.area).all()]
    
    # 滩涂统计
    total_flats = TidalFlat.query.filter(
        TidalFlat.farmer_id.in_(member_ids) if member_ids else TidalFlat.farmer_id == -1
    ).count()
    total_area = db.session.query(func.sum(TidalFlat.area)).filter(
        TidalFlat.farmer_id.in_(member_ids) if member_ids else TidalFlat.farmer_id == -1
    ).scalar() or 0
    
    # 设备统计
    total_devices = HardwareDevice.query.filter(
        HardwareDevice.flat_id.in_(
            [f.id for f in TidalFlat.query.filter(TidalFlat.farmer_id.in_(member_ids) if member_ids else TidalFlat.farmer_id == -1).all()]
        )
    ).count()
    
    # 溯源统计
    trace_count = TraceabilityNode.query.filter(
        TraceabilityNode.farmer_id.in_(member_ids) if member_ids else TraceabilityNode.farmer_id == -1
    ).count()
    
    # 预警统计
    alert_count = AlertRecord.query.join(TidalFlat).filter(
        TidalFlat.farmer_id.in_(member_ids) if member_ids else TidalFlat.farmer_id == -1
    ).count()
    
    unresolved_alerts = AlertRecord.query.join(TidalFlat).filter(
        TidalFlat.farmer_id.in_(member_ids) if member_ids else TidalFlat.farmer_id == -1,
        AlertRecord.resolved == False
    ).count()
    
    # 营收统计
    current_year = datetime.now().year
    revenue_total = db.session.query(func.sum(RevenueRecord.sales_revenue)).filter(
        RevenueRecord.farmer_id.in_(member_ids) if member_ids else RevenueRecord.farmer_id == -1,
        RevenueRecord.year == current_year
    ).scalar() or 0
    
    return jsonify({
        'success': True,
        'stats': {
            'total_members': len(member_ids),
            'total_flats': total_flats,
            'total_area': total_area,
            'total_devices': total_devices,
            'trace_count': trace_count,
            'alert_count': alert_count,
            'unresolved_alerts': unresolved_alerts,
            'annual_revenue': revenue_total
        }
    })
