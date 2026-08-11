"""
政府监管专属路由
"""
from flask import Blueprint, render_template, jsonify, request, Response
from flask_login import login_required, current_user
from extensions import db
from models import (
    User, TidalFlat, HardwareDevice, WaterQualityData,
    AlertRecord, TraceabilityNode, RevenueRecord, EcologicalPlan
)
from datetime import datetime, timedelta
from sqlalchemy import func

regulator_bp = Blueprint('regulator', __name__)

@regulator_bp.route('/forbidden-zone')
@login_required
def forbidden_zone():
    """禁养区违规监测"""
    if current_user.role != 'regulator':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 获取所有在禁养区的滩涂
    forbidden_flats = TidalFlat.query.filter_by(is_fishing_allowed=False).all()
    
    # 违规养殖（在禁养区仍有养殖记录）
    violations = []
    for flat in forbidden_flats:
        farmer = User.query.get(flat.farmer_id) if flat.farmer_id else None
        if farmer:
            violations.append({
                'flat': flat,
                'farmer': farmer,
                'alert_level': 'red',
                'detected_at': datetime.now()
            })
    
    # 获取警告区滩涂
    warning_flats = TidalFlat.query.filter_by(status='warning').all()
    
    return render_template('regulator/forbidden_zone.html',
                         forbidden_flats=forbidden_flats,
                         violations=violations,
                         warning_flats=warning_flats)

@regulator_bp.route('/density-monitor')
@login_required
def density_monitor():
    """养殖密度监测"""
    if current_user.role != 'regulator':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    flats = TidalFlat.query.all()
    
    # 密度分析
    density_data = []
    for flat in flats:
        # 获取最近的苗种投放量
        from models import SeedlingRecord
        recent_seedlings = SeedlingRecord.query.filter_by(flat_id=flat.id)\
            .order_by(SeedlingRecord.created_at.desc()).first()
        
        if recent_seedlings and flat.area > 0:
            density = recent_seedlings.quantity / flat.area  # kg/亩
            # 高密度阈值：80 kg/亩
            is_high_density = density > 80
        else:
            density = 0
            is_high_density = False
        
        density_data.append({
            'flat': flat,
            'density': round(density, 1),
            'high_density': is_high_density,
            'farmer': User.query.get(flat.farmer_id).real_name if flat.farmer_id else '未知'
        })
    
    high_density_count = len([d for d in density_data if d['high_density']])
    
    return render_template('regulator/density.html',
                         density_data=density_data,
                         high_density_count=high_density_count)

@regulator_bp.route('/monitoring-report')
@login_required
def monitoring_report():
    """监管台账导出"""
    if current_user.role != 'regulator':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    report_type = request.args.get('type', 'full')
    
    if report_type == 'full':
        # 生成完整监管台账
        data = generate_full_report()
    elif report_type == 'water':
        data = generate_water_report()
    elif report_type == 'alert':
        data = generate_alert_report()
    else:
        data = generate_full_report()
    
    return render_template('regulator/report.html', 
                         report_data=data,
                         report_type=report_type)

@regulator_bp.route('/export-report')
@login_required
def export_report():
    """导出监管报表"""
    if current_user.role != 'regulator':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    report_type = request.args.get('type', 'full')
    
    if report_type == 'full':
        csv_content = generate_full_report_csv()
    elif report_type == 'water':
        csv_content = generate_water_report_csv()
    else:
        csv_content = generate_full_report_csv()
    
    from io import StringIO
    output = StringIO()
    output.write(csv_content)
    output.seek(0)
    
    filename = f"监管报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@regulator_bp.route('/ecological-capacity')
@login_required
def ecological_capacity():
    """海洋生态承载力分析"""
    if current_user.role != 'regulator':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 计算区域生态指标
    flats = TidalFlat.query.all()
    total_area = sum(f.area for f in flats)
    total_devices = HardwareDevice.query.count()
    
    # 氮磷含量估算（简化版）
    # 基于养殖密度估算污染负荷
    from models import SeedlingRecord
    total_seedling = 0
    for flat in flats:
        recent = SeedlingRecord.query.filter_by(flat_id=flat.id)\
            .order_by(SeedlingRecord.created_at.desc()).first()
        if recent:
            total_seedling += recent.quantity
    
    # 生态压力指数
    if total_area > 0:
        nitrogen_load = total_seedling * 0.01  # kg N / kg 贝类
        phosphorus_load = total_seedling * 0.003  # kg P / kg 贝类
        capacity_index = total_seedling / (total_area * 50)  # 50kg/亩为基准
    else:
        nitrogen_load = 0
        phosphorus_load = 0
        capacity_index = 0
    
    # 轮休规划统计
    current_year = datetime.now().year
    rest_plans = EcologicalPlan.query.filter_by(
        plan_year=current_year,
        plan_phase='resting'
    ).all()
    
    # 建议
    suggestions = []
    if capacity_index > 1.0:
        suggestions.append('当前养殖负荷接近或超过生态承载力，建议扩大轮休面积或降低养殖密度')
    if nitrogen_load > 100:
        suggestions.append('氮负荷较高，建议增加生态混养比例（如贝类+海带），促进营养盐循环')
    if len(rest_plans) < len(flats) * 0.2:
        suggestions.append('生态轮休比例偏低，建议增加滩涂轮休面积至20%以上')
    
    return render_template('regulator/ecological.html',
                         stats={
                             'total_area': total_area,
                             'total_devices': total_devices,
                             'total_seedling': total_seedling,
                             'nitrogen_load': round(nitrogen_load, 1),
                             'phosphorus_load': round(phosphorus_load, 1),
                             'capacity_index': round(capacity_index, 2),
                             'rest_plans_count': len(rest_plans)
                         },
                         suggestions=suggestions)

