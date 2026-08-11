"""
AI产量预测路由
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import TidalFlat, WaterQualityData, SeedlingRecord, PredictionRecord
from datetime import datetime, timedelta
import random
import math

predict_bp = Blueprint('predict', __name__)

# 简易AI预测模型（基于历史数据的加权预测）
class YieldPredictor:
    """寒地产量预测模型"""
    
    # 寒地贝类适宜条件
    OPTIMAL_CONDITIONS = {
        'temperature': (2, 12),      # 适宜水温范围
        'salinity': (28, 34),         # 适宜盐度范围
        'dissolved_oxygen': (5, 8),   # 适宜溶解氧
        'ph': (7.8, 8.2),            # 适宜pH
        'optimal_stocking': (50, 80)  # 适宜养殖密度（kg/亩）
    }
    
    @classmethod
    def predict(cls, flat_area, seed_quantity, water_quality_data, days=90):
        """
        预测贝类产量和存活率
        
        参数:
            flat_area: 滩涂面积（亩）
            seed_quantity: 苗种投放量（kg）
            water_quality_data: 历史水质数据列表
            days: 预测周期（天）
        
        返回:
            dict: 预测结果
        """
        # 计算平均水质指标
        if water_quality_data:
            avg_temp = sum(d.temperature for d in water_quality_data) / len(water_quality_data)
            avg_salinity = sum(d.salinity for d in water_quality_data) / len(water_quality_data)
            avg_oxygen = sum(d.dissolved_oxygen for d in water_quality_data) / len(water_quality_data)
            avg_ph = sum(d.ph for d in water_quality_data) / len(water_quality_data)
        else:
            avg_temp = 8
            avg_salinity = 32
            avg_oxygen = 6
            avg_ph = 8.0
        
        # 计算环境适宜度（0-100分）
        temp_score = cls._calc_condition_score(avg_temp, *cls.OPTIMAL_CONDITIONS['temperature'])
        salinity_score = cls._calc_condition_score(avg_salinity, *cls.OPTIMAL_CONDITIONS['salinity'])
        oxygen_score = cls._calc_condition_score(avg_oxygen, *cls.OPTIMAL_CONDITIONS['dissolved_oxygen'])
        ph_score = cls._calc_condition_score(avg_ph, *cls.OPTIMAL_CONDITIONS['ph'])
        
        # 加权综合评分
        env_score = (temp_score * 0.3 + salinity_score * 0.25 + oxygen_score * 0.25 + ph_score * 0.2) * 100
        
        # 计算存活率（基于环境适宜度）
        base_survival_rate = 0.85  # 基础存活率85%
        env_factor = env_score / 100
        survival_rate = base_survival_rate * (0.5 + 0.5 * env_factor)
        survival_rate = max(0.3, min(0.95, survival_rate))  # 限制在30%-95%
        
        # 预测产量
        # 贝类一般增重倍数3-5倍（从小苗到成品）
        growth_factor = 4.0 * env_factor  # 环境越好增重越多
        predicted_yield = seed_quantity * survival_rate * growth_factor
        
        # 置信度
        confidence = min(0.95, 0.7 + random.uniform(0, 0.1))
        
        # 生成优化建议
        suggestions = cls._generate_suggestions(
            avg_temp, avg_salinity, avg_oxygen, avg_ph, 
            env_score, survival_rate
        )
        
        return {
            'predicted_yield': round(predicted_yield, 0),
            'survival_rate': round(survival_rate * 100, 1),
            'growth_factor': round(growth_factor, 1),
            'environmental_score': round(env_score, 1),
            'confidence': round(confidence * 100, 1),
            'avg_water_quality': {
                'temperature': round(avg_temp, 1),
                'salinity': round(avg_salinity, 1),
                'oxygen': round(avg_oxygen, 1),
                'ph': round(avg_ph, 2)
            },
            'temp_score': round(temp_score * 100, 1),
            'salinity_score': round(salinity_score * 100, 1),
            'oxygen_score': round(oxygen_score * 100, 1),
            'ph_score': round(ph_score * 100, 1),
            'suggestions': suggestions,
            'yield_trend': cls._generate_trend(predicted_yield, days)
        }
    
    @classmethod
    def _calc_condition_score(cls, value, min_val, max_val):
        """计算单一指标的适宜度分数（0-1）"""
        if min_val <= value <= max_val:
            return 1.0
        elif value < min_val:
            deviation = (min_val - value) / min_val
            return max(0, 1.0 - deviation * 3)
        else:
            deviation = (value - max_val) / max_val
            return max(0, 1.0 - deviation * 3)
    
    @classmethod
    def _generate_suggestions(cls, temp, salinity, oxygen, ph, env_score, survival_rate):
        """生成优化建议"""
        suggestions = []
        
        if temp < cls.OPTIMAL_CONDITIONS['temperature'][0]:
            suggestions.append({
                'level': 'warning',
                'type': 'temperature',
                'title': '水温偏低',
                'content': f'当前平均水温{temp}℃，低于适宜范围。建议：加深养殖水位保温，或使用保温网覆盖。',
                'action': 'increase_depth'
            })
        elif temp > cls.OPTIMAL_CONDITIONS['temperature'][1]:
            suggestions.append({
                'level': 'warning',
                'type': 'temperature',
                'title': '水温偏高',
                'content': f'当前平均水温{temp}℃，高于适宜范围。建议：增加换水频次，使用遮阳网。',
                'action': 'increase_water_change'
            })
        
        if oxygen < cls.OPTIMAL_CONDITIONS['dissolved_oxygen'][0]:
            suggestions.append({
                'level': 'danger',
                'type': 'oxygen',
                'title': '溶解氧不足',
                'content': f'当前平均溶解氧{oxygen}mg/L，低于安全阈值。建议：立即启动增氧设备，检查是否有污染。',
                'action': 'start_aerator'
            })
        
        if salinity < cls.OPTIMAL_CONDITIONS['salinity'][0]:
            suggestions.append({
                'level': 'warning',
                'type': 'salinity',
                'title': '盐度偏低',
                'content': f'当前平均盐度{salinity}‰，低于适宜范围。建议：检查是否有淡水注入，必要时调整养殖位置。',
                'action': 'adjust_position'
            })
        
        if env_score < 60:
            suggestions.append({
                'level': 'info',
                'type': 'overall',
                'title': '整体环境待优化',
                'content': f'环境综合评分{env_score}分，建议采取以上措施改善养殖环境，预计可提升产量{round((80 - env_score) * 0.5)}%。',
                'action': 'comprehensive_optimization'
            })
        
        if survival_rate < 0.6:
            suggestions.append({
                'level': 'danger',
                'type': 'survival',
                'title': '存活率偏低',
                'content': f'预测存活率{survival_rate * 100}%，建议降低养殖密度至{cls.OPTIMAL_CONDITIONS["optimal_stocking"][0]}kg/亩以下。',
                'action': 'reduce_density'
            })
        
        # 生态轮休建议
        if env_score > 80 and survival_rate > 0.8:
            suggestions.append({
                'level': 'success',
                'type': 'rotation',
                'title': '适宜轮休规划',
                'content': '当前滩涂环境良好，建议纳入"三年两养一休"规划，养殖2年后进行生态修复。',
                'action': 'plan_rotation'
            })
        
        return suggestions
    
    @classmethod
    def _generate_trend(cls, final_yield, days):
        """生成产量增长趋势数据"""
        trend = []
        current_yield = 0
        for day in range(0, days + 1, 10):
            progress = day / days
            # S型生长曲线
            growth = 1 - math.exp(-3 * progress)
            day_yield = final_yield * growth
            trend.append({
                'day': day,
                'yield': round(day_yield, 0)
            })
        return trend

@predict_bp.route('/')
@login_required
def predict_index():
    """预测首页"""
    user = current_user
    
    if user.role == 'farmer':
        flats = TidalFlat.query.filter_by(farmer_id=user.id).all()
        predictions = PredictionRecord.query.filter_by(user_id=user.id).order_by(PredictionRecord.created_at.desc()).limit(10).all()
    elif user.role == 'cooperative':
        from models import User as UserModel
        member_ids = [m.id for m in UserModel.query.filter_by(role='farmer', area=user.area).all()]
        flats = TidalFlat.query.filter(TidalFlat.farmer_id.in_(member_ids) if member_ids else TidalFlat.farmer_id == -1).all()
        predictions = PredictionRecord.query.filter(PredictionRecord.user_id.in_(member_ids) if member_ids else PredictionRecord.user_id == -1).order_by(PredictionRecord.created_at.desc()).limit(10).all()
    else:
        flats = TidalFlat.query.all()
        predictions = PredictionRecord.query.order_by(PredictionRecord.created_at.desc()).limit(10).all()
    
    # 获取每个滩涂的苗种记录
    flat_details = []
    for flat in flats:
        seedlings = SeedlingRecord.query.filter_by(flat_id=flat.id).all()
        flat_details.append({
            'flat': flat,
            'seedlings': seedlings,
            'has_active_seedling': any(s.quantity > 0 for s in seedlings)
        })
    
    # 计算统计数据
    total_yield = sum(p.predicted_yield for p in predictions) if predictions else 0
    total_env = sum(p.environmental_score for p in predictions) if predictions else 0
    total_survival = sum(p.survival_rate for p in predictions) if predictions else 0
    count = len(predictions)
    
    return render_template('predict/index.html', 
                         flats=flat_details, 
                         predictions=predictions,
                         total_yield=total_yield,
                         avg_env=total_env / count if count > 0 else 0,
                         avg_survival=total_survival / count if count > 0 else 0,
                         predict_count=count)

@predict_bp.route('/run', methods=['POST'])
@login_required
def run_prediction():
    """执行预测 —— 转发至《数据智能体综合应用平台V1.0》软著·贝类产量预测智能体(LSTM)"""
    flat_id = request.form.get('flat_id', type=int)
    seed_quantity = request.form.get('seed_quantity', type=float)
    predict_days = request.form.get('days', 90, type=int)

    if not flat_id or not seed_quantity:
        return jsonify({'success': False, 'message': '请填写完整信息'})

    flat = TidalFlat.query.get_or_404(flat_id)

    # 获取近7天水质数据传入智能体
    week_ago = datetime.now() - timedelta(days=7)
    water_data = WaterQualityData.query.filter(
        WaterQualityData.flat_id == flat_id,
        WaterQualityData.timestamp >= week_ago
    ).order_by(WaterQualityData.timestamp.asc()).all()

    # 优先调用软著智能体平台(8090)的贝类产量预测智能体
    from services.agent_client import call_agent
    env_data = {
        'flat_name': flat.name, 'flat_area': flat.area,
        'seed_quantity': seed_quantity, 'days': predict_days,
        'water_history': [{
            'temperature': w.temperature, 'salinity': w.salinity,
            'oxygen': w.dissolved_oxygen, 'ph': w.ph
        } for w in water_data]
    }
    agent_result = call_agent('贝类产量预测智能体', env_data)

    if agent_result['success']:
        ai = agent_result['ai_reply']
        # 解析软著平台返回结果，兼容本地数据库字段
        import re
        def _num(s):
            m = re.search(r'-?\d+\.?\d*', str(s))
            return float(m.group()) if m else 0.0
        predicted_yield = _num(ai.get('预估产量', 0))
        survival_rate = _num(ai.get('存活率', 0))
        env_score = _num(ai.get('环境评分', 0))
        confidence = _num(ai.get('置信度', 0))
        suggestions = ai.get('风险提示', [])

        # 保存预测记录到数据库
        prediction_record = PredictionRecord(
            user_id=current_user.id,
            flat_id=flat_id,
            seed_quantity=seed_quantity,
            predict_days=predict_days,
            predicted_yield=predicted_yield,
            survival_rate=survival_rate,
            environmental_score=env_score,
            confidence=confidence,
            avg_temperature=env_data['water_history'][-1]['temperature'] if env_data['water_history'] else 8,
            avg_salinity=env_data['water_history'][-1]['salinity'] if env_data['water_history'] else 30,
            avg_oxygen=env_data['water_history'][-1]['oxygen'] if env_data['water_history'] else 6,
            avg_ph=env_data['water_history'][-1]['ph'] if env_data['water_history'] else 8.0,
            suggestions_count=len(suggestions)
        )
        db.session.add(prediction_record)
        db.session.commit()

        return jsonify({
            'success': True,
            'source': 'agent_server',
            'platform': '数据智能体综合应用平台V1.0',
            'prediction': {
                'predicted_yield': predicted_yield,
                'survival_rate': survival_rate,
                'environmental_score': env_score,
                'confidence': confidence,
                'temp_score': ai.get('水温适宜度', 0),
                'salinity_score': ai.get('盐度适宜度', 0),
                'oxygen_score': ai.get('溶氧适宜度', 0),
                'ph_score': ai.get('pH适宜度', 0),
                'avg_water_quality': {
                    'temperature': env_data['water_history'][-1]['temperature'] if env_data['water_history'] else 8,
                    'salinity': env_data['water_history'][-1]['salinity'] if env_data['water_history'] else 30,
                    'oxygen': env_data['water_history'][-1]['oxygen'] if env_data['water_history'] else 6,
                    'ph': env_data['water_history'][-1]['ph'] if env_data['water_history'] else 8.0
                },
                'suggestions': [{
                    'level': s.get('level', 'info'),
                    'title': '智能体风险提示',
                    'content': s.get('text', ''),
                    'action': 'agent_advice'
                } for s in suggestions],
                'yield_trend': ai.get('增长曲线', []),
                '养殖建议': ai.get('养殖建议', '')
            },
            'flat_info': {'name': flat.name, 'area': flat.area}
        })

    # 软著平台离线时降级到本地预测模型（保证业务可用性）
    result = YieldPredictor.predict(
        flat_area=flat.area,
        seed_quantity=seed_quantity,
        water_quality_data=water_data,
        days=predict_days
    )
    prediction_record = PredictionRecord(
        user_id=current_user.id,
        flat_id=flat_id,
        seed_quantity=seed_quantity,
        predict_days=predict_days,
        predicted_yield=result['predicted_yield'],
        survival_rate=result['survival_rate'],
        environmental_score=result['environmental_score'],
        confidence=result['confidence'],
        avg_temperature=result['avg_water_quality']['temperature'],
        avg_salinity=result['avg_water_quality']['salinity'],
        avg_oxygen=result['avg_water_quality']['oxygen'],
        avg_ph=result['avg_water_quality']['ph'],
        suggestions_count=len(result['suggestions'])
    )
    db.session.add(prediction_record)
    db.session.commit()

    return jsonify({
        'success': True,
        'source': 'local_fallback',
        'message': agent_result.get('message', '软著平台离线，已降级本地预测'),
        'prediction': result,
        'flat_info': {'name': flat.name, 'area': flat.area}
    })

@predict_bp.route('/compare', methods=['POST'])
@login_required
def compare_prediction():
    """对比不同滩涂的预测结果"""
    flat_ids = request.form.getlist('flat_ids')
    seed_quantities = request.form.getlist('seed_quantities')
    
    if not flat_ids:
        return jsonify({'success': False, 'message': '请选择至少一个滩涂'})
    
    results = []
    for i, flat_id in enumerate(flat_ids):
        flat = TidalFlat.query.get(int(flat_id))
        if not flat:
            continue
        
        seed_qty = float(seed_quantities[i]) if i < len(seed_quantities) else 50.0
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        water_data = WaterQualityData.query.filter(
            WaterQualityData.flat_id == flat.id,
            WaterQualityData.timestamp >= thirty_days_ago
        ).all()
        
        prediction = YieldPredictor.predict(
            flat_area=flat.area,
            seed_quantity=seed_qty,
            water_quality_data=water_data
        )
        
        results.append({
            'flat_name': flat.name,
            'predicted_yield': prediction['predicted_yield'],
            'survival_rate': prediction['survival_rate'],
            'env_score': prediction['environmental_score'],
            'suggestions_count': len(prediction['suggestions'])
        })
    
    return jsonify({'success': True, 'results': results})
