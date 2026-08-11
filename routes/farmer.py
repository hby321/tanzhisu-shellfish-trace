"""
农户专属路由
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import (
    TidalFlat, DailyLog, SeedlingRecord, TransactionPost,
    RevenueRecord, EcologicalPlan, WeatherWarning, AlertRecord,
    KnowledgeArticle
)
from datetime import datetime, timedelta

farmer_bp = Blueprint('farmer', __name__)

@farmer_bp.route('/flats')
@login_required
def my_flats():
    """我的滩涂列表"""
    flats = TidalFlat.query.filter_by(farmer_id=current_user.id).all()
    
    flat_details = []
    for flat in flats:
        # 获取最新预警
        alert = AlertRecord.query.filter_by(
            flat_id=flat.id, 
            resolved=False
        ).order_by(AlertRecord.timestamp.desc()).first()
        
        # 获取生态规划
        current_year = datetime.now().year
        plan = EcologicalPlan.query.filter_by(
            flat_id=flat.id,
            plan_year=current_year
        ).first()
        
        flat_details.append({
            'flat': flat,
            'active_alert': alert,
            'ecological_plan': plan
        })
    
    return render_template('farmer/flats.html', flat_details=flat_details)

@farmer_bp.route('/log', methods=['GET', 'POST'])
@login_required
def daily_log():
    """电子养殖台账"""
    user = current_user
    flats = TidalFlat.query.filter_by(farmer_id=user.id).all()
    
    if request.method == 'POST':
        flat_id = request.form.get('flat_id', type=int)
        log_date = request.form.get('log_date')
        work_type = request.form.get('work_type')
        content = request.form.get('content', '').strip()
        operator = request.form.get('operator', user.real_name)
        
        if not flat_id or not log_date or not work_type:
            return jsonify({'success': False, 'message': '请填写完整信息'})
        
        log = DailyLog(
            flat_id=flat_id,
            log_date=datetime.strptime(log_date, '%Y-%m-%d'),
            work_type=work_type,
            content=content,
            operator=operator
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '台账已保存'})
    
    # 获取历史台账
    logs = DailyLog.query.filter(
        DailyLog.flat_id.in_([f.id for f in flats])
    ).order_by(DailyLog.log_date.desc()).limit(100).all()
    
    return render_template('farmer/log.html', flats=flats, logs=logs)

@farmer_bp.route('/seedling', methods=['GET', 'POST'])
@login_required
def seedling_record():
    """苗种投放记录"""
    user = current_user
    flats = TidalFlat.query.filter_by(farmer_id=user.id).all()
    
    if request.method == 'POST':
        flat_id = request.form.get('flat_id', type=int)
        species = request.form.get('species', '').strip()
        quantity = request.form.get('quantity', type=float)
        source = request.form.get('source', '').strip()
        
        if not flat_id or not species or not quantity:
            return jsonify({'success': False, 'message': '请填写完整信息'})
        
        record = SeedlingRecord(
            flat_id=flat_id,
            species=species,
            quantity=quantity,
            source=source,
            operator=current_user.real_name
        )
        db.session.add(record)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '苗种记录已保存'})
    
    records = SeedlingRecord.query.filter(
        SeedlingRecord.flat_id.in_([f.id for f in flats])
    ).order_by(SeedlingRecord.created_at.desc()).all()
    
    return render_template('farmer/seedling.html', flats=flats, records=records)

@farmer_bp.route('/market', methods=['GET', 'POST'])
@login_required
def market():
    """产销撮合"""
    if request.method == 'POST':
        product_name = request.form.get('product_name', '').strip()
        product_category = request.form.get('product_category', '').strip()
        quantity = request.form.get('quantity', type=float)
        expected_price = request.form.get('expected_price', type=float)
        listing_date = request.form.get('listing_date')
        description = request.form.get('description', '')
        
        if not product_name or not quantity:
            return jsonify({'success': False, 'message': '请填写完整信息'})
        
        post = TransactionPost(
            farmer_id=current_user.id,
            product_name=product_name,
            product_category=product_category,
            quantity=quantity,
            expected_price=expected_price,
            listing_date=datetime.strptime(listing_date, '%Y-%m-%d') if listing_date else None,
            description=description
        )
        db.session.add(post)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '发布成功'})
    
    # 获取我的发布和他人的报价
    my_posts = TransactionPost.query.filter_by(farmer_id=current_user.id)\
        .order_by(TransactionPost.created_at.desc()).all()
    market_posts = TransactionPost.query.filter(
        TransactionPost.farmer_id != current_user.id,
        TransactionPost.status == 'open'
    ).order_by(TransactionPost.created_at.desc()).limit(20).all()
    
    return render_template('farmer/market.html', 
                         my_posts=my_posts, 
                         market_posts=market_posts)

@farmer_bp.route('/revenue', methods=['GET', 'POST'])
@login_required
def revenue():
    """收益统计"""
    user = current_user
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # 获取或创建当月收益记录
    revenue_record = RevenueRecord.query.filter_by(
        farmer_id=user.id,
        year=current_year,
        month=current_month
    ).first()
    
    if not revenue_record:
        revenue_record = RevenueRecord(
            farmer_id=user.id,
            year=current_year,
            month=current_month
        )
        db.session.add(revenue_record)
        db.session.commit()
    
    # 处理表单提交
    if request.method == 'POST':
        revenue_record.seed_cost = float(request.form.get('seed_cost', 0) or 0)
        revenue_record.hardware_rental = float(request.form.get('hardware_rental', 0) or 0)
        revenue_record.material_cost = float(request.form.get('material_cost', 0) or 0)
        revenue_record.sales_revenue = float(request.form.get('sales_revenue', 0) or 0)
        revenue_record.total_cost = revenue_record.seed_cost + revenue_record.hardware_rental + revenue_record.material_cost
        revenue_record.net_income = revenue_record.sales_revenue - revenue_record.total_cost
        db.session.commit()
        flash('本月数据已保存！', 'success')
        return redirect(url_for('farmer.revenue'))
    
    # 计算年度汇总
    yearly_records = RevenueRecord.query.filter_by(
        farmer_id=user.id,
        year=current_year
    ).order_by(RevenueRecord.month).all()
    
    yearly_summary = {
        'total_seed_cost': sum(r.seed_cost for r in yearly_records),
        'total_hardware_rental': sum(r.hardware_rental for r in yearly_records),
        'total_material_cost': sum(r.material_cost for r in yearly_records),
        'total_sales': sum(r.sales_revenue for r in yearly_records),
        'total_net': sum(r.net_income for r in yearly_records)
    }
    
    return render_template('farmer/revenue.html',
                         current_record=revenue_record,
                         yearly_records=yearly_records,
                         yearly_summary=yearly_summary)

@farmer_bp.route('/ecological-plan')
@login_required
def ecological_plan():
    """生态轮休规划"""
    user = current_user
    flats = TidalFlat.query.filter_by(farmer_id=user.id).all()
    current_year = datetime.now().year
    
    plans = EcologicalPlan.query.filter(
        EcologicalPlan.flat_id.in_([f.id for f in flats]),
        EcologicalPlan.plan_year == current_year
    ).all()
    
    # 如果没有规划，自动生成建议
    if not plans:
        plan_suggestions = []
        for i, flat in enumerate(flats):
            # 简化版轮休规划：按照三年两养一休模式
            phase = 'breeding' if (current_year % 3) != 0 else 'resting'
            plan = EcologicalPlan(
                flat_id=flat.id,
                plan_year=current_year,
                plan_phase=phase,
                start_date=datetime(current_year, 3, 1),
                end_date=datetime(current_year, 12, 31),
                plan_notes=f'三年两养一休规划：第{current_year % 3 or 3}年，{("养殖期" if phase == "breeding" else "生态修复期")}'
            )
            db.session.add(plan)
            plan_suggestions.append(plan)
        db.session.commit()
        plans = plan_suggestions
    
    return render_template('farmer/ecological_plan.html', 
                         flats=flats, 
                         plans=plans)

@farmer_bp.route('/knowledge')
@login_required
def knowledge():
    """农技知识库"""
    # 从数据库获取所有知识文章，按分类分组
    from sqlalchemy import func
    categories = db.session.query(KnowledgeArticle.category, func.count(KnowledgeArticle.id)).group_by(KnowledgeArticle.category).all()
    
    knowledge_data = []
    for category, count in categories:
        articles = KnowledgeArticle.query.filter_by(category=category).order_by(KnowledgeArticle.views.desc()).all()
        knowledge_data.append({
            'category': category,
            'articles': [{'title': a.title, 'summary': a.summary, 'content': a.content, 'views': a.views, 'author': a.author, 'is_featured': a.is_featured} for a in articles]
        })
    
    return render_template('farmer/knowledge.html', knowledge_data=knowledge_data)

@farmer_bp.route('/pdf-export/<int:log_id>')
@login_required
def export_pdf(log_id):
    """导出台账为PDF"""
    log = DailyLog.query.get_or_404(log_id)
    
    # 验证所有权
    if log.flat.farmer_id != current_user.id:
        return jsonify({'success': False, 'message': '无权访问'}), 403
    
    # 生成简单的文本内容（实际项目中可使用reportlab等库生成PDF）
    content = f"""
贝类养殖台账记录
==================
日期: {log.log_date}
滩涂: {log.flat.name}
工作类型: {log.work_type}
内容: {log.content}
操作人: {log.operator}
创建时间: {log.created_at}
    """
    
    from flask import Response
    return Response(
        content,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename=台账_{log_id}.txt'}
    )
