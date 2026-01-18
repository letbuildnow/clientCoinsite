from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user
from app import db
from app.models import User, AccessCode

bp = Blueprint('auth', __name__)

@bp.route('/', methods=['GET'])
def index():
    # If they are already logged in, send them to their dashboard
    if current_user.is_authenticated:
        if current_user.role == 'ADMIN':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))
        
    # Otherwise, show the landing page
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # FIX 2: Check role if they are already logged in
    if current_user.is_authenticated:
        if current_user.role == 'ADMIN':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        
        # FIX 3: Check role immediately after logging in
        if user.role == 'ADMIN':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
        
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, send them to dashboard
    if current_user.is_authenticated:
        if current_user.role == 'ADMIN':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))
        
    if request.method == 'POST':
        code_input = request.form.get('valid_code')
        username = request.form['username']
        password = request.form['password']

        # 1. Verify Code again (Security)
        access_code = AccessCode.query.filter_by(code=code_input, is_used=False).first()
        
        if not access_code:
            flash('Error: This invite code is invalid or expired.')
            return redirect(url_for('auth.register'))

        # 2. Create User
        user = User(
            username=username, 
            wallet_balance=access_code.balance_value, # Assign money from code
            used_code_id=access_code.id
        )
        user.set_password(password)
        
        # 3. Mark code as used
        access_code.is_used = True
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('auth.login'))

    return render_template('register_gate.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# API to check code without refreshing page
@bp.route('/api/verify-code', methods=['POST'])
def verify_code():
    data = request.get_json()
    code_str = data.get('code')
    
    code_entry = AccessCode.query.filter_by(code=code_str, is_used=False).first()
    
    if code_entry:
        return jsonify({'valid': True, 'amount': code_entry.balance_value})
    else:
        return jsonify({'valid': False})