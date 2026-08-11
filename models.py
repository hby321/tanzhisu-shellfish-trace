"""
数据模型定义
"""
from datetime import datetime
from flask_login import UserMixin
from extensions import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash

# 用户角色定义
ROLE_FARMER = 'farmer'          # 农户
ROLE_COOPERATIVE = 'cooperative' # 合作社
ROLE_ENTERPRISE = 'enterprise'   # 企业
ROLE_REGULATOR = 'regulator'     # 监管

ROLE_NAMES = {
    ROLE_FARMER: '农户',
    ROLE_COOPERATIVE: '合作社',
    ROLE_ENTERPRISE: '企业',
    ROLE_REGULATOR: '监管'
}

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_FARMER)
    real_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    area = db.Column(db.String(100))  # 所在区域
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_active = db.Column(db.Boolean, default=True)
    
    # 关联
    tidal_flats = db.relationship('TidalFlat', backref='owner', lazy='dynamic')
    traceability_records = db.relationship('TraceabilityNode', 
                                           foreign_keys='TraceabilityNode.farmer_id',
                                           backref=db.backref('farmer', lazy='joined'), lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def role_name(self):
        return ROLE_NAMES.get(self.role, '未知')
    
    @property
    def is_farmer(self):
        return self.role == ROLE_FARMER
    
    @property
    def is_cooperative(self):
        return self.role == ROLE_COOPERATIVE
    
    @property
    def is_enterprise(self):
        return self.role == ROLE_ENTERPRISE
    
    @property
    def is_regulator(self):
        return self.role == ROLE_REGULATOR

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class TidalFlat(db.Model):
    """滩涂点位模型"""
    __tablename__ = 'tidal_flats'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    area = db.Column(db.Float)  # 面积（亩）
    latitude = db.Column(db.Float)  # 纬度
    longitude = db.Column(db.Float)  # 经度
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='normal')  # normal/warning/danger
    is_fishing_allowed = db.Column(db.Boolean, default=True)  # 是否在禁养区
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联
    water_quality_data = db.relationship('WaterQualityData', backref='flat', lazy='dynamic')
    hardware_devices = db.relationship('HardwareDevice', backref='flat', lazy='dynamic')
    alerts = db.relationship('AlertRecord', backref='flat', lazy='dynamic')
    
    @property
    def status_name(self):
        status_map = {'normal': '正常', 'warning': '预警', 'danger': '危险'}
        return status_map.get(self.status, '未知')


class HardwareDevice(db.Model):
    """低温传感硬件设备模型"""
    __tablename__ = 'hardware_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), unique=True, nullable=False)
    model = db.Column(db.String(50))
    flat_id = db.Column(db.Integer, db.ForeignKey('tidal_flats.id'))
    status = db.Column(db.String(20), default='online')  # online/offline/fault
    battery_level = db.Column(db.Float, default=100)  # 电量百分比
    firmware_version = db.Column(db.String(20), default='v1.0.0')
    last_sync = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 租赁信息
    rental_start = db.Column(db.DateTime)
    rental_end = db.Column(db.DateTime)
    rental_fee = db.Column(db.Float)
    
    @property
    def status_name(self):
        status_map = {'online': '在线', 'offline': '离线', 'fault': '故障'}
        return status_map.get(self.status, '未知')
    
    @property
    def battery_status(self):
        if self.battery_level > 50:
            return '充足'
        elif self.battery_level > 20:
            return '正常'
        else:
            return '低电量'


class WaterQualityData(db.Model):
    """水质数据模型"""
    __tablename__ = 'water_quality_data'
    
    id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('tidal_flats.id'))
    timestamp = db.Column(db.DateTime, default=datetime.now)
    temperature = db.Column(db.Float)  # 水温 ℃
    salinity = db.Column(db.Float)  # 盐度 ‰
    dissolved_oxygen = db.Column(db.Float)  # 溶解氧 mg/L
    ph = db.Column(db.Float)  # pH值
    
    # 正常范围参考（寒地贝类）
    NORMAL_RANGES = {
        'temperature': (-1, 20),
        'salinity': (25, 38),
        'dissolved_oxygen': (4, 8),
        'ph': (7.5, 8.5)
    }
    
    def get_quality_status(self):
        """获取水质状态"""
        issues = []
        ranges = self.NORMAL_RANGES
        
        if self.temperature:
            t_min, t_max = ranges['temperature']
            if self.temperature < t_min or self.temperature > t_max:
                issues.append('水温异常')
        
        if self.salinity:
            s_min, s_max = ranges['salinity']
            if self.salinity < s_min or self.salinity > s_max:
                issues.append('盐度异常')
        
        if self.dissolved_oxygen:
            do_min, do_max = ranges['dissolved_oxygen']
            if self.dissolved_oxygen < do_min:
                issues.append('溶解氧偏低')
            elif self.dissolved_oxygen > do_max:
                issues.append('溶解氧偏高')
        
        if self.ph:
            ph_min, ph_max = ranges['ph']
            if self.ph < ph_min or self.ph > ph_max:
                issues.append('pH异常')
        
        if not issues:
            return {'status': 'normal', 'issues': []}
        elif len(issues) == 1:
            return {'status': 'warning', 'issues': issues}
        else:
            return {'status': 'danger', 'issues': issues}


