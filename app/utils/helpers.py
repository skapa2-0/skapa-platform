from flask import request
from datetime import datetime, timedelta
from app import db
from app.models import Notification, ActivityLog, ApiUsageStats, UserPreferences
from sqlalchemy import func, desc
import json


def create_notification(user_id, title, message, type='info', action_url=None, action_text=None):
    """Crée une nouvelle notification pour un utilisateur"""
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


def log_user_activity(user_id=None, action='', description='', extra_data=None):
    """Enregistre une activité utilisateur"""
    ip_address = request.remote_addr if request else None
    user_agent = request.headers.get('User-Agent') if request else None
    endpoint = request.endpoint if request else None
    method = request.method if request else None
    
    ActivityLog.log_activity(
        user_id=user_id,
        action=action,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        endpoint=endpoint,
        method=method,
        extra_data=extra_data
    )


def get_user_preferences(user_id):
    """Récupère les préférences d'un utilisateur (les crée si elles n'existent pas)"""
    preferences = UserPreferences.query.filter_by(user_id=user_id).first()
    if not preferences:
        preferences = UserPreferences(user_id=user_id)
        db.session.add(preferences)
        db.session.commit()
    return preferences


def get_dashboard_stats(user_id, days=30):
    """Récupère les statistiques pour le dashboard utilisateur"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Statistiques d'utilisation API
    api_stats = db.session.query(
        func.date(ApiUsageStats.created_at).label('date'),
        func.count(ApiUsageStats.id).label('requests'),
        func.sum(ApiUsageStats.tokens_used).label('tokens'),
        func.avg(ApiUsageStats.response_time).label('avg_response_time')
    ).filter(
        ApiUsageStats.user_id == user_id,
        ApiUsageStats.created_at >= start_date
    ).group_by(func.date(ApiUsageStats.created_at)).all()
    
    # Conversion en format JSON pour les graphiques
    chart_data = {
        'dates': [],
        'requests': [],
        'tokens': [],
        'response_times': []
    }
    
    for stat in api_stats:
        chart_data['dates'].append(stat.date.strftime('%Y-%m-%d'))
        chart_data['requests'].append(stat.requests or 0)
        chart_data['tokens'].append(stat.tokens or 0)
        chart_data['response_times'].append(round(stat.avg_response_time or 0, 2))
    
    # Statistiques générales
    total_requests = ApiUsageStats.query.filter(
        ApiUsageStats.user_id == user_id
    ).count()
    
    total_tokens = db.session.query(
        func.sum(ApiUsageStats.tokens_used)
    ).filter(ApiUsageStats.user_id == user_id).scalar() or 0
    
    avg_response_time = db.session.query(
        func.avg(ApiUsageStats.response_time)
    ).filter(ApiUsageStats.user_id == user_id).scalar() or 0
    
    # Requêtes des dernières 24h
    last_24h_requests = ApiUsageStats.query.filter(
        ApiUsageStats.user_id == user_id,
        ApiUsageStats.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    return {
        'chart_data': chart_data,
        'total_requests': total_requests,
        'total_tokens': int(total_tokens),
        'avg_response_time': round(avg_response_time or 0, 2),
        'last_24h_requests': last_24h_requests
    }


def get_admin_dashboard_stats():
    """Récupère les statistiques pour le dashboard admin"""
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Statistiques des utilisateurs
    from app.models import User
    total_users = User.query.count()
    new_users_today = User.query.filter(
        func.date(User.created_at) == today
    ).count()
    new_users_week = User.query.filter(
        func.date(User.created_at) >= week_ago
    ).count()
    
    # Statistiques API
    total_api_requests = ApiUsageStats.query.count()
    api_requests_today = ApiUsageStats.query.filter(
        func.date(ApiUsageStats.created_at) == today
    ).count()
    api_requests_week = ApiUsageStats.query.filter(
        func.date(ApiUsageStats.created_at) >= week_ago
    ).count()
    
    # Top utilisateurs par requêtes
    top_users = db.session.query(
        User.name,
        User.email,
        func.count(ApiUsageStats.id).label('request_count')
    ).join(ApiUsageStats).group_by(
        User.id, User.name, User.email
    ).order_by(desc('request_count')).limit(5).all()
    
    # Endpoints les plus utilisés
    top_endpoints = db.session.query(
        ApiUsageStats.endpoint,
        func.count(ApiUsageStats.id).label('count')
    ).group_by(ApiUsageStats.endpoint).order_by(desc('count')).limit(5).all()
    
    return {
        'users': {
            'total': total_users,
            'new_today': new_users_today,
            'new_week': new_users_week
        },
        'api': {
            'total_requests': total_api_requests,
            'requests_today': api_requests_today,
            'requests_week': api_requests_week
        },
        'top_users': [{'name': u.name, 'email': u.email, 'requests': u.request_count} for u in top_users],
        'top_endpoints': [{'endpoint': e.endpoint, 'count': e.count} for e in top_endpoints]
    }


def get_recent_activity_logs(user_id=None, limit=10):
    """Récupère les logs d'activité récents"""
    query = ActivityLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    return query.order_by(desc(ActivityLog.created_at)).limit(limit).all()


def format_file_size(size_bytes):
    """Formate une taille en bytes en format lisible"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def get_time_ago(datetime_obj):
    """Retourne une chaîne 'il y a X temps' pour une datetime"""
    if not datetime_obj:
        return "Jamais"
    
    now = datetime.utcnow()
    diff = now - datetime_obj
    
    if diff.days > 0:
        if diff.days == 1:
            return "Il y a 1 jour"
        return f"Il y a {diff.days} jours"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        if hours == 1:
            return "Il y a 1 heure"
        return f"Il y a {hours} heures"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        if minutes == 1:
            return "Il y a 1 minute"
        return f"Il y a {minutes} minutes"
    else:
        return "À l'instant"


def nl2br(text):
    """Convertit les retours à la ligne en balises HTML <br>"""
    if not text:
        return text
    from markupsafe import Markup
    return Markup(text.replace('\n', '<br>\n').replace('\r\n', '<br>\n').replace('\r', '<br>\n')) 