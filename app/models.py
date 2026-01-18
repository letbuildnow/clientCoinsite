from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# --- The User Model ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(10), default='USER') # 'ADMIN' or 'USER'
    
    # Financials
    wallet_balance = db.Column(db.Float, default=0.0) # Available Cash
    
    # Relationships
    used_code_id = db.Column(db.Integer, db.ForeignKey('access_code.id'))
    trades = db.relationship('ActiveTrade', backref='trader', lazy='dynamic')
    transactions = db.relationship('TransactionLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def equity(self):
        # Calculate Total Equity (Cash + Unrealized PnL from open trades)
        unrealized_pnl = sum([t.current_pnl for t in self.trades])
        return self.wallet_balance + unrealized_pnl

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# --- The Invite Code System ---
class AccessCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, index=True)
    balance_value = db.Column(db.Float, nullable=False) # e.g. 50000.00
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- Trading Models ---
class ActiveTrade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    symbol = db.Column(db.String(10)) # e.g. EURUSD
    entry_price = db.Column(db.Float)
    quantity = db.Column(db.Float)
    direction = db.Column(db.String(4)) # 'BUY' or 'SELL'
    current_pnl = db.Column(db.Float, default=0.0) # Updated by Cron Job
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class TransactionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.String(20)) # 'DEPOSIT', 'WITHDRAWAL', 'PROFIT', 'LOSS'
    amount = db.Column(db.Float)
    description = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)