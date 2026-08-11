"""
区块链溯源路由
"""
from flask import Blueprint, render_template, jsonify, request, send_file, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import TraceabilityNode, TidalFlat, WaterQualityData, User
from datetime import datetime, timedelta
import hashlib
import os

trace_bp = Blueprint('traceability', __name__)

# 存储溯源链数据的简易区块链
class SimpleBlockchain:
    """简易区块链实现"""
    def __init__(self):
        self.chain = []
        self.current_data = []
    
    def new_block(self, previous_hash=None):
        block = {
            'index': len(self.chain),
            'data': self.current_data,
            'timestamp': datetime.now().isoformat(),
            'previous_hash': previous_hash or self.get_last_hash()
        }
        block['hash'] = self._hash(block)
        self.chain.append(block)
        self.current_data = []
        return block
    
    def add_data(self, data):
        self.current_data.append(data)
    
    def get_last_hash(self):
        if self.chain:
            return self.chain[-1]['hash']
        return '0' * 64
    
    def _hash(self, block):
        block_string = str(sorted(block.items()))
        return hashlib.sha256(block_string.encode()).hexdigest()

# 全局区块链实例
blockchain = SimpleBlockchain()

@trace_bp.route('/list')
@login_required
def trace_list():
    """溯源记录列表"""
    user = current_user
    
    if user.role == 'farmer':
        traces = TraceabilityNode.query.filter_by(farmer_id=user.id)\
            .order_by(TraceabilityNode.created_at.desc()).all()
    elif user.role == 'cooperative':
        from models import User as UserModel
        member_ids = [m.id for m in UserModel.query.filter_by(role='farmer', area=user.area).all()]
        traces = TraceabilityNode.query.filter(
            TraceabilityNode.farmer_id.in_(member_ids) if member_ids else TraceabilityNode.farmer_id == -1
        ).order_by(TraceabilityNode.created_at.desc()).all()
    elif user.role == 'enterprise':
        traces = TraceabilityNode.query.filter_by(status='completed')\
            .order_by(TraceabilityNode.created_at.desc()).all()
    else:
        traces = TraceabilityNode.query.order_by(TraceabilityNode.created_at.desc()).all()
    
    return render_template('traceability/list.html', traces=traces)

@trace_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_trace():
    """创建溯源记录"""
    if request.method == 'POST':
        product_name = request.form.get('product_name', '').strip()
        product_category = request.form.get('product_category', '').strip()
        seed_source = request.form.get('seed_source', '').strip()
        seed_date = request.form.get('seed_date')
        harvest_date = request.form.get('harvest_date')
        quality_check = request.form.get('quality_check', '合格')
        
        if not product_name or not product_category:
            return jsonify({'success': False, 'message': '请填写产品信息'})
        
        # 生成批次码
        batch_code = f"{product_category[:2].upper()}{datetime.now().strftime('%Y%m%d%H%M%S')}{current_user.id}"
        
        # 生成区块链哈希
        chain_data = {
            'batch_code': batch_code,
            'product': product_name,
            'farmer': current_user.real_name,
            'timestamp': datetime.now().isoformat()
        }
        blockchain.add_data(chain_data)
        block = blockchain.new_block()
        
        # 生成溯源节点
        node = TraceabilityNode(
            batch_code=batch_code,
            product_name=product_name,
            product_category=product_category,
            farmer_id=current_user.id,
            seed_source=seed_source,
            seed_date=datetime.strptime(seed_date, '%Y-%m-%d') if seed_date else None,
            harvest_date=datetime.strptime(harvest_date, '%Y-%m-%d') if harvest_date else None,
            quality_check=quality_check,
            blockchain_hash=block['hash'],
            status='processing'
        )
        db.session.add(node)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '溯源码生成成功',
            'batch_code': batch_code,
            'blockchain_hash': block['hash']
        })
    
    return render_template('traceability/create.html')

