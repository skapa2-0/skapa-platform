from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import hashlib
import base64
import os
import json
from app import db, login_manager

# Clé de chiffrement pour les clés API (en production, utiliser une variable d'environnement)
ENCRYPTION_KEY = os.environ.get('API_ENCRYPTION_KEY', 'demo-key-32-chars-long-changeme!!')

def get_cipher():
    """Obtient l'objet cipher pour chiffrer/déchiffrer les clés API"""
    key = base64.urlsafe_b64encode(ENCRYPTION_KEY.encode()[:32].ljust(32, b'0'))
    from cryptography.fernet import Fernet
    return Fernet(key)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    justification = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending_email_verification')
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    email_verified_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    last_login_at = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    # suspended_at = db.Column(db.DateTime)
    # suspended_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relations
    api_keys = db.relationship('ApiKey', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    email_tokens = db.relationship('EmailToken', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', foreign_keys='AuditLog.user_id', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    user_preferences = db.relationship('UserPreferences', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_approved(self):
        return self.status == 'approved'
    
    def can_login(self):
        # Un admin peut toujours se connecter
        if self.is_admin():
            return True
        # Pour les autres utilisateurs, les conditions habituelles s'appliquent
        return self.status == 'approved' and self.email_verified_at is not None and self.status != 'suspended'
    
    def record_login(self):
        """Enregistre une connexion"""
        self.last_login_at = datetime.utcnow()
        self.login_count += 1
        db.session.commit()
    
    def generate_api_key(self):
        """Génère une nouvelle clé API pour l'utilisateur"""
        # Révoque l'ancienne clé si elle existe
        old_key = ApiKey.query.filter_by(user_id=self.id, is_active=True).first()
        if old_key:
            old_key.revoke()
        
        # Crée une nouvelle clé
        api_key = ApiKey(user_id=self.id)
        full_key = api_key.generate_key()
        db.session.add(api_key)
        db.session.commit()
        return api_key, full_key
    
    def get_active_api_key(self):
        return ApiKey.query.filter_by(user_id=self.id, is_active=True).first()
    
    def get_preferences(self):
        """Récupère ou crée les préférences utilisateur"""
        if not self.user_preferences:
            prefs = UserPreferences(user_id=self.id)
            db.session.add(prefs)
            db.session.commit()
        return self.user_preferences
    
    def get_unread_notifications_count(self):
        """Compte les notifications non lues"""
        return self.notifications.filter_by(is_read=False).count()
    
    def __repr__(self):
        return f'<User {self.email}>'

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key_hash = db.Column(db.String(255), nullable=False, unique=True)
    encrypted_key = db.Column(db.Text, nullable=True)  # Clé chiffrée pour récupération
    full_key = db.Column(db.String(255), nullable=True)
    key_prefix = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), default='Clé API principale')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)
    revoked_at = db.Column(db.DateTime)
    usage_count = db.Column(db.Integer, default=0)
    
    # Relations pour les statistiques
    usage_stats = db.relationship('ApiUsageStats', backref='api_key', lazy='dynamic', cascade='all, delete-orphan')
    
    def generate_key(self):
        """Génère une nouvelle clé API"""
        # Génère une clé de 32 caractères
        raw_key = secrets.token_urlsafe(32)
        self.key_prefix = f"ak_{raw_key[:8]}"
        full_key_value = f"ak_{raw_key}"
        
        # Hash la clé pour le stockage et la validation
        self.key_hash = hashlib.sha256(full_key_value.encode()).hexdigest()
        self.full_key = full_key_value
        
        # Optionnellement chiffre et stocke la clé pour récupération ultérieure
        try:
            from app.utils.encryption import get_cipher
            cipher = get_cipher()
            self.encrypted_key = cipher.encrypt(full_key_value.encode()).decode()
        except ImportError:
            # Si le module de chiffrement n'est pas disponible, on stocke en clair (pour dev)
            pass
        
        return full_key_value
    
    def reconstruct_key(self):
        """Récupère la clé complète à partir de la version chiffrée ou stockée"""
        # Préférer la version déchiffrée si disponible
        if self.encrypted_key:
            try:
                from app.utils.encryption import get_cipher
                cipher = get_cipher()
                decrypted_key = cipher.decrypt(self.encrypted_key.encode()).decode()
                return decrypted_key
            except (ImportError, Exception):
                pass
        
        # Sinon utiliser la version en clair
        if self.full_key:
            return self.full_key
            
        return None
    
    def verify_key(self, key):
        """Vérifie si une clé correspond à cette entrée"""
        return self.key_hash == hashlib.sha256(key.encode()).hexdigest()
    
    def revoke(self):
        """Révoque la clé API"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
    
    def update_last_used(self):
        """Met à jour la date de dernière utilisation et le compteur"""
        self.last_used_at = datetime.utcnow()
        self.usage_count += 1
        db.session.commit()
    
    @staticmethod
    def find_by_key(key):
        """Trouve une clé API active par sa valeur"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return ApiKey.query.filter_by(key_hash=key_hash, is_active=True).first()
    
    def __repr__(self):
        return f'<ApiKey {self.key_prefix}... for user {self.user_id}>'