class AlertRecord(db.Model):
    """预警记录模型"""
    __tablename__ = 'alert_records'
    
    ALERT_LEVELS = {
        'blue': {'name': '蓝色预警', 'color': '#2196F3', 'severity': 1},
        'orange': {'name': '橙色预警', 'color': '#FF9800', 'severity': 2},
        'red': {'name': '红色预警', 'color': '#F44336', 'severity': 3}
    }
    
    ALERT_TYPES = {
        'temperature': '水温异常',
        'salinity': '盐度异常',
        'oxygen': '溶解氧异常',
        'ph': 'pH异常',
        'cold_wave': '寒潮预警',
        'hypoxia': '缺氧预警',
        'other': '其他预警'
    }
    
    id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('tidal_flats.id'))
    level = db.Column(db.String(20), nullable=False)
    alert_type = db.Column(db.String(30))
    message = db.Column(db.Text)
    advice = db.Column(db.Text)  # 应对建议
    timestamp = db.Column(db.DateTime, default=datetime.now)
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    
    @property
    def level_info(self):
        return self.ALERT_LEVELS.get(self.level, {'name': '未知', 'color': '#999', 'severity': 0})
    
    @property
    def type_name(self):
        return self.ALERT_TYPES.get(self.alert_type, '未知')


class TraceabilityNode(db.Model):
    """区块链溯源节点模型"""
    __tablename__ = 'traceability_nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_code = db.Column(db.String(50), unique=True, nullable=False)
    product_name = db.Column(db.String(100))
    product_category = db.Column(db.String(50))  # 贝类品类
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='processing')  # processing/completed
    blockchain_hash = db.Column(db.String(64))
    qr_code_path = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 溯源详情
    seed_source = db.Column(db.String(200))  # 苗种来源
    seed_date = db.Column(db.Date)  # 投苗日期
    harvest_date = db.Column(db.Date)  # 捕捞日期
    quality_check = db.Column(db.String(200))  # 质检结果
    logistics_info = db.Column(db.String(200))  # 物流信息
    
    # 企业加工信息
    enterprise_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    processing_info = db.Column(db.Text)
    
    # 关联
    enterprise = db.relationship('User', 
                                foreign_keys=[enterprise_id],
                                backref='processed_traceability',
                                lazy='joined')
    
    @property
    def status_name(self):
        return '已完成' if self.status == 'completed' else '进行中'


class SeedlingRecord(db.Model):
    """苗种投放记录"""
    __tablename__ = 'seedling_records'
    
    id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('tidal_flats.id'))
    species = db.Column(db.String(50))  # 贝类品种
    quantity = db.Column(db.Float)  # 投放量（kg）
    source = db.Column(db.String(200))  # 苗种来源
    operator = db.Column(db.String(50))
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)


class DailyLog(db.Model):
    """养殖日常台账"""
    __tablename__ = 'daily_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('tidal_flats.id'))
    log_date = db.Column(db.Date)
    work_type = db.Column(db.String(50))  # 投喂/消杀/巡查/捕捞
    content = db.Column(db.Text)
    operator = db.Column(db.String(50))
    photos = db.Column(db.String(500))  # 图片路径，逗号分隔
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联
    flat = db.relationship('TidalFlat', backref='daily_logs', lazy='joined')


class TransactionPost(db.Model):
    """产销撮合发布"""
    __tablename__ = 'transaction_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_name = db.Column(db.String(100))
    product_category = db.Column(db.String(50))
    quantity = db.Column(db.Float)  # 产量（kg）
    expected_price = db.Column(db.Float)  # 预期售价（元/kg）
    listing_date = db.Column(db.Date)  # 上市时间
    status = db.Column(db.String(20), default='open')  # open/closed
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联
    farmer = db.relationship('User', backref='transaction_posts', lazy='joined')


