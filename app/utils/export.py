import csv
import json
from io import StringIO
from datetime import datetime, timedelta
from flask import current_app
from app.models import User, ApiKey, AuditLog, ApiUsageStats, Notification
from app import db
from sqlalchemy import func, desc

class ExportService:
    """Service pour l'export de données"""
    
    @staticmethod
    def export_users_csv(include_sensitive=False):
        """Exporte les utilisateurs en CSV"""
        output = StringIO()
        
        # Headers
        headers = ['ID', 'Email', 'Nom', 'Statut', 'Role', 'Date création', 'Date approbation', 'Dernière connexion', 'Nb connexions']
        if include_sensitive:
            headers.extend(['Justification', 'Email vérifié'])
        
        writer = csv.writer(output)
        writer.writerow(headers)
        
        # Données
        users = User.query.limit(current_app.config['MAX_EXPORT_RECORDS']).all()
        
        for user in users:
            row = [
                user.id,
                user.email,
                user.name,
                user.status,
                user.role,
                user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                user.approved_at.strftime('%Y-%m-%d %H:%M:%S') if user.approved_at else '',
                user.last_login_at.strftime('%Y-%m-%d %H:%M:%S') if user.last_login_at else '',
                user.login_count or 0
            ]
            
            if include_sensitive:
                row.extend([
                    user.justification,
                    'Oui' if user.email_verified_at else 'Non'
                ])
            
            writer.writerow(row)
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def export_api_keys_csv():
        """Exporte les clés API en CSV"""
        output = StringIO()
        
        headers = ['ID', 'User ID', 'Email utilisateur', 'Préfixe clé', 'Nom', 'Active', 'Date création', 'Dernière utilisation', 'Nb utilisations']
        writer = csv.writer(output)
        writer.writerow(headers)
        
        # Requête avec JOIN pour récupérer l'email
        api_keys = db.session.query(ApiKey, User.email).join(User).limit(current_app.config['MAX_EXPORT_RECORDS']).all()
        
        for api_key, user_email in api_keys:
            row = [
                api_key.id,
                api_key.user_id,
                user_email,
                api_key.key_prefix,
                api_key.name,
                'Oui' if api_key.is_active else 'Non',
                api_key.created_at.strftime('%Y-%m-%d %H:%M:%S') if api_key.created_at else '',
                api_key.last_used_at.strftime('%Y-%m-%d %H:%M:%S') if api_key.last_used_at else '',
                api_key.usage_count or 0
            ]
            writer.writerow(row)
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def export_audit_logs_csv(user_id=None, days=30):
        """Exporte les logs d'audit en CSV"""
        output = StringIO()
        
        headers = ['ID', 'User ID', 'Email utilisateur', 'Action', 'Type ressource', 'ID ressource', 'Adresse IP', 'Date/Heure', 'Détails']
        writer = csv.writer(output)
        writer.writerow(headers)
        
        # Filtrer par date
        since = datetime.utcnow() - timedelta(days=days)
        query = db.session.query(AuditLog, User.email).outerjoin(User).filter(AuditLog.timestamp >= since)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        logs = query.order_by(AuditLog.timestamp.desc()).limit(current_app.config['MAX_EXPORT_RECORDS']).all()
        
        for log, user_email in logs:
            row = [
                log.id,
                log.user_id or '',
                user_email or '',
                log.action,
                log.resource_type or '',
                log.resource_id or '',
                log.ip_address or '',
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.details or ''
            ]
            writer.writerow(row)
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def export_usage_stats_csv(days=30):
        """Exporte les statistiques d'utilisation en CSV"""
        output = StringIO()
        
        headers = ['Date', 'Clé API ID', 'Préfixe clé', 'Email utilisateur', 'Requêtes', 'Erreurs', 'Temps réponse moyen (ms)', 'Données transférées (bytes)']
        writer = csv.writer(output)
        writer.writerow(headers)
        
        # Filtrer par date
        since = datetime.utcnow().date() - timedelta(days=days)
        
        stats = db.session.query(
            ApiUsageStats, ApiKey.key_prefix, User.email
        ).join(
            ApiKey, ApiUsageStats.api_key_id == ApiKey.id
        ).join(
            User, ApiKey.user_id == User.id
        ).filter(
            ApiUsageStats.date >= since
        ).order_by(
            ApiUsageStats.date.desc()
        ).limit(current_app.config['MAX_EXPORT_RECORDS']).all()
        
        for stat, key_prefix, user_email in stats:
            row = [
                stat.date.strftime('%Y-%m-%d'),
                stat.api_key_id,
                key_prefix,
                user_email,
                stat.requests_count,
                stat.errors_count,
                round(stat.response_time_avg, 2),
                stat.data_transferred
            ]
            writer.writerow(row)
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def export_users_json(include_sensitive=False):
        """Exporte les utilisateurs en JSON"""
        users = User.query.limit(current_app.config['MAX_EXPORT_RECORDS']).all()
        
        users_data = []
        for user in users:
            user_data = {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'status': user.status,
                'role': user.role,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'approved_at': user.approved_at.isoformat() if user.approved_at else None,
                'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
                'login_count': user.login_count
            }
            
            if include_sensitive:
                user_data.update({
                    'justification': user.justification,
                    'email_verified': user.email_verified_at is not None
                })
            
            users_data.append(user_data)
        
        return json.dumps({
            'export_date': datetime.utcnow().isoformat(),
            'total_records': len(users_data),
            'users': users_data
        }, indent=2, ensure_ascii=False)
    
    @staticmethod
    def export_api_keys_json():
        """Exporte les clés API en JSON"""
        api_keys = db.session.query(ApiKey, User.email).join(User).limit(current_app.config['MAX_EXPORT_RECORDS']).all()
        
        keys_data = []
        for api_key, user_email in api_keys:
            key_data = {
                'id': api_key.id,
                'user_id': api_key.user_id,
                'user_email': user_email,
                'key_prefix': api_key.key_prefix,
                'name': api_key.name,
                'is_active': api_key.is_active,
                'created_at': api_key.created_at.isoformat() if api_key.created_at else None,
                'last_used_at': api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                'usage_count': api_key.usage_count
            }
            keys_data.append(key_data)
        
        return json.dumps({
            'export_date': datetime.utcnow().isoformat(),
            'total_records': len(keys_data),
            'api_keys': keys_data
        }, indent=2, ensure_ascii=False)
    
    @staticmethod
    def generate_system_report():
        """Génère un rapport système complet"""
        # Statistiques générales
        total_users = User.query.count()
        active_users = User.query.filter_by(status='approved').count()
        total_api_keys = ApiKey.query.filter_by(is_active=True).count()
        
        # Utilisation récente
        today = datetime.utcnow().date()
        today_stats = db.session.query(
            func.sum(ApiUsageStats.requests_count).label('requests'),
            func.sum(ApiUsageStats.errors_count).label('errors')
        ).filter(ApiUsageStats.date == today).first()
        
        # Top utilisateurs
        top_users = db.session.query(
            User.email,
            func.sum(ApiUsageStats.requests_count).label('total_requests')
        ).join(ApiKey).join(ApiUsageStats).group_by(User.email).order_by(
            desc('total_requests')
        ).limit(10).all()
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_users': total_users,
                'active_users': active_users,
                'total_api_keys': total_api_keys,
                'today_requests': today_stats.requests or 0 if today_stats else 0,
                'today_errors': today_stats.errors or 0 if today_stats else 0
            },
            'top_users': [
                {'email': user.email, 'total_requests': user.total_requests}
                for user in top_users
            ]
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False) 