class EmailToken(db.Model):
    __tablename__ = 'email_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), nullable=False, unique=True)
    token_type = db.Column(db.String(50), nullable=False)  # 'email_verification', 'password_reset'
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    
    def __init__(self, user_id, token_type, expires_in_hours=24):
        self.user_id = user_id
        self.token_type = token_type
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    
    def is_valid(self):
        """Vérifie si le token est valide (non utilisé et non expiré)"""
        return self.used_at is None and datetime.utcnow() < self.expires_at
    
    def use_token(self):
        """Marque le token comme utilisé"""
        self.used_at = datetime.utcnow()
    
    @staticmethod
    def find_valid_token(token, token_type):
        """Trouve un token valide par sa valeur et son type"""
        email_token = EmailToken.query.filter_by(token=token, token_type=token_type).first()
        if email_token and email_token.is_valid():
            return email_token
        return None
    
    def __repr__(self):
        return f'<EmailToken {self.token_type} for user {self.user_id}>' 


class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    theme = db.Column(db.String(20), default='auto')  # 'light', 'dark', 'auto'
    language = db.Column(db.String(10), default='fr')  # 'fr', 'en'
    notifications_email = db.Column(db.Boolean, default=True)
    notifications_browser = db.Column(db.Boolean, default=True)
    dashboard_refresh_rate = db.Column(db.Integer, default=30)  # en secondes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserPreferences for user {self.user_id}>'


class AuditLog(db.Model):
    """Journal d'audit pour tracer toutes les actions importantes"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # 'login', 'api_key_generated', 'user_approved', etc.
    resource_type = db.Column(db.String(50))  # 'user', 'api_key', 'system'
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON avec détails supplémentaires
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    @staticmethod
    def log_action(action, user_id=None, resource_type=None, resource_id=None, 
                   details=None, ip_address=None, user_agent=None):
        """Enregistre une action dans le journal d'audit"""
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    def get_details(self):
        """Récupère les détails sous forme de dictionnaire"""
        return json.loads(self.details) if self.details else {}
    
    def __repr__(self):
        return f'<AuditLog {self.action} by user {self.user_id}>'

class Notification(db.Model):
    """Système de notifications pour les utilisateurs"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # 'info', 'success', 'warning', 'error'
    is_read = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String(500))  # URL optionnelle pour action
    action_text = db.Column(db.String(100))  # Texte du bouton d'action
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    @staticmethod
    def create_notification(user_id, title, message, type='info', action_url=None, action_text=None):
        """Crée une nouvelle notification"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            action_url=action_url,
            action_text=action_text
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    def mark_as_read(self):
        """Marque la notification comme lue"""
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def to_dict(self):
        """Convertit la notification en dictionnaire pour JSON"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'action_url': self.action_url,
            'action_text': self.action_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
    
    def __repr__(self):
        return f'<Notification {self.title} for user {self.user_id}>'

# Fin des modèles de base


class ActivityLog(db.Model):
    """Journal des activités utilisateurs"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    @staticmethod
    def log_activity(user_id=None, action=None, description=None, ip_address=None, 
                    user_agent=None, endpoint=None, method=None, extra_data=None):
        """Enregistre une activité utilisateur"""
        # Utilise seulement les champs supportés par ActivityLog
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            description=description,
            ip_address=ip_address
        )
        db.session.add(activity)
        db.session.commit()
        return activity
    
    def __repr__(self):
        return f'<ActivityLog {self.action} by user {self.user_id}>'



