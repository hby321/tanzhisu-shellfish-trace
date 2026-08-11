"""
滩智溯 - 辽宁寒地滩涂贝类全链路智慧养殖与区块链溯源一体化平台
Flask主应用入口
"""
import os
import sys
import traceback
from flask import Flask, render_template, redirect, url_for, flash, jsonify, send_from_directory
from flask_cors import CORS
from extensions import db, login_manager

def create_app():
    """应用工厂函数"""
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tanzhi_su_secret_key_2024')
    # 数据库地址：优先使用环境变量（云端部署），默认本地 SQLite
    # Render 免费层为临时文件系统，重启会丢失数据，init_demo_data 会自动重建演示数据
    db_uri = os.environ.get('DATABASE_URL', 'sqlite:///tanzhisu.db')
    # 兼容 Render/Heroku 风格的 PostgreSQL URL（如需持久化可配置）
    if db_uri.startswith('postgres://'):
        db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB上传限制
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}, r"/ai/api/*": {"origins": "*"}})
    
    # 注册蓝图
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.water_quality import water_bp
    from routes.alert import alert_bp
    from routes.hardware import hardware_bp
    from routes.traceability import trace_bp
    from routes.predict import predict_bp
    from routes.farmer import farmer_bp
    from routes.cooperative import coop_bp
    from routes.enterprise import enterprise_bp
    from routes.regulator import regulator_bp
    from routes.api import api_bp
    from routes.mini_program import mini_bp
    from routes.notification import notification_bp
    from routes.ai import ai_bp  # 软著《数据智能体综合应用平台 V1.0》转发入口
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(water_bp, url_prefix='/water')
    app.register_blueprint(alert_bp, url_prefix='/alert')
    app.register_blueprint(hardware_bp, url_prefix='/hardware')
    app.register_blueprint(trace_bp, url_prefix='/trace')
    app.register_blueprint(predict_bp, url_prefix='/predict')
    app.register_blueprint(farmer_bp, url_prefix='/farmer')
    app.register_blueprint(coop_bp, url_prefix='/coop')
    app.register_blueprint(enterprise_bp, url_prefix='/enterprise')
    app.register_blueprint(regulator_bp, url_prefix='/regulator')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(mini_bp, url_prefix='/mini')
    app.register_blueprint(notification_bp, url_prefix='/notification')
    app.register_blueprint(ai_bp, url_prefix='/ai')  # AI智能体统一入口
    
    # 注册错误处理
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        traceback.print_exc()
        return render_template('errors/500.html'), 500
    
    # 首页
    @app.route('/')
    def index():
        if not login_manager._login_disabled:
            from flask_login import current_user
            if current_user.is_authenticated:
                return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    # 小程序H5入口 - 部署到公网后手机微信访问此路径
    @app.route('/m/')
    def mini_program_h5():
        h5_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'h5')
        if os.path.exists(os.path.join(h5_path, 'index.html')):
            return send_from_directory(h5_path, 'index.html')
        return '小程序H5未构建，请先运行 npm run build:h5', 404

    @app.route('/m/<path:filename>')
    def mini_program_static(filename):
        h5_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'h5')
        if os.path.exists(os.path.join(h5_path, filename)):
            return send_from_directory(h5_path, filename)
        return '', 404
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        init_demo_data(app)
    
    return app