@regulator_bp.route('/region-overview')
@login_required
def region_overview():
    """区域概览"""
    if current_user.role != 'regulator':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 按区域统计
    regions = db.session.query(
        User.area,
        func.count(User.id).label('farmer_count')
    ).filter(User.role == 'farmer').group_by(User.area).all()
    
    region_data = []
    for region, count in regions:
        flats_in_region = TidalFlat.query.filter(
            TidalFlat.farmer_id.in_(
                [u.id for u in User.query.filter_by(role='farmer', area=region).all()]
            )
        ).all()
        
        alerts_in_region = AlertRecord.query.filter(
            AlertRecord.flat_id.in_([f.id for f in flats_in_region]) if flats_in_region else AlertRecord.flat_id == -1
        ).count()
        
        region_data.append({
            'region': region,
            'farmer_count': count,
            'flat_count': len(flats_in_region),
            'total_area': sum(f.area for f in flats_in_region),
            'alert_count': alerts_in_region
        })
    
    return jsonify({'success': True, 'regions': region_data})

def generate_full_report():
    """生成完整监管报告数据"""
    return {
        'report_title': '农产品质量安全监管台账',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sections': [
            {
                'title': '滩涂养殖情况',
                'data': [{
                    'total_flats': TidalFlat.query.count(),
                    'normal_flats': TidalFlat.query.filter_by(status='normal').count(),
                    'warning_flats': TidalFlat.query.filter_by(status='warning').count()
                }]
            },
            {
                'title': '预警处理情况',
                'data': [{
                    'total_alerts': AlertRecord.query.count(),
                    'resolved': AlertRecord.query.filter_by(resolved=True).count(),
                    'unresolved': AlertRecord.query.filter_by(resolved=False).count()
                }]
            },
            {
                'title': '溯源管理情况',
                'data': [{
                    'total_traces': TraceabilityNode.query.count(),
                    'completed': TraceabilityNode.query.filter_by(status='completed').count()
                }]
            }
        ]
    }

def generate_water_report():
    """生成水质报告数据"""
    return {
        'report_title': '水质监测监管报告',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'summary': '本报告基于全域滩涂水质实时监测数据生成',
        'flats_with_data': WaterQualityData.query.distinct(WaterQualityData.flat_id).count()
    }

def generate_alert_report():
    """生成预警报告数据"""
    return {
        'report_title': '灾害预警处置报告',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'alert_levels': {
            'blue': AlertRecord.query.filter_by(level='blue').count(),
            'orange': AlertRecord.query.filter_by(level='orange').count(),
            'red': AlertRecord.query.filter_by(level='red').count()
        }
    }

def generate_full_report_csv():
    """生成完整报告CSV"""
    lines = ['项目,数量']
    lines.append(f'滩涂总数,{TidalFlat.query.count()}')
    lines.append(f'正常滩涂,{TidalFlat.query.filter_by(status="normal").count()}')
    lines.append(f'预警滩涂,{TidalFlat.query.filter_by(status="warning").count()}')
    lines.append(f'预警总数,{AlertRecord.query.count()}')
    lines.append(f'已处理预警,{AlertRecord.query.filter_by(resolved=True).count()}')
    lines.append(f'未处理预警,{AlertRecord.query.filter_by(resolved=False).count()}')
    lines.append(f'溯源总数,{TraceabilityNode.query.count()}')
    lines.append(f'完成溯源,{TraceabilityNode.query.filter_by(status="completed").count()}')
    return '\n'.join(lines)

def generate_water_report_csv():
    """生成水质报告CSV"""
    lines = ['滩涂名称,水温(℃),盐度(‰),溶解氧(mg/L),pH值,监测时间']
    for flat in TidalFlat.query.all():
        latest = WaterQualityData.query.filter_by(flat_id=flat.id)\
            .order_by(WaterQualityData.timestamp.desc()).first()
        if latest:
            lines.append(f'{flat.name},{latest.temperature},{latest.salinity},{latest.dissolved_oxygen},{latest.ph},{latest.timestamp}')
    return '\n'.join(lines)