class PurchaseOrder(db.Model):
    """采购订单"""
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('transaction_posts.id'))
    enterprise_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    agreed_price = db.Column(db.Float)
    quantity = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')  # pending/confirmed/completed
    contract_path = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联
    post = db.relationship('TransactionPost', backref='purchase_orders', lazy='joined')
    enterprise = db.relationship('User', backref='purchase_orders')


class RevenueRecord(db.Model):
    """农户收益统计"""
    __tablename__ = 'revenue_records'
    
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    year = db.Column(db.Integer)
    month = db.Column(db.Integer)
    # 成本
    seed_cost = db.Column(db.Float, default=0)  # 苗种成本
    hardware_rental = db.Column(db.Float, default=0)  # 硬件租赁费
    material_cost = db.Column(db.Float, default=0)  # 消杀耗材
    other_cost = db.Column(db.Float, default=0)  # 其他成本
    # 收入
    sales_revenue = db.Column(db.Float, default=0)  # 销售收入
    # 计算
    total_cost = db.Column(db.Float, default=0)  # 总成本
    net_income = db.Column(db.Float, default=0)  # 净收入
    created_at = db.Column(db.DateTime, default=datetime.now)


class EcologicalPlan(db.Model):
    """生态轮休规划"""
    __tablename__ = 'ecological_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('tidal_flats.id'))
    plan_year = db.Column(db.Integer)
    plan_phase = db.Column(db.String(20))  # breeding/resting
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    plan_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)


class WeatherWarning(db.Model):
    """气象预警记录"""
    __tablename__ = 'weather_warnings'
    
    id = db.Column(db.Integer, primary_key=True)
    warning_type = db.Column(db.String(50))  # gale/cold/snow
    level = db.Column(db.String(20))  # blue/yellow/orange/red
    area = db.Column(db.String(100))
    content = db.Column(db.Text)
    forecast_date = db.Column(db.Date)
    processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class KnowledgeArticle(db.Model):
    """农技知识文章"""
    __tablename__ = 'knowledge_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text)
    content = db.Column(db.Text)  # 完整内容
    author = db.Column(db.String(50))
    views = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class PredictionRecord(db.Model):
    """AI产量预测历史记录"""
    __tablename__ = 'prediction_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    flat_id = db.Column(db.Integer, db.ForeignKey('tidal_flats.id'))
    seed_quantity = db.Column(db.Float)
    predict_days = db.Column(db.Integer)
    predicted_yield = db.Column(db.Float)
    survival_rate = db.Column(db.Float)
    environmental_score = db.Column(db.Float)
    confidence = db.Column(db.Float)
    avg_temperature = db.Column(db.Float)
    avg_salinity = db.Column(db.Float)
    avg_oxygen = db.Column(db.Float)
    avg_ph = db.Column(db.Float)
    suggestions_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联
    user = db.relationship('User', backref='predictions', lazy='joined')
    flat = db.relationship('TidalFlat', backref='predictions', lazy='joined')


class Notification(db.Model):
    """消息通知模型"""
    __tablename__ = 'notifications'
    
    TYPE_ALERT = 'alert'          # 灾害预警
    TYPE_TRACEABILITY = 'trace'   # 溯源通知
    TYPE_TRANSACTION = 'trade'    # 产销交易
    TYPE_SYSTEM = 'system'        # 系统消息
    TYPE_ENTERPRISE = 'enterprise'  # 企业通知
    TYPE_REGULATOR = 'regulator'  # 监管通知
    
    TYPE_NAMES = {
        TYPE_ALERT: '灾害预警',
        TYPE_TRACEABILITY: '溯源通知',
        TYPE_TRANSACTION: '产销交易',
        TYPE_SYSTEM: '系统消息',
        TYPE_ENTERPRISE: '企业通知',
        TYPE_REGULATOR: '监管通知'
    }
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    notify_type = db.Column(db.String(30), default=TYPE_SYSTEM)
    level = db.Column(db.String(20), default='info')  # info/warning/danger/success
    is_read = db.Column(db.Boolean, default=False)
    related_id = db.Column(db.Integer)  # 关联业务ID
    related_type = db.Column(db.String(30))  # 关联业务类型
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联
    user = db.relationship('User', backref='notifications', lazy='joined')
    
    @property
    def type_name(self):
        return self.TYPE_NAMES.get(self.notify_type, '系统消息')
    
    @property
    def level_class(self):
        levels = {
            'info': 'bg-blue-50 text-blue-700 border-blue-200',
            'warning': 'bg-yellow-50 text-yellow-700 border-yellow-200',
            'danger': 'bg-red-50 text-red-700 border-red-200',
            'success': 'bg-green-50 text-green-700 border-green-200'
        }
        return levels.get(self.level, levels['info'])
