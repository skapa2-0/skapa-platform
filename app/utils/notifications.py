from flask import current_app, request
from app import db
from app.models import Notification, AuditLog
from datetime import datetime, timedelta
import json

class NotificationService:
    """Service pour la gestion des notifications"""
    
    @staticmethod
    def create_notification(user_id, title, message, type='info', action_url=None, action_text=None, emit_realtime=True):
        """Crée une nouvelle notification"""
        notification = Notification.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            action_url=action_url,
            action_text=action_text
        )
        
        return notification
    
    @staticmethod
    def notify_user_approved(user):
        """Notification quand un utilisateur est approuvé"""
        return NotificationService.create_notification(
            user_id=user.id,
            title='🎉 Compte approuvé !',
            message=f'Félicitations {user.name} ! Votre compte a été approuvé. Vous pouvez maintenant générer vos clés API.',
            type='success',
            action_url='/dashboard',
            action_text='Accéder au tableau de bord'
        )
    
    @staticmethod
    def notify_api_key_generated(user):
        """Notification quand une clé API est générée"""
        return NotificationService.create_notification(
            user_id=user.id,
            title='🔑 Nouvelle clé API générée',
            message='Une nouvelle clé API a été générée pour votre compte. Assurez-vous de la sauvegarder en lieu sûr.',
            type='info',
            action_url='/dashboard',
            action_text='Voir la clé'
        )
    
    @staticmethod
    def notify_api_key_revoked(user):
        """Notification quand une clé API est révoquée"""
        return NotificationService.create_notification(
            user_id=user.id,
            title='⚠️ Clé API révoquée',
            message='Votre clé API a été révoquée. Générez-en une nouvelle si nécessaire.',
            type='warning',
            action_url='/dashboard',
            action_text='Générer nouvelle clé'
        )
    
    @staticmethod
    def notify_suspicious_activity(user, details):
        """Notification pour activité suspecte"""
        return NotificationService.create_notification(
            user_id=user.id,
            title='🚨 Activité suspecte détectée',
            message=f'Une activité inhabituelle a été détectée sur votre compte : {details}',
            type='error',
            action_url='/dashboard/security',
            action_text='Vérifier la sécurité'
        )
    
    @staticmethod
    def notify_rate_limit_exceeded(user):
        """Notification quand la limite de taux est dépassée"""
        return NotificationService.create_notification(
            user_id=user.id,
            title='📊 Limite de taux dépassée',
            message='Vous avez dépassé la limite de requêtes autorisées. Votre accès pourrait être temporairement restreint.',
            type='warning',
            action_url='/dashboard/usage',
            action_text='Voir l\'utilisation'
        )
    
    @staticmethod
    def get_user_notifications(user_id, limit=20, unread_only=False):
        """Récupère les notifications d'un utilisateur"""
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        return query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def mark_notification_as_read(notification_id, user_id):
        """Marque une notification comme lue"""
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=user_id
        ).first()
        
        if notification and not notification.is_read:
            notification.mark_as_read()
            return True
        return False
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Marque toutes les notifications comme lues"""
        notifications = Notification.query.filter_by(
            user_id=user_id, 
            is_read=False
        ).all()
        
        for notification in notifications:
            notification.mark_as_read()
        
        return len(notifications)

class AuditService:
    """Service pour l'audit et le logging"""
    
    @staticmethod
    def log_action(action, user_id=None, resource_type=None, resource_id=None, details=None):
        """Enregistre une action dans le journal d'audit"""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR')
            user_agent = request.headers.get('User-Agent')
        
        return AuditLog.log_action(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_login(user):
        """Log une connexion utilisateur"""
        return AuditService.log_action(
            action='user_login',
            user_id=user.id,
            resource_type='user',
            resource_id=user.id,
            details={'email': user.email}
        )
    
    @staticmethod
    def log_logout(user):
        """Log une déconnexion utilisateur"""
        return AuditService.log_action(
            action='user_logout',
            user_id=user.id,
            resource_type='user',
            resource_id=user.id
        )
    
    @staticmethod
    def log_api_key_generated(user, api_key):
        """Log la génération d'une clé API"""
        return AuditService.log_action(
            action='api_key_generated',
            user_id=user.id,
            resource_type='api_key',
            resource_id=api_key.id,
            details={'key_prefix': api_key.key_prefix}
        )
    
    @staticmethod
    def log_api_key_revoked(user, api_key):
        """Log la révocation d'une clé API"""
        return AuditService.log_action(
            action='api_key_revoked',
            user_id=user.id,
            resource_type='api_key',
            resource_id=api_key.id,
            details={'key_prefix': api_key.key_prefix}
        )
    
    @staticmethod
    def log_user_approved(admin_user, approved_user):
        """Log l'approbation d'un utilisateur"""
        return AuditService.log_action(
            action='user_approved',
            user_id=admin_user.id,
            resource_type='user',
            resource_id=approved_user.id,
            details={
                'approved_email': approved_user.email,
                'admin_email': admin_user.email
            }
        )
    
    @staticmethod
    def log_api_usage(api_key, endpoint, response_code, response_time=None):
        """Log l'utilisation d'une API"""
        return AuditService.log_action(
            action='api_usage',
            user_id=api_key.user_id,
            resource_type='api_key',
            resource_id=api_key.id,
            details={
                'endpoint': endpoint,
                'response_code': response_code,
                'response_time': response_time
            }
        )
    
    @staticmethod
    def log_failed_login_attempt(email, reason):
        """Log une tentative de connexion échouée"""
        return AuditService.log_action(
            action='failed_login_attempt',
            resource_type='security',
            details={
                'email': email,
                'reason': reason
            }
        )
    
    @staticmethod
    def get_audit_logs(user_id=None, action=None, limit=100, offset=0):
        """Récupère les logs d'audit avec filtres"""
        query = AuditLog.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if action:
            query = query.filter_by(action=action)
        
        return query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_security_alerts(hours=24):
        """Récupère les alertes de sécurité récentes"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        security_actions = [
            'failed_login_attempt',
            'suspicious_activity',
            'rate_limit_exceeded',
            'unauthorized_access_attempt'
        ]
        
        return AuditLog.query.filter(
            AuditLog.action.in_(security_actions),
            AuditLog.timestamp >= since
        ).order_by(AuditLog.timestamp.desc()).all() 