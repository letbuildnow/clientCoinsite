import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Security Key (Change this to a random long string in production)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-change-me'
    
    # Database Settings (Using SQLite for now, easy to switch to PostgreSQL later)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False