class SystemMetrics(db.Model):
    """Métriques système globales"""
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    metric_unit = db.Column(db.String(20))  # 'count', 'bytes', 'ms', etc.
    category = db.Column(db.String(50))  # 'performance', 'usage', 'errors'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    @staticmethod
    def record_metric(name, value, unit=None, category=None):
        """Enregistre une métrique système"""
        metric = SystemMetrics(
            metric_name=name,
            metric_value=value,
            metric_unit=unit,
            category=category
        )
        db.session.add(metric)
        db.session.commit()
        return metric
    
    def __repr__(self):
        return f'<SystemMetrics {self.metric_name}: {self.metric_value}>'


class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='open')  # 'open', 'in_progress', 'resolved', 'closed'
    priority = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high', 'urgent'
    category = db.Column(db.String(50), default='general')  # 'general', 'technical', 'billing', 'api'
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolution = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # Relations
    user = db.relationship('User', foreign_keys=[user_id], backref='support_tickets')
    assignee = db.relationship('User', foreign_keys=[assigned_to])
    messages = db.relationship('SupportMessage', backref='ticket', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_status_badge_class(self):
        """Retourne la classe CSS pour le badge de statut"""
        classes = {
            'open': 'bg-primary',
            'in_progress': 'bg-warning',
            'resolved': 'bg-success',
            'closed': 'bg-secondary'
        }
        return classes.get(self.status, 'bg-secondary')
    
    def get_priority_badge_class(self):
        """Retourne la classe CSS pour le badge de priorité"""
        classes = {
            'low': 'bg-secondary',
            'medium': 'bg-info',
            'high': 'bg-warning',
            'urgent': 'bg-danger'
        }
        return classes.get(self.priority, 'bg-secondary')
    
    def can_be_replied_to(self):
        """Vérifie si le ticket peut recevoir des réponses"""
        return self.status in ['open', 'in_progress', 'closed']
    
    def can_be_closed_by_user(self):
        """Vérifie si l'utilisateur peut fermer le ticket"""
        return self.status in ['open', 'in_progress']
    
    def can_be_reopened(self):
        """Vérifie si le ticket peut être rouvert"""
        return self.status == 'closed'
    
    def get_last_message(self):
        """Retourne le dernier message du ticket"""
        return self.messages.order_by(SupportMessage.created_at.desc()).first()
    
    def get_message_count(self):
        """Retourne le nombre de messages dans le ticket"""
        return self.messages.count()
    
    def has_unread_staff_messages(self, user_id):
        """Vérifie s'il y a des messages du staff non lus par l'utilisateur"""
        # Pour le moment, on considère tous les messages staff comme lus
        # On pourrait ajouter un système de lecture plus tard
        return False
    
    def __repr__(self):
        return f'<SupportTicket {self.subject} by user {self.user_id}>'


class SupportMessage(db.Model):
    """Messages/réponses des tickets de support"""
    __tablename__ = 'support_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_staff = db.Column(db.Boolean, default=False)  # True si réponse d'un admin/staff
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    user = db.relationship('User', backref='support_messages')
    
    def __repr__(self):
        return f'<SupportMessage for ticket {self.ticket_id} by user {self.user_id}>'


class ApiUsageStats(db.Model):
    __tablename__ = 'api_usage_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=False)
    endpoint = db.Column(db.String(200), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    response_time = db.Column(db.Float)  # en millisecondes
    tokens_used = db.Column(db.Integer, default=0)
    model_used = db.Column(db.String(100))
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    request_size = db.Column(db.Integer)  # taille de la requête en bytes
    response_size = db.Column(db.Integer)  # taille de la réponse en bytes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    user = db.relationship('User', backref='api_usage_stats')
    
    @staticmethod
    def log_api_usage(user_id, api_key_id, endpoint, method, status_code, 
                     response_time=None, tokens_used=0, model_used=None, 
                     ip_address=None, user_agent=None, request_size=None, 
                     response_size=None):
        """Enregistre l'utilisation de l'API"""
        stat = ApiUsageStats(
            user_id=user_id,
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            tokens_used=tokens_used,
            model_used=model_used,
            ip_address=ip_address,
            user_agent=user_agent,
            request_size=request_size,
            response_size=response_size
        )
        db.session.add(stat)
        db.session.commit()
        return stat
    
    def __repr__(self):
        return f'<ApiUsageStats {self.endpoint} by user {self.user_id}>'
