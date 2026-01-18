from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('user', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    # 1. Security Check: Redirect Admins to the Admin Panel
    # (Admins shouldn't see the User view)
    if current_user.role == 'ADMIN':
        return redirect(url_for('admin.dashboard'))
        
    # 2. Render the Investor Dashboard
    return render_template('user_dashboard.html', user=current_user)