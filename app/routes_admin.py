from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, AccessCode, ActiveTrade, TransactionLog
import secrets
import string
import yfinance as yf  # <--- NEW: Needed to fetch prices for the admin trade

bp = Blueprint('admin', __name__)

# --- Middleware: Protect Admin Routes ---
@bp.before_request
def restrict_admin():
    if not current_user.is_authenticated or current_user.role != 'ADMIN':
        flash("Access Denied: Admins only.")
        return redirect(url_for('auth.login'))

# --- 1. Dashboard & Code Gen ---
@bp.route('/dashboard')
def dashboard():
    # Get all users (excluding the admin themselves)
    users = User.query.filter(User.role != 'ADMIN').all()
    # Get codes (newest first)
    codes = AccessCode.query.order_by(AccessCode.created_at.desc()).all()
    return render_template('admin_panel.html', users=users, codes=codes)

@bp.route('/generate-code', methods=['POST'])
def generate_code():
    try:
        amount = float(request.form.get('amount'))
        
        # Generate random string: XXXX-XXXX
        chars = string.ascii_uppercase + string.digits
        code_str = ''.join(secrets.choice(chars) for _ in range(8))
        formatted_code = f"{code_str[:4]}-{code_str[4:]}"
        
        new_code = AccessCode(code=formatted_code, balance_value=amount)
        db.session.add(new_code)
        db.session.commit()
        
        flash(f"Success: Code {formatted_code} created for ${amount:,.2f}")
    except Exception as e:
        flash(f"Error generating code: {e}")
        
    return redirect(url_for('admin.dashboard'))

@bp.route('/delete-code/<int:code_id>')
def delete_code(code_id):
    code = AccessCode.query.get(code_id)
    if code:
        db.session.delete(code)
        db.session.commit()
        flash("Invite code deleted.")
    return redirect(url_for('admin.dashboard'))

# --- 2. Financial Management ---
@bp.route('/user/update-balance', methods=['POST'])
def update_balance():
    user_id = request.form.get('user_id')
    amount = float(request.form.get('amount'))
    action_type = request.form.get('type') # 'DEPOSIT' or 'WITHDRAWAL'
    
    user = User.query.get(user_id)
    
    if not user:
        flash("User not found.")
        return redirect(url_for('admin.dashboard'))

    log_desc = ""

    if action_type == 'DEPOSIT':
        user.wallet_balance += amount
        log_desc = f"Admin Deposit by {current_user.username}"
        flash(f"Deposited ${amount} to {user.username}")
        
    elif action_type == 'WITHDRAWAL':
        if user.wallet_balance < amount:
            flash(f"Error: {user.username} only has ${user.wallet_balance}")
            return redirect(url_for('admin.dashboard'))
            
        user.wallet_balance -= amount
        log_desc = f"Admin Withdrawal by {current_user.username}"
        flash(f"Withdrew ${amount} from {user.username}")

    # Create a Transaction Log so the user sees it in history
    log = TransactionLog(
        user_id=user.id,
        type=action_type,
        amount=amount,
        description=log_desc
    )
    
    db.session.add(log)
    db.session.commit()
    
    return redirect(url_for('admin.dashboard'))

# --- 3. Account Security ---
@bp.route('/user/reset-password', methods=['POST'])
def reset_password():
    user_id = request.form.get('user_id')
    new_password = request.form.get('new_password')
    
    user = User.query.get(user_id)
    if user:
        user.set_password(new_password)
        db.session.commit()
        flash(f"Password for {user.username} has been reset.")
    
    return redirect(url_for('admin.dashboard'))

@bp.route('/user/delete/<int:user_id>')
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        # Cleanup: Delete their active trades first to avoid DB errors
        trades = ActiveTrade.query.filter_by(user_id=user.id).all()
        for t in trades:
            db.session.delete(t)
            
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.username} and all their data deleted.")
        
    return redirect(url_for('admin.dashboard'))

# --- 4. Trade Execution (NEW: Admin trades for User) ---
@bp.route('/user/place-trade', methods=['POST'])
def place_trade_for_user():
    user_id = request.form.get('user_id')
    symbol = request.form.get('symbol').upper()
    direction = request.form.get('direction')
    quantity = float(request.form.get('quantity'))
    
    user = User.query.get(user_id)
    
    if not user:
        flash("User not found.")
        return redirect(url_for('admin.dashboard'))

    # Fetch Real Price from Market
    try:
        ticker = yf.Ticker(symbol)
        # Get last closed price
        current_price = ticker.history(period="1d")['Close'].iloc[-1]
    except:
        flash(f"Error: Could not find market data for symbol '{symbol}'")
        return redirect(url_for('admin.dashboard'))

    # Calculate Cost (Optional: You can allow negative balance if you want)
    cost = current_price * quantity
    
    # Execute Trade Logic
    user.wallet_balance -= cost
    
    new_trade = ActiveTrade(
        user_id=user.id,
        symbol=symbol,
        direction=direction,
        quantity=quantity,
        entry_price=current_price
    )
    
    db.session.add(new_trade)
    db.session.commit()
    
    flash(f"Successfully opened {direction} {symbol} for {user.username} at ${current_price:,.2f}")
    return redirect(url_for('admin.dashboard'))