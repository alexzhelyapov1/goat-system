import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# JWT Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'fdcd4f0abd3353e7f7d2ba1bed7c4e06e8c9068da5c0ed9792f0e4001d10d85b')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
API_BASE_URL = "http://api:5001" # Internal Docker service name and port

class Config:
    # Flask-related configurations
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess' # This is for Flask's session management
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = 5400
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_BOT_USERNAME = os.environ.get('TELEGRAM_BOT_USERNAME')
    TELEGRAM_ADMIN_CHAT_ID = os.environ.get('TELEGRAM_ADMIN_CHAT_ID', None)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'


