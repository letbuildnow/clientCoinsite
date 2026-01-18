from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Initialize Plugins
db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login' # Where to send users if they aren't logged in

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Init extensions
    db.init_app(app)
    login.init_app(app)

    # Register Blueprints (We will create these files in Phase 2)
    from app.routes_auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.routes_admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.routes_user import bp as user_bp
    app.register_blueprint(user_bp)

    # Create Database Tables automatically
    with app.app_context():
        db.create_all()

    return app

from app import models # Import models to ensure they are registered