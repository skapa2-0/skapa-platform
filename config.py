import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-me-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@skapa.design'

    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@skapa.design'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'

    API_RATE_LIMIT = int(os.environ.get('API_RATE_LIMIT') or 100)

    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

    MONITORING_ENABLED = os.environ.get('MONITORING_ENABLED', 'true').lower() in ['true', 'on', '1']
    METRICS_RETENTION_DAYS = int(os.environ.get('METRICS_RETENTION_DAYS') or 30)

    BACKUP_ENABLED = False

    ENABLE_PUSH_NOTIFICATIONS = False

    MAX_EXPORT_RECORDS = int(os.environ.get('MAX_EXPORT_RECORDS') or 10000)

    SWAGGER = {
        'title': 'Skapa Platform API',
        'version': '1.0.0',
        'description': 'API de gestion des utilisateurs et clés API — Skapa',
        'contact': {
            'name': 'Skapa Support',
            'email': 'contact@skapa.design'
        },
        'license': {
            'name': 'MIT'
        }
    } 