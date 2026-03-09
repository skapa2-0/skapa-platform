from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_caching import Cache
from flask_cors import CORS
from flasgger import Swagger
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
cache = Cache()
cors = CORS()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    cors.init_app(app)
    
    # Configuration Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api-docs/",
        "title": app.config['SWAGGER']['title'],
        "version": app.config['SWAGGER']['version'],
        "description": app.config['SWAGGER']['description']
    }
    swagger = Swagger(app, config=swagger_config)
    
    # Configuration Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    # Enregistrement des blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Nouveaux blueprints
    from app.notifications import bp as notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    
    from app.support import bp as support_bp
    app.register_blueprint(support_bp, url_prefix='/support')
    
    from app.analytics import bp as analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    # Filtres de template globaux
    from app.utils.helpers import get_time_ago, format_file_size, nl2br
    app.jinja_env.filters['time_ago'] = get_time_ago
    app.jinja_env.filters['file_size'] = format_file_size
    app.jinja_env.filters['nl2br'] = nl2br
    
    return app

from app import models 