def init_demo_data(app):
    """初始化演示数据"""
    from models import User, TidalFlat, HardwareDevice, WaterQualityData, AlertRecord, TraceabilityNode
    from models import RevenueRecord, SeedlingRecord, EcologicalPlan, TransactionPost, DailyLog
    from models import WeatherWarning, PurchaseOrder
    from models import KnowledgeArticle, PredictionRecord, Notification
    from werkzeug.security import generate_password_hash
    import datetime
    import hashlib
    
    # 检查是否已有数据
    if User.query.first():
        return
    
    # 创建用户
    users = [
        # 农户账号（保持原有ID不变）
        {'username': 'farmer001', 'password': '123456', 'role': 'farmer', 'name': '张养殖', 'phone': '13800000001', 'area': '丹东东港'},
        {'username': 'farmer002', 'password': '123456', 'role': 'farmer', 'name': '李海产', 'phone': '13800000002', 'area': '盘锦盖州'},
        {'username': 'farmer003', 'password': '123456', 'role': 'farmer', 'name': '王滩涂', 'phone': '13800000003', 'area': '丹东凤城'},
        # 新增丹东东港地区农户（合作社社员）
        {'username': 'farmer004', 'password': '123456', 'role': 'farmer', 'name': '陈贝类', 'phone': '13800000004', 'area': '丹东东港'},
        {'username': 'farmer005', 'password': '123456', 'role': 'farmer', 'name': '刘滩涂', 'phone': '13800000005', 'area': '丹东东港'},
        {'username': 'farmer006', 'password': '123456', 'role': 'farmer', 'name': '赵水产', 'phone': '13800000006', 'area': '丹东东港'},
        {'username': 'farmer007', 'password': '123456', 'role': 'farmer', 'name': '孙养殖', 'phone': '13800000007', 'area': '丹东东港'},
        {'username': 'farmer008', 'password': '123456', 'role': 'farmer', 'name': '周海产', 'phone': '13800000008', 'area': '丹东东港'},
        {'username': 'farmer009', 'password': '123456', 'role': 'farmer', 'name': '吴滩涂', 'phone': '13800000009', 'area': '丹东东港'},
        # 合作社账号
        {'username': 'coop001', 'password': '123456', 'role': 'cooperative', 'name': '东港滩涂合作社', 'phone': '13900000001', 'area': '丹东东港'},
        # 企业账号
        {'username': 'ent001', 'password': '123456', 'role': 'enterprise', 'name': '辽贝预制菜有限公司', 'phone': '13700000001', 'area': '沈阳'},
        {'username': 'ent002', 'password': '123456', 'role': 'enterprise', 'name': '大连海鲜连锁', 'phone': '13700000002', 'area': '大连'},
        # 监管账号
        {'username': 'reg001', 'password': '123456', 'role': 'regulator', 'name': '丹东渔业监管局', 'phone': '13600000001', 'area': '丹东'},
        {'username': 'reg002', 'password': '123456', 'role': 'regulator', 'name': '盘锦渔业监管局', 'phone': '13600000002', 'area': '盘锦'},
    ]
    
    for u_data in users:
        user = User(
            username=u_data['username'],
            password_hash=generate_password_hash(u_data['password']),
            role=u_data['role'],
            real_name=u_data['name'],
            phone=u_data['phone'],
            area=u_data['area']
        )
        db.session.add(user)
    
    db.session.flush()
    
    # 创建滩涂点位（真实辽宁沿海坐标）
    flats = [
        # 丹东市沿海 - farmer001 (id=1)
        {'name': '东港1号滩涂', 'area': 50, 'latitude': 39.95, 'longitude': 124.15, 'farmer_id': 1, 'status': 'normal'},
        {'name': '东港2号滩涂', 'area': 80, 'latitude': 39.92, 'longitude': 124.18, 'farmer_id': 1, 'status': 'normal'},
        {'name': '东港3号滩涂', 'area': 65, 'latitude': 39.98, 'longitude': 124.10, 'farmer_id': 1, 'status': 'normal'},
        # 营口市盖州沿海 - farmer002 (id=2)
        {'name': '盖州1号滩涂', 'area': 60, 'latitude': 40.25, 'longitude': 122.38, 'farmer_id': 2, 'status': 'normal'},
        {'name': '盖州2号滩涂', 'area': 45, 'latitude': 40.28, 'longitude': 122.35, 'farmer_id': 2, 'status': 'warning'},
        {'name': '鲅鱼圈滩涂', 'area': 55, 'latitude': 40.22, 'longitude': 122.12, 'farmer_id': 2, 'status': 'normal'},
        # 丹东凤城地区 - farmer003 (id=3)
        {'name': '凤城1号滩涂', 'area': 100, 'latitude': 40.45, 'longitude': 123.95, 'farmer_id': 3, 'status': 'normal'},
        {'name': '凤城2号滩涂', 'area': 75, 'latitude': 40.42, 'longitude': 123.92, 'farmer_id': 3, 'status': 'normal'},
        # 盘锦市沿海
        {'name': '盘锦1号滩涂', 'area': 90, 'latitude': 40.72, 'longitude': 122.07, 'farmer_id': 3, 'status': 'normal'},
        {'name': '盘锦2号滩涂', 'area': 70, 'latitude': 40.75, 'longitude': 122.10, 'farmer_id': 1, 'status': 'normal'},
        # 锦州沿海
        {'name': '锦州1号滩涂', 'area': 85, 'latitude': 40.95, 'longitude': 121.12, 'farmer_id': 2, 'status': 'warning'},
        # 葫芦岛沿海
        {'name': '葫芦岛滩涂', 'area': 40, 'latitude': 40.72, 'longitude': 120.84, 'farmer_id': 3, 'status': 'normal'},
        # 新增丹东东港滩涂 - 新社员
        {'name': '东港4号滩涂', 'area': 55, 'latitude': 39.90, 'longitude': 124.20, 'farmer_id': 4, 'status': 'normal'},
        {'name': '东港5号滩涂', 'area': 70, 'latitude': 39.88, 'longitude': 124.22, 'farmer_id': 4, 'status': 'normal'},
        {'name': '东港6号滩涂', 'area': 45, 'latitude': 39.93, 'longitude': 124.08, 'farmer_id': 5, 'status': 'normal'},
        {'name': '东港7号滩涂', 'area': 60, 'latitude': 39.87, 'longitude': 124.25, 'farmer_id': 5, 'status': 'warning'},
        {'name': '东港8号滩涂', 'area': 80, 'latitude': 39.96, 'longitude': 124.12, 'farmer_id': 6, 'status': 'normal'},
        {'name': '东港9号滩涂', 'area': 50, 'latitude': 39.91, 'longitude': 124.16, 'farmer_id': 6, 'status': 'normal'},
        {'name': '东港10号滩涂', 'area': 65, 'latitude': 39.89, 'longitude': 124.19, 'farmer_id': 7, 'status': 'normal'},
        {'name': '东港11号滩涂', 'area': 40, 'latitude': 39.94, 'longitude': 124.13, 'farmer_id': 7, 'status': 'normal'},
        {'name': '东港12号滩涂', 'area': 75, 'latitude': 39.86, 'longitude': 124.21, 'farmer_id': 8, 'status': 'normal'},
        {'name': '东港13号滩涂', 'area': 55, 'latitude': 39.97, 'longitude': 124.09, 'farmer_id': 8, 'status': 'normal'},
        {'name': '东港14号滩涂', 'area': 60, 'latitude': 39.85, 'longitude': 124.17, 'farmer_id': 9, 'status': 'normal'},
        {'name': '东港15号滩涂', 'area': 45, 'latitude': 39.92, 'longitude': 124.14, 'farmer_id': 9, 'status': 'normal'},
    ]
    
    for f_data in flats:
        flat = TidalFlat(**f_data)
        db.session.add(flat)
    
    db.session.flush()
    
    import random
    now = datetime.datetime.now()
    
    # 创建硬件设备（含租赁信息）
    devices = [
        {'device_id': 'HW001', 'model': 'LC-Sensor-A', 'flat_id': 1, 'status': 'online', 'battery': 85,
         'rental_start': now - datetime.timedelta(days=120), 'rental_end': now + datetime.timedelta(days=245), 'rental_fee': 1200},
        {'device_id': 'HW002', 'model': 'LC-Sensor-A', 'flat_id': 1, 'status': 'online', 'battery': 72,
         'rental_start': now - datetime.timedelta(days=90), 'rental_end': now + datetime.timedelta(days=275), 'rental_fee': 1200},
        {'device_id': 'HW003', 'model': 'LC-Sensor-B', 'flat_id': 2, 'status': 'online', 'battery': 90,
         'rental_start': now - datetime.timedelta(days=60), 'rental_end': now + datetime.timedelta(days=305), 'rental_fee': 1500},
        {'device_id': 'HW004', 'model': 'LC-Sensor-A', 'flat_id': 3, 'status': 'offline', 'battery': 15,
         'rental_start': now - datetime.timedelta(days=200), 'rental_end': now - datetime.timedelta(days=5), 'rental_fee': 1200},
        {'device_id': 'HW005', 'model': 'LC-Sensor-B', 'flat_id': 4, 'status': 'online', 'battery': 68,
         'rental_start': now - datetime.timedelta(days=30), 'rental_end': now + datetime.timedelta(days=335), 'rental_fee': 1500},
        {'device_id': 'HW006', 'model': 'LC-Sensor-A', 'flat_id': 5, 'status': 'online', 'battery': 88,
         'rental_start': now - datetime.timedelta(days=45), 'rental_end': now + datetime.timedelta(days=320), 'rental_fee': 1000},
        {'device_id': 'HW007', 'model': 'LC-Sensor-A', 'flat_id': 6, 'status': 'fault', 'battery': 45,
         'rental_start': now - datetime.timedelta(days=75), 'rental_end': now + datetime.timedelta(days=290), 'rental_fee': 1000},
    ]
    
    for d_data in devices:
        device = HardwareDevice(
            device_id=d_data['device_id'],
            model=d_data['model'],
            flat_id=d_data['flat_id'],
            status=d_data['status'],
            battery_level=d_data['battery'],
            rental_start=d_data.get('rental_start'),
            rental_end=d_data.get('rental_end'),
            rental_fee=d_data.get('rental_fee'),
            last_sync=datetime.datetime.now() - datetime.timedelta(hours=random.randint(0, 6))
        )
        db.session.add(device)
    
    db.session.flush()
    
    # 创建水质数据（180天历史 + 近7天每2小时1条，更丰富的数据）
    # 辽宁贝类养殖真实水质参数
    # 数据来源：
    #   - 2024年辽宁省海洋生态预警监测公报（辽宁省自然资源厅）
    #   - 2024年北海区海洋生态预警监测公报（自然资源部北海局）
    #   - 大连栉孔扇贝农产品地理标志质量控制技术规范（农业农村部）
    #   - GB 11607-89 渔业水质标准
    flat_baselines = {
        # 东港1号滩涂 - 位于丹东东港，黄海北部
        1: {'temp_base': 12, 'salt_base': 31, 'oxy_base': 6.5, 'ph_base': 8.0},
        # 东港2号滩涂 - 位于丹东东港，靠近鸭绿江入海口（低盐区）
        2: {'temp_base': 11, 'salt_base': 29, 'oxy_base': 6.0, 'ph_base': 8.1},
        # 东港3号滩涂 - 位于丹东东港，水深较深
        3: {'temp_base': 10, 'salt_base': 31, 'oxy_base': 7.0, 'ph_base': 7.9},
        # 盘锦1号滩涂 - 位于盘锦，辽河三角洲（辽河口低盐区）
        4: {'temp_base': 13, 'salt_base': 27, 'oxy_base': 5.5, 'ph_base': 8.2},
        # 盘锦2号滩涂 - 位于盘锦，盐碱地滩涂
        5: {'temp_base': 12, 'salt_base': 31, 'oxy_base': 6.8, 'ph_base': 7.8},
        # 盖州滩涂 - 位于营口盖州
        6: {'temp_base': 11, 'salt_base': 30, 'oxy_base': 6.2, 'ph_base': 8.0},
    }

    def get_day_of_year(days_ago):
        """获取距今天数前对应的年内日序号"""
        return (now - datetime.timedelta(days=days_ago)).timetuple().tm_yday

    def get_seasonal_temp(base_temp, day_of_year):
        """水温季节变化模型（辽宁海域）
        春季3-5月：5-15℃，夏季6-8月：18-26℃，秋季9-11月：8-18℃，冬季12-2月：0-6℃
        来源：大连栉孔扇贝地理标志规范、辽宁省海洋生态预警监测公报"""
        if 60 <= day_of_year <= 150:  # 春季 (3-5月)
            return base_temp - 5 + (day_of_year - 60) * 0.1
        elif 151 <= day_of_year <= 240:  # 夏季 (6-8月)
            return base_temp + 6 - (day_of_year - 151) * 0.05
        elif 241 <= day_of_year <= 330:  # 秋季 (9-11月)
            return base_temp - 3 - (day_of_year - 241) * 0.08
        else:  # 冬季 (12-2月)
            return base_temp - 8

    def get_seasonal_salinity(base_salt, day_of_year):
        """盐度季节变化模型（辽宁近岸海域）
        夏季降雨多、河流入海量大 → 盐度偏低2-4‰
        冬季干燥少雨、蒸发强 → 盐度偏高1-2‰
        来源：辽宁省海洋生态预警监测公报（低盐区主要在辽河口，夏季盐度更低）"""
        if 60 <= day_of_year <= 150:  # 春季 - 逐渐降低
            return base_salt - (day_of_year - 60) * 0.02
        elif 151 <= day_of_year <= 240:  # 夏季 - 最低（雨季、河流入海）
            return base_salt - 3 + (day_of_year - 151) * 0.01
        elif 241 <= day_of_year <= 330:  # 秋季 - 逐渐回升
            return base_salt - 1 + (day_of_year - 241) * 0.02
        else:  # 冬季 - 最高（干燥少雨）
            return base_salt + 1.5

    def get_seasonal_oxygen(base_oxy, temp):
        """溶解氧季节变化模型（与水温反相关）
        水温越高，氧气溶解度越低；水温越低，氧气溶解度越高
        物理规律：温度每升高1℃，溶解氧约降低0.2-0.3 mg/L
        来源：2024年辽宁省海洋生态预警监测公报（夏季2.79-9.97 mg/L）"""
        # 以15℃为基准温度，计算温度偏差对溶氧的影响
        temp_diff = temp - 15
        return base_oxy - temp_diff * 0.25

    # 极端天气事件模拟（影响水质的重大事件）
    # 数据来源：辽宁省气象灾害公报、辽宁省海洋生态预警监测公报
    extreme_events = [
        # 台风"海棠"影响（7月下旬，距今天约15天）
        {'days_ago': 15, 'duration': 3, 'type': 'typhoon',
         'temp_drop': 4, 'salt_drop': 6, 'oxy_drop': 3, 'ph_change': -0.5,
         'affected_flats': [1, 2, 3]},  # 东港地区受台风影响
        # 暴雨洪涝（6月中旬，距今天约45天）
        {'days_ago': 45, 'duration': 2, 'type': 'flood',
         'temp_drop': 2, 'salt_drop': 8, 'oxy_drop': 2, 'ph_change': -0.8,
         'affected_flats': [4, 5]},  # 盘锦辽河三角洲受洪水影响
        # 冬季寒潮（12月下旬，距今天约150天）
        {'days_ago': 150, 'duration': 5, 'type': 'cold_wave',
         'temp_drop': 10, 'salt_change': 1, 'oxy_rise': 2, 'ph_change': 0.1,
         'affected_flats': [1, 2, 3, 4, 5, 6]},  # 全省受寒潮影响
        # 赤潮事件（8月上旬，距今天约5天）
        {'days_ago': 5, 'duration': 4, 'type': 'red_tide',
         'temp_rise': 2, 'salt_drop': 1, 'oxy_drop': 4, 'ph_change': 0.3,
         'affected_flats': [3]},  # 东港3号滩涂发生赤潮
        # 春季大风（4月中旬，距今天约110天）
        {'days_ago': 110, 'duration': 2, 'type': 'storm',
         'temp_drop': 3, 'salt_change': 0, 'oxy_rise': 1.5, 'ph_change': 0,
         'affected_flats': [1, 2]},  # 东港地区大风
    ]

    def get_weather_impact(day_ago, flat_id, param):
        """获取某一天某个滩涂某个参数受极端天气的影响值"""
        for event in extreme_events:
            if event['days_ago'] <= day_ago <= event['days_ago'] + event['duration']:
                if flat_id in event['affected_flats']:
                    if param == 'temp':
                        if event['type'] == 'cold_wave':
                            return -event['temp_drop']
                        elif event['type'] in ['typhoon', 'storm', 'flood']:
                            return -event['temp_drop']
                        elif event['type'] == 'red_tide':
                            return event.get('temp_rise', 0)
                    elif param == 'salt':
                        return event.get('salt_drop', 0) + event.get('salt_change', 0)
                    elif param == 'oxy':
                        if event.get('oxy_drop'):
                            return -event['oxy_drop']
                        elif event.get('oxy_rise'):
                            return event['oxy_rise']
                        return 0
                    elif param == 'ph':
                        return event.get('ph_change', 0)
        return 0

    for flat_id in range(1, 7):
        base = flat_baselines[flat_id]
        # 180天日数据（更丰富的历史）
        for day in range(180, 0, -1):
            ts = now - datetime.timedelta(days=day)
            day_of_year = get_day_of_year(day)
            seasonal_temp = get_seasonal_temp(base['temp_base'], day_of_year)
            seasonal_salt = get_seasonal_salinity(base['salt_base'], day_of_year)
            seasonal_oxy = get_seasonal_oxygen(base['oxy_base'], seasonal_temp)
            # 添加极端天气影响
            weather_temp = get_weather_impact(day, flat_id, 'temp')
            weather_salt = get_weather_impact(day, flat_id, 'salt')
            weather_oxy = get_weather_impact(day, flat_id, 'oxy')
            weather_ph = get_weather_impact(day, flat_id, 'ph')
            data = WaterQualityData(
                flat_id=flat_id,
                timestamp=ts,
                temperature=round(seasonal_temp + weather_temp + random.uniform(-1.0, 1.0), 1),
                salinity=round(max(15, seasonal_salt + weather_salt + random.uniform(-0.8, 0.8)), 1),
                dissolved_oxygen=round(max(1.5, seasonal_oxy + weather_oxy + random.uniform(-0.8, 0.8)), 1),
                ph=round(min(9.5, max(6.5, base['ph_base'] + weather_ph + random.uniform(-0.2, 0.2))), 2)
            )
            db.session.add(data)
        # 近7天每2小时1条（更密集的高频数据，84条）
        for hour in range(7*24, 0, -2):
            ts = now - datetime.timedelta(hours=hour)
            days_ago = hour / 24
            day_of_year = get_day_of_year(days_ago)
            seasonal_temp = get_seasonal_temp(base['temp_base'], day_of_year)
            seasonal_salt = get_seasonal_salinity(base['salt_base'], day_of_year)
            seasonal_oxy = get_seasonal_oxygen(base['oxy_base'], seasonal_temp)
            # 添加极端天气影响
            weather_temp = get_weather_impact(days_ago, flat_id, 'temp')
            weather_salt = get_weather_impact(days_ago, flat_id, 'salt')
            weather_oxy = get_weather_impact(days_ago, flat_id, 'oxy')
            weather_ph = get_weather_impact(days_ago, flat_id, 'ph')
            # 近岸日变化：白天升温、夜间降温
            hour_of_day = ts.hour
            if 6 <= hour_of_day <= 14:
                temp_offset = (hour_of_day - 6) * 0.3
            else:
                temp_offset = -0.5
            # 溶解氧日变化：白天光合作用产氧，夜间呼吸耗氧
            if 8 <= hour_of_day <= 16:
                oxy_offset = (hour_of_day - 8) * 0.2
            else:
                oxy_offset = -0.8
            data = WaterQualityData(
                flat_id=flat_id,
                timestamp=ts,
                temperature=round(seasonal_temp + weather_temp + temp_offset + random.uniform(-0.5, 0.5), 1),
                salinity=round(max(15, seasonal_salt + weather_salt + random.uniform(-0.5, 0.5)), 1),
                dissolved_oxygen=round(max(1.5, seasonal_oxy + weather_oxy + oxy_offset + random.uniform(-0.3, 0.3)), 1),
                ph=round(min(9.5, max(6.5, base['ph_base'] + weather_ph + random.uniform(-0.15, 0.15))), 2)
            )
            db.session.add(data)
    
    # 创建预警记录（20条，覆盖三级告警和历史事件）
    alerts = [
        # 近期极端天气事件告警
        {'flat_id': 3, 'level': 'red', 'type': 'red_tide', 'message': '赤潮预警！溶解氧骤降至2.1mg/L，贝类面临缺氧风险', 'resolved': False, 'hours_ago': 120},
        {'flat_id': 1, 'level': 'orange', 'type': 'typhoon', 'message': '台风"海棠"影响！盐度骤降6‰，溶氧减少3mg/L', 'resolved': True, 'hours_ago': 360},
        {'flat_id': 2, 'level': 'orange', 'type': 'typhoon', 'message': '台风影响持续，建议暂停养殖活动', 'resolved': True, 'hours_ago': 348},
        {'flat_id': 4, 'level': 'red', 'type': 'flood', 'message': '辽河三角洲洪水预警！盐度降至19‰以下', 'resolved': True, 'hours_ago': 1080},
        {'flat_id': 5, 'level': 'orange', 'type': 'flood', 'message': '洪水影响中，pH值降至7.2，监测水体恢复', 'resolved': True, 'hours_ago': 1068},
        {'flat_id': 1, 'level': 'blue', 'type': 'storm', 'message': '春季大风，增氧设备运行正常', 'resolved': True, 'hours_ago': 2640},
        # 常规告警
        {'flat_id': 1, 'level': 'blue', 'type': 'temperature', 'message': '水温轻微波动，建议关注', 'resolved': True, 'hours_ago': 240},
        {'flat_id': 2, 'level': 'blue', 'type': 'salinity', 'message': '盐度轻微异常，建议持续监测', 'resolved': True, 'hours_ago': 72},
        {'flat_id': 3, 'level': 'blue', 'type': 'ph', 'message': 'pH值轻微偏高（8.4），建议关注', 'resolved': True, 'hours_ago': 96},
        {'flat_id': 4, 'level': 'orange', 'type': 'oxygen', 'message': '溶解氧偏低（3.8mg/L），需及时增氧', 'resolved': False, 'hours_ago': 12},
        {'flat_id': 6, 'level': 'blue', 'type': 'salinity', 'message': '盐度轻微偏高，受潮汐影响', 'resolved': True, 'hours_ago': 48},
        {'flat_id': 3, 'level': 'blue', 'type': 'oxygen', 'message': '溶解氧轻微波动，属正常范围', 'resolved': True, 'hours_ago': 144},
        # 新增预警记录
        {'flat_id': 2, 'level': 'blue', 'type': 'temperature', 'message': '水温日变化较大，夜间降温明显', 'resolved': True, 'hours_ago': 36},
        {'flat_id': 5, 'level': 'orange', 'type': 'oxygen', 'message': '高温天气溶解氧下降，建议开启增氧', 'resolved': True, 'hours_ago': 48},
        {'flat_id': 1, 'level': 'blue', 'type': 'salinity', 'message': '雨后盐度略有下降，属正常范围', 'resolved': True, 'hours_ago': 72},
        {'flat_id': 4, 'level': 'blue', 'type': 'ph', 'message': 'pH值偏低（7.6），建议监测', 'resolved': False, 'hours_ago': 24},
        {'flat_id': 6, 'level': 'orange', 'type': 'temperature', 'message': '水温超过25℃，贝类活动减少', 'resolved': True, 'hours_ago': 60},
        {'flat_id': 2, 'level': 'blue', 'type': 'oxygen', 'message': '溶氧日间变化正常，光合作用增氧明显', 'resolved': True, 'hours_ago': 168},
        {'flat_id': 5, 'level': 'red', 'type': 'cold_wave', 'message': '寒潮预警！气温骤降10℃，注意保温', 'resolved': True, 'hours_ago': 720},
        {'flat_id': 1, 'level': 'blue', 'type': 'ph', 'message': 'pH值稳定在正常范围', 'resolved': True, 'hours_ago': 200},
    ]
    
    for a_data in alerts:
        alert = AlertRecord(
            flat_id=a_data['flat_id'],
            level=a_data['level'],
            alert_type=a_data['type'],
            message=a_data['message'],
            timestamp=now - datetime.timedelta(hours=a_data['hours_ago']),
            resolved=a_data['resolved'],
            resolved_at=now - datetime.timedelta(hours=a_data['hours_ago'] - 24) if a_data['resolved'] else None
        )
        db.session.add(alert)
    
    # 创建溯源节点（20条，覆盖所有滩涂和产品类型）
    trace_nodes = [
        {'product_name': '丹东野生缢蛏', 'batch_code': 'DDYZQ20260501', 'farmer_id': 1, 'status': 'completed',
         'seed_source': '丹东东港苗种场', 'seed_date': now - datetime.timedelta(days=150),
         'harvest_date': now - datetime.timedelta(days=20), 'quality_check': '合格，重金属检测达标',
         'enterprise_id': 4, 'processing_info': '清洗分级→速冻→真空包装',
         'blockchain_hash': hashlib.sha256(f'batch1{now}'.encode()).hexdigest()[:16]},
        {'product_name': '盘锦文蛤', 'batch_code': 'PJWG20260502', 'farmer_id': 2, 'status': 'processing',
         'seed_source': '盘锦苗种场', 'seed_date': now - datetime.timedelta(days=100),
         'quality_check': '待检测',
         'blockchain_hash': hashlib.sha256(f'batch2{now}'.encode()).hexdigest()[:16]},
        {'product_name': '凤城蚬子', 'batch_code': 'FCXZ20260503', 'farmer_id': 3, 'status': 'completed',
         'seed_source': '凤城苗种场', 'seed_date': now - datetime.timedelta(days=130),
         'harvest_date': now - datetime.timedelta(days=10), 'quality_check': '优质，无药残',
         'enterprise_id': 5, 'processing_info': '鲜活分拣→冷链运输',
         'blockchain_hash': hashlib.sha256(f'batch3{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港野生文蛤', 'batch_code': 'DGWG20260601', 'farmer_id': 1, 'status': 'completed',
         'seed_source': '东港苗种场', 'seed_date': now - datetime.timedelta(days=120),
         'harvest_date': now - datetime.timedelta(days=15), 'quality_check': '合格',
         'enterprise_id': 4, 'processing_info': '清洗分级、速冻加工',
         'blockchain_hash': hashlib.sha256(f'batch4{now}'.encode()).hexdigest()[:16]},
        {'product_name': '盖州蚬子', 'batch_code': 'GZXZ20260602', 'farmer_id': 2, 'status': 'processing',
         'seed_source': '盖州苗种场', 'seed_date': now - datetime.timedelta(days=90),
         'quality_check': '待定',
         'blockchain_hash': hashlib.sha256(f'batch5{now}'.encode()).hexdigest()[:16]},
        {'product_name': '凤城扇贝', 'batch_code': 'FCSB20260603', 'farmer_id': 3, 'status': 'completed',
         'seed_source': '凤城苗种场', 'seed_date': now - datetime.timedelta(days=160),
         'harvest_date': now - datetime.timedelta(days=5), 'quality_check': '优质',
         'enterprise_id': 5, 'processing_info': '冷冻保鲜、礼盒包装',
         'blockchain_hash': hashlib.sha256(f'batch6{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港缢蛏（礼盒装）', 'batch_code': 'DGYZQ20260701', 'farmer_id': 1, 'status': 'completed',
         'seed_source': '丹东苗种场', 'seed_date': now - datetime.timedelta(days=80),
         'harvest_date': now - datetime.timedelta(days=3), 'quality_check': '合格，规格均匀',
         'enterprise_id': 4, 'processing_info': '精选分级→泡沫箱冰鲜包装',
         'blockchain_hash': hashlib.sha256(f'batch7{now}'.encode()).hexdigest()[:16]},
        {'product_name': '盖州毛蚶', 'batch_code': 'GZMH20260702', 'farmer_id': 2, 'status': 'processing',
         'seed_source': '盖州本地苗种', 'seed_date': now - datetime.timedelta(days=70),
         'quality_check': '待检测',
         'blockchain_hash': hashlib.sha256(f'batch8{now}'.encode()).hexdigest()[:16]},
        # 新增溯源记录
        {'product_name': '盘锦缢蛏', 'batch_code': 'PJYZQ20260504', 'farmer_id': 2, 'status': 'completed',
         'seed_source': '盘锦本地苗种', 'seed_date': now - datetime.timedelta(days=140),
         'harvest_date': now - datetime.timedelta(days=25), 'quality_check': '合格',
         'enterprise_id': 4, 'processing_info': '清洗→速冻→散装',
         'blockchain_hash': hashlib.sha256(f'batch9{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港毛蚶', 'batch_code': 'DGMH20260505', 'farmer_id': 1, 'status': 'completed',
         'seed_source': '东港苗种场', 'seed_date': now - datetime.timedelta(days=110),
         'harvest_date': now - datetime.timedelta(days=18), 'quality_check': '优质',
         'enterprise_id': 5, 'processing_info': '鲜活分拣、真空包装',
         'blockchain_hash': hashlib.sha256(f'batch10{now}'.encode()).hexdigest()[:16]},
        {'product_name': '凤城文蛤', 'batch_code': 'FCWG20260506', 'farmer_id': 3, 'status': 'processing',
         'seed_source': '凤城苗种场', 'seed_date': now - datetime.timedelta(days=95),
         'quality_check': '检测中',
         'blockchain_hash': hashlib.sha256(f'batch11{now}'.encode()).hexdigest()[:16]},
        {'product_name': '盘锦扇贝', 'batch_code': 'PJSB20260604', 'farmer_id': 2, 'status': 'completed',
         'seed_source': '丹东扇贝苗种场', 'seed_date': now - datetime.timedelta(days=170),
         'harvest_date': now - datetime.timedelta(days=8), 'quality_check': '合格',
         'enterprise_id': 4, 'processing_info': '冷冻保鲜',
         'blockchain_hash': hashlib.sha256(f'batch12{now}'.encode()).hexdigest()[:16]},
        {'product_name': '盖州缢蛏', 'batch_code': 'GZYZQ20260605', 'farmer_id': 2, 'status': 'completed',
         'seed_source': '盖州苗种场', 'seed_date': now - datetime.timedelta(days=135),
         'harvest_date': now - datetime.timedelta(days=12), 'quality_check': '合格',
         'enterprise_id': 5, 'processing_info': '清洗分级→冰鲜',
         'blockchain_hash': hashlib.sha256(f'batch13{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港蚬子', 'batch_code': 'DGXZ20260606', 'farmer_id': 1, 'status': 'processing',
         'seed_source': '东港苗种场', 'seed_date': now - datetime.timedelta(days=85),
         'quality_check': '待检测',
         'blockchain_hash': hashlib.sha256(f'batch14{now}'.encode()).hexdigest()[:16]},
        {'product_name': '凤城毛蚶（礼盒装）', 'batch_code': 'FCMH20260703', 'farmer_id': 3, 'status': 'completed',
         'seed_source': '凤城本地苗种', 'seed_date': now - datetime.timedelta(days=95),
         'harvest_date': now - datetime.timedelta(days=6), 'quality_check': '优质，规格大',
         'enterprise_id': 5, 'processing_info': '精选分级→礼盒包装',
         'blockchain_hash': hashlib.sha256(f'batch15{now}'.encode()).hexdigest()[:16]},
        {'product_name': '盘锦蚬子', 'batch_code': 'PJXZ20260704', 'farmer_id': 2, 'status': 'processing',
         'seed_source': '盘锦苗种场', 'seed_date': now - datetime.timedelta(days=65),
         'quality_check': '生长期',
         'blockchain_hash': hashlib.sha256(f'batch16{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港扇贝', 'batch_code': 'DGSB20260705', 'farmer_id': 1, 'status': 'completed',
         'seed_source': '东港深水区苗种', 'seed_date': now - datetime.timedelta(days=145),
         'harvest_date': now - datetime.timedelta(days=4), 'quality_check': '优质',
         'enterprise_id': 4, 'processing_info': '冷冻→礼盒包装',
         'blockchain_hash': hashlib.sha256(f'batch17{now}'.encode()).hexdigest()[:16]},
        {'product_name': '盖州文蛤', 'batch_code': 'GZWG20260706', 'farmer_id': 2, 'status': 'completed',
         'seed_source': '盖州苗种场', 'seed_date': now - datetime.timedelta(days=105),
         'harvest_date': now - datetime.timedelta(days=15), 'quality_check': '合格',
         'enterprise_id': 5, 'processing_info': '鲜活分拣',
         'blockchain_hash': hashlib.sha256(f'batch18{now}'.encode()).hexdigest()[:16]},
        {'product_name': '凤城缢蛏', 'batch_code': 'FCYZQ20260707', 'farmer_id': 3, 'status': 'processing',
         'seed_source': '凤城苗种场', 'seed_date': now - datetime.timedelta(days=75),
         'quality_check': '正常生长',
         'blockchain_hash': hashlib.sha256(f'batch19{now}'.encode()).hexdigest()[:16]},
        {'product_name': '盘锦毛蚶', 'batch_code': 'PJMH20260708', 'farmer_id': 2, 'status': 'completed',
         'seed_source': '盘锦本地苗种', 'seed_date': now - datetime.timedelta(days=125),
         'harvest_date': now - datetime.timedelta(days=20), 'quality_check': '合格',
         'enterprise_id': 4, 'processing_info': '清洗→速冻',
         'blockchain_hash': hashlib.sha256(f'batch20{now}'.encode()).hexdigest()[:16]},
        # 新增社员溯源记录
        {'product_name': '东港缢蛏', 'batch_code': 'DGYZQ20260801', 'farmer_id': 4, 'status': 'completed',
         'seed_source': '东港苗种场', 'seed_date': now - datetime.timedelta(days=90),
         'harvest_date': now - datetime.timedelta(days=10), 'quality_check': '合格',
         'enterprise_id': 4, 'processing_info': '清洗分级→速冻',
         'blockchain_hash': hashlib.sha256(f'batch21{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港文蛤', 'batch_code': 'DGWG20260802', 'farmer_id': 4, 'status': 'processing',
         'seed_source': '东港本地苗种', 'seed_date': now - datetime.timedelta(days=60),
         'quality_check': '生长中',
         'blockchain_hash': hashlib.sha256(f'batch22{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港毛蚶', 'batch_code': 'DGMH20260803', 'farmer_id': 5, 'status': 'completed',
         'seed_source': '东港苗种场', 'seed_date': now - datetime.timedelta(days=110),
         'harvest_date': now - datetime.timedelta(days=15), 'quality_check': '优质',
         'enterprise_id': 5, 'processing_info': '鲜活分拣→真空包装',
         'blockchain_hash': hashlib.sha256(f'batch23{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港扇贝', 'batch_code': 'DGSB20260804', 'farmer_id': 5, 'status': 'completed',
         'seed_source': '东港深水区苗种', 'seed_date': now - datetime.timedelta(days=130),
         'harvest_date': now - datetime.timedelta(days=8), 'quality_check': '合格',
         'enterprise_id': 4, 'processing_info': '冷冻→礼盒包装',
         'blockchain_hash': hashlib.sha256(f'batch24{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港蚬子', 'batch_code': 'DGXZ20260805', 'farmer_id': 6, 'status': 'processing',
         'seed_source': '东港苗种场', 'seed_date': now - datetime.timedelta(days=70),
         'quality_check': '待检测',
         'blockchain_hash': hashlib.sha256(f'batch25{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港缢蛏（礼盒）', 'batch_code': 'DGYZQ20260806', 'farmer_id': 6, 'status': 'completed',
         'seed_source': '丹东苗种场', 'seed_date': now - datetime.timedelta(days=100),
         'harvest_date': now - datetime.timedelta(days=5), 'quality_check': '优质，规格均匀',
         'enterprise_id': 4, 'processing_info': '精选分级→礼盒包装',
         'blockchain_hash': hashlib.sha256(f'batch26{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港文蛤', 'batch_code': 'DGWG20260807', 'farmer_id': 7, 'status': 'completed',
         'seed_source': '东港苗种场', 'seed_date': now - datetime.timedelta(days=85),
         'harvest_date': now - datetime.timedelta(days=12), 'quality_check': '合格',
         'enterprise_id': 5, 'processing_info': '鲜活分拣',
         'blockchain_hash': hashlib.sha256(f'batch27{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港毛蚶', 'batch_code': 'DGMH20260808', 'farmer_id': 7, 'status': 'processing',
         'seed_source': '东港本地苗种', 'seed_date': now - datetime.timedelta(days=55),
         'quality_check': '生长中',
         'blockchain_hash': hashlib.sha256(f'batch28{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港扇贝', 'batch_code': 'DGSB20260809', 'farmer_id': 8, 'status': 'completed',
         'seed_source': '东港深水区苗种', 'seed_date': now - datetime.timedelta(days=140),
         'harvest_date': now - datetime.timedelta(days=3), 'quality_check': '优质',
         'enterprise_id': 4, 'processing_info': '冷冻保鲜',
         'blockchain_hash': hashlib.sha256(f'batch29{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港蚬子', 'batch_code': 'DGXZ20260810', 'farmer_id': 8, 'status': 'completed',
         'seed_source': '东港苗种场', 'seed_date': now - datetime.timedelta(days=95),
         'harvest_date': now - datetime.timedelta(days=20), 'quality_check': '合格',
         'enterprise_id': 5, 'processing_info': '清洗分级→冰鲜',
         'blockchain_hash': hashlib.sha256(f'batch30{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港缢蛏', 'batch_code': 'DGYZQ20260811', 'farmer_id': 9, 'status': 'processing',
         'seed_source': '东港苗种场', 'seed_date': now - datetime.timedelta(days=65),
         'quality_check': '生长中',
         'blockchain_hash': hashlib.sha256(f'batch31{now}'.encode()).hexdigest()[:16]},
        {'product_name': '东港文蛤（礼盒）', 'batch_code': 'DGWG20260812', 'farmer_id': 9, 'status': 'completed',
         'seed_source': '东港本地苗种', 'seed_date': now - datetime.timedelta(days=120),
         'harvest_date': now - datetime.timedelta(days=7), 'quality_check': '优质',
         'enterprise_id': 4, 'processing_info': '精选分级→礼盒包装',
         'blockchain_hash': hashlib.sha256(f'batch32{now}'.encode()).hexdigest()[:16]},
    ]
    
    for t_data in trace_nodes:
        node = TraceabilityNode(
            product_name=t_data['product_name'],
            batch_code=t_data['batch_code'],
            product_category='贝类',
            farmer_id=t_data['farmer_id'],
            status=t_data['status'],
            seed_source=t_data.get('seed_source'),
            seed_date=t_data.get('seed_date'),
            harvest_date=t_data.get('harvest_date'),
            quality_check=t_data.get('quality_check'),
            enterprise_id=t_data.get('enterprise_id'),
            processing_info=t_data.get('processing_info'),
            blockchain_hash=t_data.get('blockchain_hash'),
            created_at=now - datetime.timedelta(days=random.randint(1, 60))
        )
        db.session.add(node)
    
    # 创建农户收益记录（近12个月，更真实的数据）
    farmer_revenue_profiles = {
        1: {'seed': (1500, 3500), 'hardware': (300, 900), 'material': (150, 600), 'sales': (8000, 25000)},
        2: {'seed': (1000, 2800), 'hardware': (200, 700), 'material': (100, 450), 'sales': (6000, 18000)},
        3: {'seed': (2000, 4000), 'hardware': (400, 1000), 'material': (200, 700), 'sales': (10000, 30000)},
    }
    
    for farmer_id in [1, 2, 3]:
        profile = farmer_revenue_profiles[farmer_id]
        for month_offset in range(12, 0, -1):
            month_date = now - datetime.timedelta(days=month_offset * 30)
            # 模拟冬季收入较低、夏季秋季收入较高的季节性
            season_factor = 0.6 if month_date.month in [12, 1, 2, 3] else (1.3 if month_date.month in [7, 8, 9, 10] else 1.0)
            seed_cost = round(random.uniform(*profile['seed']), 2)
            hardware_rental = round(random.uniform(*profile['hardware']), 2)
            material_cost = round(random.uniform(*profile['material']), 2)
            sales = round(random.uniform(*profile['sales']) * season_factor, 2)
            total_cost = seed_cost + hardware_rental + material_cost + round(random.uniform(50, 200), 2)
            net = sales - total_cost
            record = RevenueRecord(
                farmer_id=farmer_id,
                year=month_date.year,
                month=month_date.month,
                seed_cost=seed_cost,
                hardware_rental=hardware_rental,
                material_cost=material_cost,
                other_cost=round(random.uniform(50, 200), 2),
                sales_revenue=sales,
                total_cost=total_cost,
                net_income=net
            )
            db.session.add(record)
    
    # 创建苗种投放记录（18条，覆盖全部滩涂和多个投放周期）
    seedling_records = [
        {'flat_id': 1, 'species': '缢蛏', 'quantity': 50000, 'source': '丹东东港苗种场', 'operator': '张养殖', 'remark': '规格均匀，活力良好'},
        {'flat_id': 1, 'species': '文蛤', 'quantity': 30000, 'source': '东港苗种场', 'operator': '张养殖', 'remark': '附苗率85%'},
        {'flat_id': 1, 'species': '毛蚶', 'quantity': 25000, 'source': '丹东本地苗种', 'operator': '张养殖', 'remark': '补投苗种，密度调整'},
        {'flat_id': 2, 'species': '文蛤', 'quantity': 35000, 'source': '盘锦苗种场', 'operator': '张养殖', 'remark': '本批次苗种质量优良'},
        {'flat_id': 2, 'species': '毛蚶', 'quantity': 20000, 'source': '盘锦本地苗种', 'operator': '张养殖', 'remark': '试养品种'},
        {'flat_id': 2, 'species': '扇贝', 'quantity': 18000, 'source': '丹东扇贝苗种场', 'operator': '张养殖', 'remark': '新增养殖品种试验'},
        {'flat_id': 3, 'species': '蚬子', 'quantity': 40000, 'source': '盖州苗种场', 'operator': '李海产', 'remark': '生长状况良好'},
        {'flat_id': 3, 'species': '文蛤', 'quantity': 22000, 'source': '凤城苗种场', 'operator': '李海产', 'remark': '混养模式，提高滩涂利用率'},
        {'flat_id': 4, 'species': '蚬子', 'quantity': 25000, 'source': '盖州本地苗种', 'operator': '李海产', 'remark': '密度适当降低'},
        {'flat_id': 4, 'species': '缢蛏', 'quantity': 28000, 'source': '盘锦苗种场', 'operator': '李海产', 'remark': '辽河入海口苗种'},
        {'flat_id': 5, 'species': '扇贝', 'quantity': 25000, 'source': '东港苗种场', 'operator': '王滩涂', 'remark': '深海苗种，适应性强'},
        {'flat_id': 5, 'species': '缢蛏', 'quantity': 35000, 'source': '凤城苗种场', 'operator': '王滩涂', 'remark': '混养模式'},
        {'flat_id': 5, 'species': '毛蚶', 'quantity': 20000, 'source': '东港本地苗种', 'operator': '王滩涂', 'remark': '轮休后重新投放'},
        {'flat_id': 6, 'species': '扇贝', 'quantity': 30000, 'source': '凤城苗种场', 'operator': '王滩涂', 'remark': '轮休后首批投放'},
        {'flat_id': 6, 'species': '文蛤', 'quantity': 25000, 'source': '盖州苗种场', 'operator': '王滩涂', 'remark': '生态养殖模式'},
        # 新增历史投放记录
        {'flat_id': 1, 'species': '蚬子', 'quantity': 38000, 'source': '东港苗种场', 'operator': '张养殖', 'remark': '去年批次，生长良好'},
        {'flat_id': 2, 'species': '缢蛏', 'quantity': 32000, 'source': '盘锦本地苗种', 'operator': '张养殖', 'remark': '秋季补投'},
        {'flat_id': 3, 'species': '扇贝', 'quantity': 22000, 'source': '丹东苗种场', 'operator': '李海产', 'remark': '优质苗种'},
    ]
    for s_data in seedling_records:
        record = SeedlingRecord(
            flat_id=s_data['flat_id'],
            species=s_data['species'],
            quantity=s_data['quantity'],
            source=s_data['source'],
            operator=s_data['operator'],
            remark=s_data.get('remark', ''),
            created_at=now - datetime.timedelta(days=random.randint(15, 90))
        )
        db.session.add(record)
    
    # 创建生态轮休规划（含历史和未来）
    ecological_plans = [
        {'flat_id': 1, 'plan_year': now.year, 'plan_phase': 'breeding', 'start_date': now - datetime.timedelta(days=30), 'end_date': now + datetime.timedelta(days=60), 'plan_notes': '当前养殖周期，预计9月收获'},
        {'flat_id': 2, 'plan_year': now.year, 'plan_phase': 'breeding', 'start_date': now - datetime.timedelta(days=20), 'end_date': now + datetime.timedelta(days=70), 'plan_notes': '文蛤养殖期'},
        {'flat_id': 3, 'plan_year': now.year, 'plan_phase': 'resting', 'start_date': now - datetime.timedelta(days=90), 'end_date': now + datetime.timedelta(days=10), 'plan_notes': '休养期，进行生态修复'},
        {'flat_id': 4, 'plan_year': now.year, 'plan_phase': 'breeding', 'start_date': now - datetime.timedelta(days=15), 'end_date': now + datetime.timedelta(days=75), 'plan_notes': '低密度养殖试点'},
        {'flat_id': 5, 'plan_year': now.year, 'plan_phase': 'breeding', 'start_date': now - datetime.timedelta(days=25), 'end_date': now + datetime.timedelta(days=65), 'plan_notes': '贝类+海带生态混养'},
        {'flat_id': 6, 'plan_year': now.year, 'plan_phase': 'resting', 'start_date': now - datetime.timedelta(days=60), 'end_date': now + datetime.timedelta(days=30), 'plan_notes': '三年两养一休-休养年'},
    ]
    for e_data in ecological_plans:
        plan = EcologicalPlan(**e_data)
        db.session.add(plan)
    
    # 创建产销信息（16条，含不同状态和价格）
    market_posts = [
        {'farmer_id': 1, 'product_name': '丹东缢蛏（大规格）', 'product_category': '缢蛏', 'quantity': 2000, 'expected_price': 15.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=30), 'description': '规格均匀，鲜活直供'},
        {'farmer_id': 1, 'product_name': '东港文蛤', 'product_category': '文蛤', 'quantity': 1500, 'expected_price': 12.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=45), 'description': '野生文蛤，壳厚肉肥'},
        {'farmer_id': 2, 'product_name': '盘锦蚬子', 'product_category': '蚬子', 'quantity': 3000, 'expected_price': 8.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=20), 'description': '大批量上市，价格可议'},
        {'farmer_id': 2, 'product_name': '盖州毛蚶', 'product_category': '毛蚶', 'quantity': 1200, 'expected_price': 18.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=60), 'description': '试养品种，品质优良'},
        {'farmer_id': 3, 'product_name': '凤城扇贝', 'product_category': '扇贝', 'quantity': 1000, 'expected_price': 25.0, 'status': 'closed', 'listing_date': now.date() - datetime.timedelta(days=10), 'description': '已售罄'},
        {'farmer_id': 3, 'product_name': '凤城缢蛏', 'product_category': '缢蛏', 'quantity': 1800, 'expected_price': 14.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=15), 'description': '混养缢蛏，口感鲜美'},
        {'farmer_id': 1, 'product_name': '东港毛蚶', 'product_category': '毛蚶', 'quantity': 800, 'expected_price': 20.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=50), 'description': '野生毛蚶，数量有限'},
        {'farmer_id': 3, 'product_name': '凤城扇贝（礼盒装）', 'product_category': '扇贝', 'quantity': 500, 'expected_price': 35.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=25), 'description': '精品礼盒装，适合节假日送礼'},
        # 新增产销信息
        {'farmer_id': 1, 'product_name': '东港蚬子', 'product_category': '蚬子', 'quantity': 2500, 'expected_price': 9.5, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=35), 'description': '鲜活蚬子，现捕现发'},
        {'farmer_id': 2, 'product_name': '盘锦文蛤（中规格）', 'product_category': '文蛤', 'quantity': 2000, 'expected_price': 11.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=40), 'description': '性价比高，适合餐饮采购'},
        {'farmer_id': 3, 'product_name': '凤城毛蚶', 'product_category': '毛蚶', 'quantity': 1000, 'expected_price': 19.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=55), 'description': '高品质毛蚶，直供海鲜市场'},
        {'farmer_id': 1, 'product_name': '丹东野生扇贝', 'product_category': '扇贝', 'quantity': 600, 'expected_price': 28.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=70), 'description': '野生捕捞，限量供应'},
        {'farmer_id': 2, 'product_name': '盖州缢蛏', 'product_category': '缢蛏', 'quantity': 1800, 'expected_price': 13.5, 'status': 'closed', 'listing_date': now.date() - datetime.timedelta(days=5), 'description': '已被预订'},
        {'farmer_id': 3, 'product_name': '凤城蚬子（精品）', 'product_category': '蚬子', 'quantity': 800, 'expected_price': 12.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=42), 'description': '精品蚬子，规格整齐'},
        {'farmer_id': 1, 'product_name': '东港文蛤（礼盒装）', 'product_category': '文蛤', 'quantity': 300, 'expected_price': 45.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=75), 'description': '高端礼盒，送礼佳品'},
        {'farmer_id': 2, 'product_name': '盘锦扇贝', 'product_category': '扇贝', 'quantity': 800, 'expected_price': 22.0, 'status': 'open', 'listing_date': now.date() + datetime.timedelta(days=80), 'description': '人工养殖，规格稳定'},
    ]
    for m_data in market_posts:
        post = TransactionPost(
            farmer_id=m_data['farmer_id'],
            product_name=m_data['product_name'],
            product_category=m_data['product_category'],
            quantity=m_data['quantity'],
            expected_price=m_data['expected_price'],
            status=m_data['status'],
            listing_date=m_data.get('listing_date'),
            description=m_data.get('description', ''),
            created_at=now - datetime.timedelta(days=random.randint(1, 15))
        )
        db.session.add(post)
    
    db.session.flush()
    
    # 创建养殖台账记录（每个滩涂8-12条，覆盖全部类型）
    log_templates = {
        '投喂': ['投喂饵料{0}kg，贝类摄食正常', '投喂配合饲料{0}kg，水温适宜', '投喂藻类饵料{0}kg，贝类活跃', '日常投喂{0}kg，观察摄食情况良好'],
        '消杀': ['使用生石灰消毒，用量{0}kg/亩', '使用漂白粉消毒，全池泼洒', '水体消杀完成，用量正常', '预防性消杀，使用碘制剂'],
        '巡查': ['巡查滩涂，水质正常，未见异常', '巡查发现水位正常，贝类生长良好', '例行巡查，滩涂围栏完好', '巡查发现少量死亡个体，已清理并记录', '夜间巡查，防盗设施正常'],
        '捕捞': ['小规模捕捞，产量约{0}kg', '集中捕捞，总产量{0}kg，规格达标', '试捕捞抽样，平均规格合格', '阶段性收获{0}kg，剩余继续养殖'],
        '水质抽检': ['水质抽检：温度{0}℃、溶氧{1}mg/L、盐度{2}‰、pH{3}', '送检水样合格，各项指标正常', '水质检测达标，适合继续养殖'],
        '苗种投放': ['投放{0}苗种{1}kg，来源{2}', '补投苗种{1}kg，附苗率良好'],
    }
    operators = {1: '张养殖', 2: '李海产', 3: '王滩涂'}
    
    for flat in TidalFlat.query.all():
        farmer = User.query.get(flat.farmer_id)
        operator = farmer.real_name if farmer else '未知'
        # 每个滩涂20-25条台账，时间跨度90天
        log_count = random.randint(20, 25)
        for i in range(log_count):
            work_type = random.choice(list(log_templates.keys()))
            template = random.choice(log_templates[work_type])
            if work_type == '投喂':
                content = template.format(random.choice([30, 40, 50, 60, 80, 100, 120]))
            elif work_type == '消杀':
                content = template.format(random.choice([15, 20, 25, 30]))
            elif work_type == '捕捞':
                content = template.format(random.choice([150, 200, 300, 500, 800, 1000]))
            elif work_type == '水质抽检':
                # 使用季节模型计算水质（与历史数据一致，非随机）
                log_day = random.randint(1, 90)
                log_ts = now - datetime.timedelta(days=log_day)
                log_doy = log_ts.timetuple().tm_yday
                log_base = flat_baselines.get(flat.id, {'temp_base': 12, 'salt_base': 30, 'oxy_base': 6.5, 'ph_base': 8.0})
                log_temp = get_seasonal_temp(log_base['temp_base'], log_doy)
                log_salt = get_seasonal_salinity(log_base['salt_base'], log_doy)
                log_oxy = get_seasonal_oxygen(log_base['oxy_base'], log_temp)
                content = template.format(
                    round(log_temp, 1),
                    round(log_oxy, 1),
                    round(log_salt, 1),
                    round(log_base['ph_base'], 2)
                )
            elif work_type == '苗种投放':
                species = random.choice(['缢蛏', '文蛤', '蚬子', '扇贝', '毛蚶'])
                qty = random.choice([500, 1000, 2000, 3000, 5000])
                source = random.choice(['东港苗种场', '盘锦苗种场', '盖州苗种场', '凤城苗种场', '丹东本地苗种'])
                content = template.format(species, qty, source)
            else:
                content = template
            
            log = DailyLog(
                flat_id=flat.id,
                work_type=work_type,
                content=content,
                operator=operator,
                log_date=(now - datetime.timedelta(days=random.randint(1, 90))).date(),
                created_at=now - datetime.timedelta(days=random.randint(1, 90))
            )
            db.session.add(log)
    
    # 创建气象预警数据（16条，含历史和未来）
    weather_warnings = [
        {'warning_type': 'cold', 'level': 'orange', 'area': '丹东', 'content': '寒潮橙色预警：未来48小时最低气温下降8-10℃，滩涂养殖需做好保温', 'forecast_date': now.date() + datetime.timedelta(days=1), 'processed': False},
        {'warning_type': 'gale', 'level': 'yellow', 'area': '盘锦', 'content': '大风黄色预警：渤海海峡将出现8-9级偏北大风，注意滩涂设施加固', 'forecast_date': now.date() + datetime.timedelta(days=2), 'processed': False},
        {'warning_type': 'snow', 'level': 'blue', 'area': '丹东', 'content': '暴雪蓝色预警：预计未来12小时降雪量将达4mm以上', 'forecast_date': now.date(), 'processed': False},
        {'warning_type': 'cold', 'level': 'blue', 'area': '盘锦', 'content': '寒潮蓝色预警：未来48小时最低气温下降4-6℃', 'forecast_date': now.date() + datetime.timedelta(days=3), 'processed': False},
        {'warning_type': 'cold', 'level': 'red', 'area': '丹东', 'content': '寒潮红色预警（历史）：1月强寒潮，最低气温-18℃', 'forecast_date': now.date() - datetime.timedelta(days=30), 'processed': True},
        {'warning_type': 'gale', 'level': 'orange', 'area': '盘锦', 'content': '大风橙色预警（历史）：渤海湾9级大风', 'forecast_date': now.date() - datetime.timedelta(days=45), 'processed': True},
        {'warning_type': 'snow', 'level': 'orange', 'area': '丹东', 'content': '暴雪橙色预警（历史）：降雪量8mm', 'forecast_date': now.date() - datetime.timedelta(days=60), 'processed': True},
        {'warning_type': 'cold', 'level': 'orange', 'area': '盘锦', 'content': '寒潮橙色预警（历史）：气温骤降10℃', 'forecast_date': now.date() - datetime.timedelta(days=75), 'processed': True},
        # 新增气象预警
        {'warning_type': 'typhoon', 'level': 'red', 'area': '丹东', 'content': '台风红色预警（历史）：台风"海棠"影响，阵风12级', 'forecast_date': now.date() - datetime.timedelta(days=15), 'processed': True},
        {'warning_type': 'storm', 'level': 'yellow', 'area': '盘锦', 'content': '雷暴大风黄色预警：局地强对流天气，注意防范', 'forecast_date': now.date() + datetime.timedelta(days=5), 'processed': False},
        {'warning_type': 'cold', 'level': 'yellow', 'area': '盖州', 'content': '低温黄色预警：最低气温将降至0℃以下', 'forecast_date': now.date() + datetime.timedelta(days=7), 'processed': False},
        {'warning_type': 'gale', 'level': 'blue', 'area': '凤城', 'content': '大风蓝色预警：未来24小时风力6-7级', 'forecast_date': now.date() + datetime.timedelta(days=4), 'processed': False},
        {'warning_type': 'flood', 'level': 'orange', 'area': '盘锦', 'content': '洪水橙色预警（历史）：辽河三角洲水位接近警戒线', 'forecast_date': now.date() - datetime.timedelta(days=45), 'processed': True},
        {'warning_type': 'haze', 'level': 'yellow', 'area': '丹东', 'content': '霾黄色预警：空气质量较差，建议减少户外活动', 'forecast_date': now.date() - datetime.timedelta(days=90), 'processed': True},
        {'warning_type': 'cold', 'level': 'blue', 'area': '盖州', 'content': '寒潮蓝色预警（历史）：春季气温骤降8℃', 'forecast_date': now.date() - datetime.timedelta(days=110), 'processed': True},
        {'warning_type': 'gale', 'level': 'orange', 'area': '丹东', 'content': '大风橙色预警（历史）：渤海北部9-10级阵风', 'forecast_date': now.date() - datetime.timedelta(days=130), 'processed': True},
    ]
    for w_data in weather_warnings:
        w = WeatherWarning(**w_data)
        db.session.add(w)
    
    # 创建采购订单数据（5条）
    purchase_orders = [
        {'post_id': 1, 'enterprise_id': 4, 'agreed_price': 14.5, 'quantity': 2000, 'status': 'completed'},
        {'post_id': 2, 'enterprise_id': 4, 'agreed_price': 11.5, 'quantity': 1500, 'status': 'completed'},
        {'post_id': 3, 'enterprise_id': 5, 'agreed_price': 7.8, 'quantity': 3000, 'status': 'confirmed'},
        {'post_id': 6, 'enterprise_id': 5, 'agreed_price': 13.5, 'quantity': 1800, 'status': 'pending'},
        {'post_id': 8, 'enterprise_id': 4, 'agreed_price': 32.0, 'quantity': 500, 'status': 'pending'},
    ]
    for p_data in purchase_orders:
        order = PurchaseOrder(
            post_id=p_data['post_id'],
            enterprise_id=p_data['enterprise_id'],
            agreed_price=p_data['agreed_price'],
            quantity=p_data['quantity'],
            status=p_data['status'],
            created_at=now - datetime.timedelta(days=random.randint(1, 20))
        )
        db.session.add(order)
    
    # 创建农技知识库文章（30+篇，涵盖6大类）
    knowledge_articles = [
        # 冬季育苗
        {'category': '冬季育苗', 'title': '东北寒地贝类冬季育苗技术要点', 'summary': '水温控制、饵料投喂、病害预防', 'content': '东北寒地贝类冬季育苗需注意：\n1. 水温控制：保持在8-12℃为宜，过低会减缓生长，过高会引发病害\n2. 饵料投喂：冬季贝类摄食量减少，应适当降低投喂量至日常的40%\n3. 病害预防：定期检查水质，保持溶氧在5mg/L以上，注意预防低温综合征\n4. 保温措施：极端低温时增加水位，必要时使用保温网\n5. 光照管理：适当增加光照时间，有助于贝类摄食和生长', 'author': '辽宁省水产研究院', 'views': 328, 'is_featured': True},
        {'category': '冬季育苗', 'title': '低温育苗温室搭建指南', 'summary': '保温材料选择、通风管理、成本预算', 'content': '低温育苗温室搭建要点：\n1. 保温材料：建议使用10cm厚的聚苯乙烯泡沫板，导热系数低\n2. 通风管理：每日通风2次，每次30分钟，保持空气新鲜\n3. 成本预算：每平方米造价约150-200元，含框架、覆盖、通风设备\n4. 温控系统：建议配置自动温控系统，设定8-15℃范围\n5. 选址建议：选择背风向阳处，减少热能损失', 'author': '丹东市水产推广站', 'views': 256},
        {'category': '冬季育苗', 'title': '北方冬季育苗常见问题解答', 'summary': '常见异常处理、应急方案', 'content': '常见问题与处理：\n1. 苗种浮起：可能是水温骤变或溶氧不足，检查水质并增氧\n2. 食欲减退：检查水温是否偏低，可适当提高0.5-1℃\n3. 苗种死亡：排查是否感染疾病，必要时使用温和性消毒剂\n4. 生长缓慢：可能是饵料不足或水温偏低，调整投喂量和温度\n5. 水质恶化：立即换水30%，并检查过滤系统', 'author': '王养殖高级工程师', 'views': 189},
        # 生态混养
        {'category': '生态混养', 'title': '贝类+海带生态混养模式', 'summary': '互利共生原理、养殖密度控制、经济效益分析', 'content': '贝藻混养技术：\n1. 共生原理：贝类呼吸产生CO2供海带光合作用，海带产生O2供贝类呼吸\n2. 密度控制：贝类养殖密度50kg/亩，海带每亩种1000-1500株\n3. 水深要求：保持在1.5-2.0米，确保海带光照和贝类活动空间\n4. 经济效益：混养模式可比单养增收30-50%\n5. 水质改善：贝藻混养可有效改善水质，减少病害发生', 'author': '大连海洋大学', 'views': 412, 'is_featured': True},
        {'category': '生态混养', 'title': '多营养层次综合水产养殖(IMTA)', 'summary': '构建海洋牧场、提高空间利用率', 'content': 'IMTA模式介绍：\n1. 理念：利用不同物种营养生态位的互补，实现废物循环利用\n2. 层次划分：上层养殖海带等大型藻类，中层养殖扇贝等滤食性贝类，底层养殖海参等沉积摄食动物\n3. 辽宁实践：丹东东港试验区已推广IMTA模式，总面积达5000亩\n4. 环境效益：氮磷利用率提高60%，养殖废水排放减少50%\n5. 经济效益：综合产值提高40-60%', 'author': '辽宁省海洋水产研究所', 'views': 378},
        {'category': '生态混养', 'title': '贝类与底栖生物协同养殖技术', 'summary': '生态平衡、生物多样性、自然净化', 'content': '协同养殖技术要点：\n1. 底栖生物选择：可选养虫、沙蚕、小型甲壳类等\n2. 投放比例：底栖生物生物量占总养殖生物量的10-15%\n3. 生态作用：分解有机碎屑，循环营养物质，改善底质环境\n4. 监测指标：底栖生物密度保持在200-500个/平方米\n5. 季节管理：春季补充底栖生物，冬季监测存活情况', 'author': '盘锦市水产技术推广站', 'views': 145},
        # 病害防治
        {'category': '病害防治', 'title': '低温期常见贝类病害识别与防治', 'summary': '寄生虫病、细菌性疾病、病毒性疾病防治方案', 'content': '贝类病害防治手册：\n1. 寄生虫病：症状为贝类消瘦、闭壳无力，可用硫酸铜溶液浸泡15分钟\n2. 细菌性疾病：症状为贝壳附着物、肉质变色，使用聚维酮碘消毒\n3. 病毒性疾病：症状为大规模死亡，目前无特效药，以预防为主\n4. 预防措施：定期消毒水体，保持水质清洁，避免过度密集养殖\n5. 治疗原则：早发现、早治疗，防止疾病扩散', 'author': '沈阳农业大学', 'views': 298, 'is_featured': True},
        {'category': '病害防治', 'title': '寒潮前后病害预防措施', 'summary': '抗应激处理、水体消毒、营养补充', 'content': '寒潮防御技术：\n1. 防寒准备：提前加深水位至1.5米以上，减少水温波动\n2. 抗应激处理：寒潮前3天添加维生素C和电解质\n3. 水体消毒：寒潮后水温回升时进行温和消毒\n4. 营养补充：恢复投喂时添加免疫增强剂\n5. 监测重点：寒潮后7天内每日监测死亡率和水质', 'author': '辽宁省水产研究院', 'views': 223},
        {'category': '病害防治', 'title': '贝类养殖水质异常应急处理', 'summary': '溶氧骤降、pH异常、盐度突变处理方案', 'content': '水质异常应急方案：\n1. 溶氧骤降：立即启动增氧设备，检查是否有污染源\n2. pH异常：偏酸时使用生石灰调节，偏碱时使用明矾\n3. 盐度突变：大量换水稀释，缓慢调整至适宜范围\n4. 氨氮超标：换水+增氧+使用硝化细菌\n5. 综合措施：建立水质预警系统，设置溶氧、pH、盐度报警阈值', 'author': '丹东市水产研究所', 'views': 187},
        {'category': '病害防治', 'title': '贝类寄生虫病综合防治方案', 'summary': '常见寄生虫识别、药物选择、用药规范', 'content': '寄生虫病防治：\n1. 常见种类：纤毛虫、吸管虫、指环虫等\n2. 识别方法：镜检鳃片和外套膜，观察虫体形态\n3. 药物选择：硫酸铜、硫酸亚铁、敌百虫等，交替使用防耐药\n4. 用药方法：药浴15-30分钟，全池泼洒浓度0.5-1ppm\n5. 注意事项：严格遵守休药期，用药后增氧', 'author': '大连海洋大学病害中心', 'views': 156},
        # 水质管理
        {'category': '水质管理', 'title': '寒地贝类养殖水质调控技术', 'summary': '温度、盐度、溶氧、pH精准控制', 'content': '水质调控技术：\n1. 水温管理：冬季保持8-12℃，夏季不超过25℃\n2. 盐度控制：适宜范围28-34‰，雨季注意淡水注入\n3. 溶氧管理：保持在5mg/L以上，可用增氧机或水流增氧\n4. pH调节：保持7.8-8.2，偏高用明矾，偏低用石灰\n5. 监测频率：每日至少2次，关键时段（清晨、午后）加密监测', 'author': '辽宁省海洋水产研究所', 'views': 345, 'is_featured': True},
        {'category': '水质管理', 'title': '冬季水质管理要点', 'summary': '低温水质特征、监测指标、调控措施', 'content': '冬季水质管理：\n1. 低温特征：溶氧升高，盐度浓缩，pH稳定\n2. 监测重点：水温变化、溶氧水平、氨氮含量\n3. 调控措施：减少换水频次，避免水温大幅波动\n4. 注意事项：冰层覆盖期间加强底层监测\n5. 春季管理：冰层融化后逐步恢复正常监测频率', 'author': '盘锦市水产技术推广站', 'views': 198},
        {'category': '水质管理', 'title': '滩涂养殖水体自净能力提升方法', 'summary': '生物净化、物理净化、化学净化综合应用', 'content': '水体自净提升方案：\n1. 生物净化：接种有益菌（芽孢杆菌、光合细菌），维持藻相平衡\n2. 物理净化：使用活性炭、沸石等吸附材料，定期更换\n3. 化学净化：定期使用水质改良剂，如过氧化钙\n4. 综合方案：建立"生物-物理-化学"三层净化体系\n5. 效果评估：每月监测水质各项指标变化', 'author': '丹东市水产研究所', 'views': 132},
        {'category': '水质管理', 'title': '赤潮预防与应急处理', 'summary': '赤潮预警、养殖应急、灾后恢复', 'content': '赤潮应对方案：\n1. 预警监测：关注海洋部门赤潮预警信息，每周进行浮游植物监测\n2. 养殖防控：发现赤潮立即减少换水，防止赤潮生物进入养殖区\n3. 应急处理：已受影响的养殖区暂停投喂，增加增氧\n4. 灾后恢复：赤潮消退后换水，检测水质恢复正常后再恢复生产\n5. 长期措施：减少养殖密度，改善养殖环境以增强生态抵抗力', 'author': '辽宁省海洋环境监测站', 'views': 267},
        # 投喂技术
        {'category': '投喂技术', 'title': '寒地贝类科学投喂方案', 'summary': '投喂量计算、投喂时机、饵料选择', 'content': '科学投喂方案：\n1. 投喂量：贝类体重的3-5%，根据水温调整\n2. 投喂时机：水温在8-20℃时投喂最佳\n3. 饵料选择：底栖硅藻、单细胞藻类、人工配合饵料\n4. 投喂频率：冬季每日1次，生长季每日2次\n5. 注意观察：根据贝类摄食情况调整投喂量', 'author': '大连海洋大学水产养殖系', 'views': 289},
        {'category': '投喂技术', 'title': '冬季饵料配方优化', 'summary': '营养需求、饵料配比、摄食促进', 'content': '冬季饵料优化：\n1. 营养需求：提高脂肪含量至10-12%，增加能量供应\n2. 饵料配比：植物性饵料60%，动物性饵料25%，添加剂15%\n3. 摄食促进：添加诱食剂（氨基酸、核苷酸）\n4. 投喂时间：选择水温最高时段投喂\n5. 注意事项：饵料新鲜度要求更高，避免变质饵料', 'author': '辽宁省水产研究院营养中心', 'views': 178},
        {'category': '投喂技术', 'title': '不同生长阶段投喂策略', 'summary': '苗种期、养成期、育肥期投喂要点', 'content': '分段投喂策略：\n1. 苗种期（壳长<2cm）：投喂硅藻为主，每日4-6次\n2. 养成期（壳长2-5cm）：混合饵料，每日2-3次\n3. 育肥期（上市前1-2月）：高蛋白饵料，增加投喂量\n4. 夏冬季调整：减少投喂量或暂停投喂\n5. 投喂记录：建立投喂台账，便于优化', 'author': '丹东东港养殖合作社', 'views': 156},
        {'category': '投喂技术', 'title': '饵料储存与质量控制', 'summary': '储存条件、保质期、质量检测', 'content': '饵料储存管理：\n1. 储存条件：干燥通风，温度<25℃，湿度<60%\n2. 保质期：配合饵料6个月，鲜活饵料3天\n3. 质量检测：检查气味、颜色、颗粒均匀度\n4. 使用原则：先进先出（FIFO），避免积压\n5. 异常处理：变质饵料立即销毁，不得使用', 'author': '盘锦市水产质检站', 'views': 98},
        # 收获加工
        {'category': '收获加工', 'title': '寒地贝类最佳收获时机判断', 'summary': '季节判断、规格要求、质量标准', 'content': '收获时机判断：\n1. 季节选择：春秋季贝类品质最佳\n2. 规格要求：壳长达到商品规格（缢蛏5cm，文蛤6cm）\n3. 肥满度：肥满率达到15%以上\n4. 质量标准：活贝率>95%，无异味\n5. 监测方法：定期测量壳长、体重、肥满度', 'author': '辽宁省海洋水产研究所', 'views': 234},
        {'category': '收获加工', 'title': '贝类捕捞与分拣技术规范', 'summary': '捕捞方式、分拣标准、质量分级', 'content': '捕捞分拣规范：\n1. 捕捞方式：手工捕捞或机械捕捞，避免损伤贝类\n2. 分拣标准：按规格分级，去除破损贝、空壳\n3. 质量分级：特级（无泥无沙）、一级（微量泥沙）、二级\n4. 保鲜处理：捕捞后立即低温保存\n5. 记录追溯：每批次记录捕捞时间、人员、地点', 'author': '丹东市水产局', 'views': 187},
        {'category': '收获加工', 'title': '贝类暂养与活运技术', 'summary': '暂养时间、运输温度、成活率保证', 'content': '活贝运输技术：\n1. 暂养时间：出货前暂养24-48小时吐沙\n2. 运输温度：0-5℃冷藏运输\n3. 运输密度：每平方米不超过50kg\n4. 成活率保证：采用透气包装+冰袋，成活率>98%\n5. 时间控制：运输时间不超过48小时', 'author': '大连海鲜连锁物流部', 'views': 167},
        {'category': '收获加工', 'title': '贝类预制菜加工技术', 'summary': '清洗、调味、烹饪、包装全流程', 'content': '预制菜加工流程：\n1. 清洗：三洗三泡，去除泥沙\n2. 调味：可添加葱姜、料酒等调味料\n3. 烹饪：速冻熟制工艺，保持口感\n4. 包装：真空密封+冷链运输\n5. 保质期：-18℃冷冻可保存6个月', 'author': '辽贝预制菜有限公司', 'views': 198, 'is_featured': True},
        # 政策解读
        {'category': '政策解读', 'title': '辽宁省"三年两养一休"政策解读', 'summary': '政策背景、实施细则、补贴申请指南', 'content': '政策解读：\n1. 背景：推进滩涂养殖可持续发展，保护海洋生态\n2. 内容：每三年养殖2年、休耕1年\n3. 补贴：休耕期给予养殖户生态补偿\n4. 申请流程：村集体申请→乡镇审核→县级审批\n5. 标准：补贴标准为每年每亩500-800元', 'author': '辽宁省农业农村厅', 'views': 456, 'is_featured': True},
        {'category': '政策解读', 'title': '滩涂养殖生态保护要求', 'summary': '禁养区规定、养殖容量、污染防治', 'content': '生态保护规定：\n1. 禁养区：海洋自然保护区、饮用水源保护区等\n2. 限养区：生态敏感区控制养殖规模\n3. 养殖容量：根据海域生产力确定最大养殖量\n4. 污染防治：禁止使用违禁药物，控制养殖污染\n5. 定期核查：每年开展养殖容量评估', 'author': '辽宁省生态环境厅', 'views': 298},
        {'category': '政策解读', 'title': '辽宁省贝类养殖许可办理指南', 'summary': '办理条件、所需材料、审批流程', 'content': '许可办理指南：\n1. 办理条件：年满18周岁，具有完全民事行为能力\n2. 所需材料：身份证、滩涂承包合同、养殖方案\n3. 审批流程：提交申请→现场核查→专家评审→审批发证\n4. 办理期限：自受理之日起30个工作日\n5. 有效期：养殖许可有效期5年', 'author': '丹东市行政审批局', 'views': 234},
        {'category': '政策解读', 'title': '水产养殖绿色发展补贴项目', 'summary': '补贴类型、申请条件、申报材料', 'content': '绿色养殖补贴：\n1. 补贴类型：生态养殖补贴、设备更新补贴、技术推广补贴\n2. 申请条件：从事绿色养殖的养殖户、合作社、企业\n3. 申报材料：项目申请书、实施方案、预算表\n4. 支持标准：单项目补贴金额不超过50万元\n5. 申报时间：每年3-4月申报，6月公布结果', 'author': '辽宁省财政厅', 'views': 189},
        # 市场分析
        {'category': '市场分析', 'title': '2024年辽宁贝类市场行情分析', 'summary': '价格走势、销售渠道、消费趋势', 'content': '市场行情分析：\n1. 价格走势：缢蛏价格同比上涨10%，文蛤价格基本平稳\n2. 销售渠道：批发、零售、电商、预制菜加工\n3. 消费趋势：预制菜、即食贝类需求增长30%\n4. 出口情况：日韩市场稳定，东南亚市场增长\n5. 建议：关注预制菜加工方向，拓展电商渠道', 'author': '辽宁省水产流通协会', 'views': 389, 'is_featured': True},
        {'category': '市场分析', 'title': '贝类电商销售策略', 'summary': '平台选择、直播带货、品牌建设', 'content': '电商运营策略：\n1. 平台选择：天猫、京东、抖音小店、拼多多\n2. 直播带货：与海鲜品类达人合作，每场直播GMV平均5万元\n3. 品牌建设：注册地理标志商标，打造区域品牌\n4. 客户服务：快速发货、冷链配送、售后无忧\n5. 数据分析：关注爆款产品，优化选品', 'author': '抖音电商海鲜品类运营', 'views': 267},
        {'category': '市场分析', 'title': '贝类预制菜市场机遇分析', 'summary': '市场规模、竞争格局、发展趋势', 'content': '预制菜机遇分析：\n1. 市场规模：2024年贝类预制菜市场规模达50亿元\n2. 竞争格局：传统海鲜企业+新锐预制菜品牌\n3. 发展趋势：速冻、自热、休闲零食化\n4. 切入建议：与预制菜企业合作，提供原料或代工\n5. 品牌机会：打造"辽宁贝类"区域公用品牌', 'author': '国信证券食品饮料研究员', 'views': 212},
        {'category': '市场分析', 'title': '海产品冷链物流成本控制', 'summary': '运输成本、保鲜技术、效率提升', 'content': '冷链成本控制：\n1. 成本构成：运输50%，包装20%，仓储15%，损耗15%\n2. 保鲜技术：气调保鲜、冰温保鲜、超低温冷冻\n3. 效率提升：集约化运输、智能调度、路线优化\n4. 合作模式：与第三方冷链物流企业签订长期合同\n5. 成本优化：规模化经营可降低单位成本20%', 'author': '辽宁港口物流集团', 'views': 145},
        # 气象灾害
        {'category': '气象灾害', 'title': '寒潮灾害防御技术手册', 'summary': '预警识别、防御措施、灾后恢复', 'content': '寒潮防御手册：\n1. 预警识别：关注气象部门寒潮蓝色/黄色/橙色/红色预警\n2. 防御措施：加深水位、加固设施、准备应急设备\n3. 应急响应：红色预警时暂停养殖作业，启动应急预案\n4. 灾后恢复：监测水质和贝类状态，逐步恢复生产\n5. 保险建议：购买水产养殖保险，降低灾害损失', 'author': '辽宁省气象灾害防御中心', 'views': 278},
        {'category': '气象灾害', 'title': '台风季节滩涂养殖防灾指南', 'summary': '台风预警、设施加固、应急方案', 'content': '台风防灾指南：\n1. 预警阶段：收到台风预警后立即准备\n2. 设施加固：加固养殖设施，检查网箱、浮球等\n3. 应急措施：台风来临前加深水位，减少贝类移动\n4. 灾后处理：台风过后检查设施，清理杂物，监测水质\n5. 经验总结：每次台风后记录损失，优化防灾措施', 'author': '丹东市应急管理局', 'views': 234},
        {'category': '气象灾害', 'title': '极端高温天气养殖应对', 'summary': '高温危害、降温措施、应急管理', 'content': '高温应对方案：\n1. 高温危害：水温超过28℃会影响贝类摄食和生长\n2. 降温措施：增加水深、换水、使用遮阳网\n3. 监测频率：高温天气每2小时监测一次水温\n4. 应急管理：水温超过30℃时启动应急降温方案\n5. 长期措施：建设深水养殖塘，配备降温设备', 'author': '大连市气象局', 'views': 189},
        {'category': '气象灾害', 'title': '春季大风天气注意事项', 'summary': '大风危害、预防措施、设备检查', 'content': '大风天应对：\n1. 大风危害：设施损坏、水质变化、贝类应激\n2. 预防措施：加固浮球、检查缆绳、清理障碍物\n3. 设备检查：检查增氧机、水泵等设备是否牢固\n4. 应急处理：大风过后检查受损设施，及时修复\n5. 安全提醒：大风天气不要出海作业', 'author': '盘锦市应急管理局', 'views': 132},
    ]
    for k_data in knowledge_articles:
        article = KnowledgeArticle(**k_data)
        db.session.add(article)
    
    # 创建AI产量预测历史记录（15条，覆盖不同滩涂和时间）
    prediction_records = [
        {'user_id': 1, 'flat_id': 1, 'seed_quantity': 150, 'predict_days': 90, 'predicted_yield': 1800, 'survival_rate': 85.2, 'environmental_score': 82.5, 'confidence': 88.3, 'avg_temperature': 8.5, 'avg_salinity': 31.2, 'avg_oxygen': 6.5, 'avg_ph': 8.0, 'suggestions_count': 2, 'days_ago': 5},
        {'user_id': 1, 'flat_id': 2, 'seed_quantity': 200, 'predict_days': 90, 'predicted_yield': 2400, 'survival_rate': 88.1, 'environmental_score': 85.7, 'confidence': 90.1, 'avg_temperature': 9.2, 'avg_salinity': 32.0, 'avg_oxygen': 6.8, 'avg_ph': 8.1, 'suggestions_count': 1, 'days_ago': 10},
        {'user_id': 1, 'flat_id': 3, 'seed_quantity': 180, 'predict_days': 120, 'predicted_yield': 2160, 'survival_rate': 83.5, 'environmental_score': 79.8, 'confidence': 85.6, 'avg_temperature': 10.1, 'avg_salinity': 30.8, 'avg_oxygen': 6.2, 'avg_ph': 7.9, 'suggestions_count': 3, 'days_ago': 15},
        {'user_id': 2, 'flat_id': 4, 'seed_quantity': 120, 'predict_days': 90, 'predicted_yield': 1440, 'survival_rate': 82.3, 'environmental_score': 77.5, 'confidence': 83.2, 'avg_temperature': 8.8, 'avg_salinity': 29.5, 'avg_oxygen': 5.8, 'avg_ph': 7.8, 'suggestions_count': 4, 'days_ago': 8},
        {'user_id': 2, 'flat_id': 5, 'seed_quantity': 100, 'predict_days': 60, 'predicted_yield': 1200, 'survival_rate': 86.7, 'environmental_score': 84.2, 'confidence': 87.5, 'avg_temperature': 9.5, 'avg_salinity': 31.8, 'avg_oxygen': 6.6, 'avg_ph': 8.0, 'suggestions_count': 2, 'days_ago': 20},
        {'user_id': 2, 'flat_id': 6, 'seed_quantity': 160, 'predict_days': 90, 'predicted_yield': 1920, 'survival_rate': 84.5, 'environmental_score': 81.3, 'confidence': 86.8, 'avg_temperature': 10.2, 'avg_salinity': 30.5, 'avg_oxygen': 6.1, 'avg_ph': 7.9, 'suggestions_count': 3, 'days_ago': 12},
        {'user_id': 3, 'flat_id': 7, 'seed_quantity': 250, 'predict_days': 120, 'predicted_yield': 3000, 'survival_rate': 87.2, 'environmental_score': 86.5, 'confidence': 89.7, 'avg_temperature': 9.8, 'avg_salinity': 32.1, 'avg_oxygen': 6.7, 'avg_ph': 8.1, 'suggestions_count': 1, 'days_ago': 3},
        {'user_id': 3, 'flat_id': 8, 'seed_quantity': 180, 'predict_days': 90, 'predicted_yield': 2160, 'survival_rate': 85.8, 'environmental_score': 83.2, 'confidence': 87.1, 'avg_temperature': 8.9, 'avg_salinity': 31.5, 'avg_oxygen': 6.4, 'avg_ph': 8.0, 'suggestions_count': 2, 'days_ago': 7},
        {'user_id': 1, 'flat_id': 1, 'seed_quantity': 160, 'predict_days': 60, 'predicted_yield': 1920, 'survival_rate': 86.5, 'environmental_score': 84.8, 'confidence': 88.9, 'avg_temperature': 10.5, 'avg_salinity': 31.8, 'avg_oxygen': 6.6, 'avg_ph': 8.1, 'suggestions_count': 1, 'days_ago': 1},
        {'user_id': 2, 'flat_id': 5, 'seed_quantity': 110, 'predict_days': 90, 'predicted_yield': 1320, 'survival_rate': 83.8, 'environmental_score': 80.2, 'confidence': 85.3, 'avg_temperature': 9.0, 'avg_salinity': 30.2, 'avg_oxygen': 6.0, 'avg_ph': 7.9, 'suggestions_count': 3, 'days_ago': 18},
        {'user_id': 1, 'flat_id': 3, 'seed_quantity': 200, 'predict_days': 180, 'predicted_yield': 2800, 'survival_rate': 82.5, 'environmental_score': 78.6, 'confidence': 84.2, 'avg_temperature': 11.2, 'avg_salinity': 30.0, 'avg_oxygen': 5.9, 'avg_ph': 7.8, 'suggestions_count': 4, 'days_ago': 25},
        {'user_id': 3, 'flat_id': 9, 'seed_quantity': 150, 'predict_days': 90, 'predicted_yield': 1800, 'survival_rate': 84.9, 'environmental_score': 82.1, 'confidence': 86.5, 'avg_temperature': 9.3, 'avg_salinity': 31.4, 'avg_oxygen': 6.3, 'avg_ph': 8.0, 'suggestions_count': 2, 'days_ago': 4},
        {'user_id': 2, 'flat_id': 6, 'seed_quantity': 130, 'predict_days': 60, 'predicted_yield': 1560, 'survival_rate': 85.3, 'environmental_score': 83.6, 'confidence': 87.8, 'avg_temperature': 10.0, 'avg_salinity': 31.6, 'avg_oxygen': 6.5, 'avg_ph': 8.0, 'suggestions_count': 1, 'days_ago': 9},
        {'user_id': 1, 'flat_id': 2, 'seed_quantity': 220, 'predict_days': 120, 'predicted_yield': 2640, 'survival_rate': 86.1, 'environmental_score': 84.5, 'confidence': 88.2, 'avg_temperature': 10.8, 'avg_salinity': 32.3, 'avg_oxygen': 6.4, 'avg_ph': 8.1, 'suggestions_count': 2, 'days_ago': 2},
        {'user_id': 3, 'flat_id': 8, 'seed_quantity': 190, 'predict_days': 90, 'predicted_yield': 2280, 'survival_rate': 84.2, 'environmental_score': 81.9, 'confidence': 86.1, 'avg_temperature': 9.6, 'avg_salinity': 31.0, 'avg_oxygen': 6.2, 'avg_ph': 7.9, 'suggestions_count': 3, 'days_ago': 14},
    ]
    for p_data in prediction_records:
        record = PredictionRecord(
            user_id=p_data['user_id'],
            flat_id=p_data['flat_id'],
            seed_quantity=p_data['seed_quantity'],
            predict_days=p_data['predict_days'],
            predicted_yield=p_data['predicted_yield'],
            survival_rate=p_data['survival_rate'],
            environmental_score=p_data['environmental_score'],
            confidence=p_data['confidence'],
            avg_temperature=p_data['avg_temperature'],
            avg_salinity=p_data['avg_salinity'],
            avg_oxygen=p_data['avg_oxygen'],
            avg_ph=p_data['avg_ph'],
            suggestions_count=p_data['suggestions_count'],
            created_at=now - datetime.timedelta(days=p_data['days_ago'])
        )
        db.session.add(record)
    
    # 创建消息通知数据（每个用户5-8条）
    notifications_data = [
        # 农户1的通知
        {'user_id': 1, 'title': '【灾害预警】赤潮预警！', 'content': '东港3号滩涂溶解氧骤降至2.1mg/L，贝类面临缺氧风险，请立即处理', 'notify_type': 'alert', 'level': 'danger', 'related_id': 1, 'related_type': 'alert', 'days_ago': 1},
        {'user_id': 1, 'title': '溯源码生成成功', 'content': '产品"东港缢蛏（礼盒装）"的溯源码已生成并完成区块链上链', 'notify_type': 'trace', 'level': 'success', 'related_id': 7, 'related_type': 'traceability', 'days_ago': 2},
        {'user_id': 1, 'title': '寒潮预警通知', 'content': '未来48小时最低气温下降8-10℃，请做好保温措施', 'notify_type': 'alert', 'level': 'warning', 'related_type': 'weather', 'days_ago': 3},
        {'user_id': 1, 'title': '新的采购订单', 'content': '辽贝预制菜有限公司对您的"丹东缢蛏（大规格）"感兴趣，请查看详情', 'notify_type': 'trade', 'level': 'info', 'related_type': 'order', 'days_ago': 4},
        {'user_id': 1, 'title': '系统维护通知', 'content': '平台将于本周六凌晨2-4点进行系统维护，请提前保存数据', 'notify_type': 'system', 'level': 'info', 'days_ago': 5},
        {'user_id': 1, 'title': 'AI产量预测完成', 'content': '东港1号滩涂的预测已完成，预计产量1920kg，置信度88.9%', 'notify_type': 'system', 'level': 'success', 'related_type': 'prediction', 'days_ago': 1},
        
        # 农户2的通知
        {'user_id': 2, 'title': '【灾害预警】洪水预警', 'content': '辽河三角洲水位接近警戒线，请加强滩涂巡查', 'notify_type': 'alert', 'level': 'danger', 'related_type': 'weather', 'days_ago': 2},
        {'user_id': 2, 'title': '溯源状态更新', 'content': '产品"盘锦文蛤"溯源记录已更新', 'notify_type': 'trace', 'level': 'info', 'related_id': 2, 'related_type': 'traceability', 'days_ago': 5},
        {'user_id': 2, 'title': '订单确认通知', 'content': '采购订单已确认，请按时完成交货', 'notify_type': 'trade', 'level': 'success', 'related_type': 'order', 'days_ago': 1},
        {'user_id': 2, 'title': '水质异常提醒', 'content': '盖州2号滩涂溶解氧偏低（3.8mg/L），建议增氧', 'notify_type': 'alert', 'level': 'warning', 'related_type': 'alert', 'days_ago': 1},
        
        # 农户3的通知
        {'user_id': 3, 'title': '【灾害预警】寒潮预警', 'content': '气温骤降10℃，贝类注意保温', 'notify_type': 'alert', 'level': 'danger', 'related_type': 'weather', 'days_ago': 2},
        {'user_id': 3, 'title': '溯源码生成成功', 'content': '产品"凤城扇贝（礼盒装）"的溯源码已生成', 'notify_type': 'trace', 'level': 'success', 'related_id': 6, 'related_type': 'traceability', 'days_ago': 3},
        {'user_id': 3, 'title': '产销信息曝光', 'content': '您发布的"凤城缢蛏"已被多家企业关注', 'notify_type': 'trade', 'level': 'info', 'related_type': 'post', 'days_ago': 4},
        
        # 合作社的通知
        {'user_id': 4, 'title': '合作社成员变动', 'content': '新增2名农户加入合作社', 'notify_type': 'system', 'level': 'info', 'days_ago': 2},
        {'user_id': 4, 'title': '统购统销通知', 'content': '本周将进行集中采购，请各成员提交需求', 'notify_type': 'system', 'level': 'warning', 'days_ago': 1},
        
        # 企业的通知
        {'user_id': 5, 'title': '新的采购订单', 'content': '订单#2026080001已创建，请查看详情', 'notify_type': 'trade', 'level': 'info', 'related_type': 'order', 'days_ago': 1},
        {'user_id': 5, 'title': '溯源验证请求', 'content': '有客户请求验证产品溯源信息', 'notify_type': 'trace', 'level': 'info', 'days_ago': 3},
        {'user_id': 5, 'title': '库存预警', 'content': '预制菜原料库存不足，请及时补货', 'notify_type': 'enterprise', 'level': 'warning', 'days_ago': 2},
        
        # 企业2的通知
        {'user_id': 6, 'title': '新供应商入驻', 'content': '东港滩涂合作社成为您的认证供应商', 'notify_type': 'enterprise', 'level': 'success', 'days_ago': 4},
        {'user_id': 6, 'title': '订单状态更新', 'content': '订单#2026080002已确认，预计3天内交货', 'notify_type': 'trade', 'level': 'info', 'days_ago': 1},
        
        # 监管的通知
        {'user_id': 7, 'title': '【监管】新增溯源记录', 'content': '本月新增溯源记录127条，同比增长15%', 'notify_type': 'regulator', 'level': 'info', 'days_ago': 2},
        {'user_id': 7, 'title': '【监管】异常预警', 'content': '东港地区出现1条红色预警，已处理', 'notify_type': 'alert', 'level': 'warning', 'days_ago': 5},
        {'user_id': 7, 'title': '【监管】季度报告', 'content': '2026年Q3贝类养殖质量安全报告已生成', 'notify_type': 'regulator', 'level': 'success', 'days_ago': 3},
        
        # 监管2的通知
        {'user_id': 8, 'title': '【监管】生态监测报告', 'content': '盘锦辽河口生态监测数据已更新', 'notify_type': 'regulator', 'level': 'info', 'days_ago': 4},
        {'user_id': 8, 'title': '【监管】养殖户培训通知', 'content': '下周举办绿色养殖技术培训班', 'notify_type': 'system', 'level': 'info', 'days_ago': 1},
    ]
    for n_data in notifications_data:
        notification = Notification(
            user_id=n_data['user_id'],
            title=n_data['title'],
            content=n_data['content'],
            notify_type=n_data['notify_type'],
            level=n_data['level'],
            related_id=n_data.get('related_id'),
            related_type=n_data.get('related_type'),
            is_read=random.random() > 0.3,
            created_at=now - datetime.timedelta(days=n_data.get('days_ago', 1), hours=random.randint(0, 23))
        )
        db.session.add(notification)
    
    db.session.commit()
    print("[INIT] 演示数据初始化完成（完整版）")

if __name__ == '__main__':
    app = create_app()
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"[ERROR] 启动失败: {e}")
        traceback.print_exc()
        sys.exit(1)
