"""
认证路由 - 登录/注册/登出
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User, ROLE_NAMES

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '')
        
        if not username or not password:
            flash('请输入用户名和密码', 'warning')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('用户名或密码错误', 'danger')
            return render_template('auth/login.html')
        
        # 角色不匹配时自动提示正确角色，而不是报错
        if role and user.role != role:
            correct_role = ROLE_NAMES.get(user.role, user.role)
            # 允许登录，但提示实际角色
            flash(f'登录成功！检测到您的账号为「{correct_role}」角色', 'info')
        
        if not user.is_active:
            flash('账号已被禁用', 'danger')
            return render_template('auth/login.html')
        
        login_user(user)
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/login.html', roles=ROLE_NAMES)

@auth_bp.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    flash('已安全退出系统', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面 - 仅支持农户自助注册"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        real_name = request.form.get('real_name', '').strip()
        phone = request.form.get('phone', '').strip()
        area = request.form.get('area', '').strip()
        
        if not all([username, password, confirm_password, real_name]):
            flash('请填写完整信息', 'warning')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('两次密码输入不一致', 'danger')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('密码至少6位', 'warning')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('auth/register.html')
        
        from extensions import db
        user = User(
            username=username,
            role='farmer',
            real_name=real_name,
            phone=phone,
            area=area
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')