@trace_bp.route('/detail/<int:trace_id>')
@login_required
def trace_detail(trace_id):
    """溯源详情"""
    trace = TraceabilityNode.query.get_or_404(trace_id)
    
    # 获取关联的水质数据
    water_data = []
    if trace.seed_date and trace.harvest_date:
        flat = TidalFlat.query.filter_by(farmer_id=trace.farmer_id).first()
        if flat:
            water_data = WaterQualityData.query.filter(
                WaterQualityData.flat_id == flat.id,
                WaterQualityData.timestamp >= trace.seed_date,
                WaterQualityData.timestamp <= trace.harvest_date
            ).order_by(WaterQualityData.timestamp.desc()).limit(50).all()
    
    return render_template('traceability/detail.html', 
                         trace=trace, 
                         water_data=water_data)

@trace_bp.route('/verify/<string:batch_code>')
def verify_trace(batch_code):
    """公开展示溯源信息（消费者扫码查看）"""
    trace = TraceabilityNode.query.filter_by(batch_code=batch_code).first_or_404()
    
    # 获取农户信息
    farmer = User.query.get(trace.farmer_id) if trace.farmer_id else None
    
    # 获取水质数据
    water_data = []
    if trace.seed_date and trace.harvest_date:
        flat = TidalFlat.query.filter_by(farmer_id=trace.farmer_id).first()
        if flat:
            water_data = WaterQualityData.query.filter(
                WaterQualityData.flat_id == flat.id,
                WaterQualityData.timestamp >= trace.seed_date,
                WaterQualityData.timestamp <= trace.harvest_date
            ).order_by(WaterQualityData.timestamp.desc()).all()
    
    return render_template('traceability/verify.html',
                         trace=trace,
                         farmer=farmer,
                         water_data=water_data)

@trace_bp.route('/batch-verify', methods=['POST'])
@login_required
def batch_verify():
    """批量核验溯源码"""
    if current_user.role != 'enterprise':
        return jsonify({'success': False, 'message': '仅企业用户可使用批量核验'})
    
    batch_codes = request.form.get('batch_codes', '').strip()
    codes = [c.strip() for c in batch_codes.split('\n') if c.strip()]
    
    results = []
    for code in codes:
        trace = TraceabilityNode.query.filter_by(batch_code=code).first()
        if trace:
            results.append({
                'code': code,
                'valid': True,
                'product': trace.product_name,
                'status': trace.status_name,
                'farmer': trace.farmer.real_name if trace.farmer else '未知'
            })
        else:
            results.append({
                'code': code,
                'valid': False,
                'message': '溯源码不存在'
            })
    
    return jsonify({'success': True, 'results': results})

@trace_bp.route('/complete/<int:trace_id>', methods=['POST'])
@login_required
def complete_trace(trace_id):
    """完成溯源（企业加工环节）"""
    trace = TraceabilityNode.query.get_or_404(trace_id)
    
    if current_user.role != 'enterprise':
        return jsonify({'success': False, 'message': '仅企业用户可完成溯源'})
    
    trace.enterprise_id = current_user.id
    trace.processing_info = request.form.get('processing_info', '')
    trace.status = 'completed'
    trace.updated_at = datetime.now()
    db.session.commit()
    
    return jsonify({'success': True, 'message': '溯源流程已完成'})

