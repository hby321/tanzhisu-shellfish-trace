"""
企业专属路由
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import (
    User, TraceabilityNode, TransactionPost, PurchaseOrder,
    TidalFlat, RevenueRecord
)
from datetime import datetime, timedelta

enterprise_bp = Blueprint('enterprise', __name__)

@enterprise_bp.route('/trace-verify')
@login_required
def trace_verify():
    """溯源核验页面"""
    if current_user.role != 'enterprise':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    return render_template('enterprise/trace_verify.html')

@enterprise_bp.route('/contracts')
@login_required
def my_contracts():
    """我的采购合同"""
    if current_user.role != 'enterprise':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    orders = PurchaseOrder.query.filter_by(enterprise_id=current_user.id)\
        .order_by(PurchaseOrder.created_at.desc()).all()
    
    # 按状态分组
    pending = [o for o in orders if o.status == 'pending']
    confirmed = [o for o in orders if o.status == 'confirmed']
    completed = [o for o in orders if o.status == 'completed']
    
    return render_template('enterprise/contracts.html',
                         pending=pending,
                         confirmed=confirmed,
                         completed=completed)

@enterprise_bp.route('/sign-contract/<int:order_id>', methods=['POST'])
@login_required
def sign_contract(order_id):
    """签约确认"""
    if current_user.role != 'enterprise':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    order = PurchaseOrder.query.get_or_404(order_id)
    
    if order.enterprise_id != current_user.id:
        return jsonify({'success': False, 'message': '无权操作'}), 403
    
    status = request.form.get('status', 'confirmed')
    order.status = status
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'订单已更新为{status}'})

@enterprise_bp.route('/new-purchase', methods=['GET', 'POST'])
@login_required
def new_purchase():
    """新建采购订单"""
    if current_user.role != 'enterprise':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    if request.method == 'POST':
        post_id = request.form.get('post_id', type=int)
        agreed_price = request.form.get('agreed_price', type=float)
        quantity = request.form.get('quantity', type=float)
        
        if not post_id or not agreed_price or not quantity:
            return jsonify({'success': False, 'message': '请填写完整信息'})
        
        order = PurchaseOrder(
            post_id=post_id,
            enterprise_id=current_user.id,
            agreed_price=agreed_price,
            quantity=quantity,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '采购订单已创建'})
    
    # 获取市场信息
    posts = TransactionPost.query.filter_by(status='open')\
        .order_by(TransactionPost.created_at.desc()).all()
    
    return render_template('enterprise/new_purchase.html', posts=posts)

@enterprise_bp.route('/brand-management')
@login_required
def brand_management():
    """品牌溯源管理"""
    if current_user.role != 'enterprise':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 获取本企业完成的溯源记录
    traces = TraceabilityNode.query.filter_by(
        enterprise_id=current_user.id,
        status='completed'
    ).order_by(TraceabilityNode.updated_at.desc()).all()
    
    # 产品溢价统计
    product_stats = {}
    for trace in traces:
        product = trace.product_name
        if product not in product_stats:
            product_stats[product] = {'count': 0, 'total': 0}
        product_stats[product]['count'] += 1
        product_stats[product]['total'] += 1
    
    return render_template('enterprise/brand.html', 
                         traces=traces, 
                         product_stats=product_stats)

@enterprise_bp.route('/purchase-report')
@login_required
def purchase_report():
    """采购数据分析报表"""
    if current_user.role != 'enterprise':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    orders = PurchaseOrder.query.filter_by(enterprise_id=current_user.id).all()
    
    # 月度统计
    monthly_data = {}
    for order in orders:
        month = order.created_at.strftime('%Y-%m')
        if month not in monthly_data:
            monthly_data[month] = {'count': 0, 'total_value': 0, 'total_qty': 0}
        
        if order.status in ['confirmed', 'completed']:
            monthly_data[month]['count'] += 1
            monthly_data[month]['total_value'] += order.agreed_price * order.quantity
            monthly_data[month]['total_qty'] += order.quantity
    
    # 产地分布
    origin_dist = {}
    for order in orders:
        post = TransactionPost.query.get(order.post_id) if order.post_id else None
        if post and post.farmer:
            area = post.farmer.area or '未知'
            if area not in origin_dist:
                origin_dist[area] = 0
            if order.status in ['confirmed', 'completed']:
                origin_dist[area] += order.quantity
    
    return render_template('enterprise/report.html',
                         monthly_data=monthly_data,
                         origin_distribution=origin_dist)
