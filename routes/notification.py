"""
消息通知路由
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Notification, AlertRecord, TraceabilityNode, TransactionPost, PurchaseOrder
from extensions import db
from datetime import datetime

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/')
@login_required
def index():
    """消息通知中心首页"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()
    
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    # 按类型分组统计
    type_stats = {}
    for n in notifications:
        if n.type_name not in type_stats:
            type_stats[n.type_name] = 0
        type_stats[n.type_name] += 1
    
    return render_template('notification/index.html',
                         notifications=notifications,
                         unread_count=unread_count,
                         type_stats=type_stats)


@notification_bp.route('/list')
@login_required
def list_all():
    """全部通知列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    notify_type = request.args.get('type', '')
    is_read = request.args.get('status', '')
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if notify_type:
        query = query.filter_by(notify_type=notify_type)
    if is_read == 'read':
        query = query.filter_by(is_read=True)
    elif is_read == 'unread':
        query = query.filter_by(is_read=False)
    
    notifications = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page
    )
    
    return render_template('notification/list.html',
                         notifications=notifications,
                         notify_type=notify_type,
                         is_read=is_read)


@notification_bp.route('/<int:id>/read', methods=['POST'])
@login_required
def mark_as_read(id):
    """标记为已读"""
    notification = Notification.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()
    
    notification.is_read = True
    notification.save()
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    return redirect(url_for('notification.index'))


@notification_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """全部标记为已读"""
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    flash('已将所有消息标记为已读', 'success')
    return redirect(url_for('notification.index'))


@notification_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """删除通知"""
    notification = Notification.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()
    
    notification.delete()
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    flash('消息已删除', 'success')
    return redirect(url_for('notification.index'))


@notification_bp.route('/unread-count')
@login_required
def unread_count():
    """获取未读消息数量"""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    return jsonify({'count': count})


@notification_bp.route('/api/recent')
@login_required
def api_recent():
    """获取最近通知（JSON格式）"""
    limit = request.args.get('limit', 5, type=int)
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'id': n.id,
            'title': n.title,
            'content': n.content,
            'type': n.notify_type,
            'type_name': n.type_name,
            'level': n.level,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M') if n.created_at else ''
        } for n in notifications]
    })


def create_notification(user_id, title, content, notify_type='system', 
                       level='info', related_id=None, related_type=None):
    """创建通知的辅助函数"""
    notification = Notification(
        user_id=user_id,
        title=title,
        content=content,
        notify_type=notify_type,
        level=level,
        related_id=related_id,
        related_type=related_type
    )
    notification.save()
    return notification


def create_alert_notification(alert):
    """根据灾害预警创建通知"""
    from models import User
    users = User.query.filter(User.role.in_(['farmer', 'cooperative', 'regulator'])).all()
    for user in users:
        create_notification(
            user_id=user.id,
            title=f'【灾害预警】{alert.message[:30]}',
            content=alert.message,
            notify_type='alert',
            level=alert.level,
            related_id=alert.id,
            related_type='alert'
        )


def create_traceability_notification(trace):
    """溯源完成通知"""
    create_notification(
        user_id=trace.farmer_id,
        title=f'溯源码已生成：{trace.product_name}',
        content=f'批次号：{trace.batch_code}，已完成区块链上链',
        notify_type='trace',
        level='success',
        related_id=trace.id,
        related_type='traceability'
    )


def create_transaction_notification(order):
    """产销交易通知"""
    create_notification(
        user_id=order.enterprise_id,
        title=f'新的采购订单',
        content=f'订单已创建，请查看详情',
        notify_type='trade',
        level='info',
        related_id=order.id,
        related_type='purchase_order'
    )