@trace_bp.route('/export', methods=['POST'])
@login_required
def export_traces():
    """批量导出溯源码"""
    trace_ids = request.form.getlist('trace_ids')
    traces = TraceabilityNode.query.filter(TraceabilityNode.id.in_(trace_ids)).all()
    
    # 生成CSV内容
    csv_content = "\ufeff批次码,产品名称,品类,农户,投苗日期,捕捞日期,质检状态,区块链哈希\n"
    for t in traces:
        farmer_name = t.farmer.real_name if t.farmer else ''
        seed_date = t.seed_date.strftime('%Y-%m-%d') if t.seed_date else ''
        harvest_date = t.harvest_date.strftime('%Y-%m-%d') if t.harvest_date else ''
        csv_content += f"{t.batch_code},{t.product_name},{t.product_category},{farmer_name},{seed_date},{harvest_date},{t.quality_check},{t.blockchain_hash}\n"
    
    # 直接返回文件下载
    from flask import Response
    filename = f"trace_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_content,
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@trace_bp.route('/admin')
@login_required
def trace_admin():
    """溯源统一管理页面"""
    user = current_user
    if user.role not in ['cooperative', 'regulator', 'enterprise']:
        return redirect(url_for('dashboard.index'))
    
    # 获取筛选参数
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    farmer_id = request.args.get('farmer_id', type=int)
    keyword = request.args.get('keyword', '')
    
    # 构建查询
    query = TraceabilityNode.query
    
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(product_category=category)
    if farmer_id:
        query = query.filter_by(farmer_id=farmer_id)
    if keyword:
        query = query.filter(
            db.or_(
                TraceabilityNode.batch_code.contains(keyword),
                TraceabilityNode.product_name.contains(keyword),
                TraceabilityNode.quality_check.contains(keyword)
            )
        )
    
    traces = query.order_by(TraceabilityNode.created_at.desc()).all()
    
    # 获取统计数据
    total_count = TraceabilityNode.query.count()
    processing_count = TraceabilityNode.query.filter_by(status='processing').count()
    completed_count = TraceabilityNode.query.filter_by(status='completed').count()
    
    # 获取所有农户
    from models import User as UserModel
    farmers = UserModel.query.filter_by(role='farmer').all()
    
    # 获取所有品类
    categories = db.session.query(TraceabilityNode.product_category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    stats = {
        'total': total_count,
        'processing': processing_count,
        'completed': completed_count
    }
    
    return render_template('traceability/admin.html', 
                         traces=traces, 
                         farmers=farmers,
                         categories=categories,
                         stats=stats,
                         filters={'status': status, 'category': category, 'farmer_id': farmer_id, 'keyword': keyword})


@trace_bp.route('/admin/delete/<int:trace_id>', methods=['POST'])
@login_required
def admin_delete_trace(trace_id):
    """管理员删除溯源记录"""
    user = current_user
    if user.role not in ['cooperative', 'regulator']:
        return jsonify({'success': False, 'message': '无权限操作'})
    
    trace = TraceabilityNode.query.get_or_404(trace_id)
    db.session.delete(trace)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '已删除'})


@trace_bp.route('/admin/batch-delete', methods=['POST'])
@login_required
def admin_batch_delete():
    """批量删除溯源记录"""
    user = current_user
    if user.role not in ['cooperative', 'regulator']:
        return jsonify({'success': False, 'message': '无权限操作'})
    
    trace_ids = request.form.getlist('trace_ids')
    TraceabilityNode.query.filter(TraceabilityNode.id.in_(trace_ids)).delete()
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'已删除 {len(trace_ids)} 条记录'})


@trace_bp.route('/admin/batch-complete', methods=['POST'])
@login_required
def admin_batch_complete():
    """批量完成溯源"""
    user = current_user
    if user.role != 'enterprise':
        return jsonify({'success': False, 'message': '仅企业用户可完成溯源'})
    
    trace_ids = request.form.getlist('trace_ids')
    now = datetime.now()
    for trace_id in trace_ids:
        trace = TraceabilityNode.query.get(int(trace_id))
        if trace and trace.status == 'processing':
            trace.status = 'completed'
            trace.enterprise_id = user.id
            trace.updated_at = now
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'已完成 {len(trace_ids)} 条溯源'})


@trace_bp.route('/api/stats')
@login_required
def trace_api_stats():
    """溯源统计API"""
    from sqlalchemy import func
    
    # 按品类统计
    category_stats = db.session.query(
        TraceabilityNode.product_category,
        func.count(TraceabilityNode.id)
    ).group_by(TraceabilityNode.product_category).all()
    
    # 按状态统计
    status_stats = db.session.query(
        TraceabilityNode.status,
        func.count(TraceabilityNode.id)
    ).group_by(TraceabilityNode.status).all()
    
    return jsonify({
        'success': True,
        'category_stats': [{'category': c[0], 'count': c[1]} for c in category_stats],
        'status_stats': [{'status': s[0], 'count': s[1]} for s in status_stats]
    })
