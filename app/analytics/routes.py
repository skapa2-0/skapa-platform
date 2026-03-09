from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.analytics import bp
from app.models import ApiUsageStats, ActivityLog
from app.utils.helpers import get_dashboard_stats, get_admin_dashboard_stats, get_recent_activity_logs
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import json

@bp.route('/')
@login_required
def index():
    """Page principale des analytics pour l'utilisateur"""
    if not current_user.can_login():
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Récupération de la période
    days = request.args.get('days', 30, type=int)
    if days not in [7, 30, 90]:
        days = 30
    
    # Statistiques du tableau de bord
    stats = get_dashboard_stats(current_user.id, days)
    
    # Logs d'activité récents
    recent_logs = get_recent_activity_logs(current_user.id, limit=15)
    
    return render_template('analytics/index.html',
                         title='Analytics',
                         stats=stats,
                         recent_logs=recent_logs,
                         days=days)


@bp.route('/api/chart-data')
@login_required
def api_chart_data():
    """API pour récupérer les données de graphiques"""
    days = request.args.get('days', 30, type=int)
    chart_type = request.args.get('type', 'requests')
    
    stats = get_dashboard_stats(current_user.id, days)
    
    return jsonify({
        'success': True,
        'data': stats['chart_data']
    })


@bp.route('/api/live-stats')
@login_required
def api_live_stats():
    """API pour les statistiques en temps réel"""
    # Requêtes des dernières 24h par heure
    now = datetime.utcnow()
    start_time = now - timedelta(hours=24)
    
    hourly_stats = db.session.query(
        func.date_trunc('hour', ApiUsageStats.created_at).label('hour'),
        func.count(ApiUsageStats.id).label('requests'),
        func.avg(ApiUsageStats.response_time).label('avg_response_time'),
        func.sum(ApiUsageStats.tokens_used).label('tokens')
    ).filter(
        ApiUsageStats.user_id == current_user.id,
        ApiUsageStats.created_at >= start_time
    ).group_by('hour').order_by('hour').all()
    
    # Format pour le graphique
    chart_data = {
        'hours': [],
        'requests': [],
        'response_times': [],
        'tokens': []
    }
    
    for stat in hourly_stats:
        # stat.hour peut être une string ou un objet datetime selon la base de données
        if isinstance(stat.hour, str):
            # Extraire l'heure de la chaîne au format ISO
            hour_str = stat.hour[:16] if len(stat.hour) >= 16 else stat.hour
            chart_data['hours'].append(hour_str[-5:])  # Format HH:MM
        else:
            chart_data['hours'].append(stat.hour.strftime('%H:%M'))
        chart_data['requests'].append(stat.requests or 0)
        chart_data['response_times'].append(round(stat.avg_response_time or 0, 2))
        chart_data['tokens'].append(stat.tokens or 0)
    
    # Statistiques actuelles
    current_stats = {
        'requests_last_hour': ApiUsageStats.query.filter(
            ApiUsageStats.user_id == current_user.id,
            ApiUsageStats.created_at >= now - timedelta(hours=1)
        ).count(),
        'avg_response_time_today': db.session.query(
            func.avg(ApiUsageStats.response_time)
        ).filter(
            ApiUsageStats.user_id == current_user.id,
            func.date(ApiUsageStats.created_at) == now.date()
        ).scalar() or 0,
        'total_tokens_today': db.session.query(
            func.sum(ApiUsageStats.tokens_used)
        ).filter(
            ApiUsageStats.user_id == current_user.id,
            func.date(ApiUsageStats.created_at) == now.date()
        ).scalar() or 0
    }
    
    return jsonify({
        'success': True,
        'chart_data': chart_data,
        'current_stats': current_stats,
        'timestamp': now.isoformat()
    })


@bp.route('/detailed')
@login_required
def detailed():
    """Page d'analytics détaillées"""
    # Statistiques par endpoint
    endpoint_stats = db.session.query(
        ApiUsageStats.endpoint,
        func.count(ApiUsageStats.id).label('count'),
        func.avg(ApiUsageStats.response_time).label('avg_time'),
        func.sum(ApiUsageStats.tokens_used).label('total_tokens')
    ).filter(
        ApiUsageStats.user_id == current_user.id
    ).group_by(ApiUsageStats.endpoint).order_by(desc('count')).all()
    
    # Statistiques par modèle
    model_stats = db.session.query(
        ApiUsageStats.model_used,
        func.count(ApiUsageStats.id).label('count'),
        func.sum(ApiUsageStats.tokens_used).label('total_tokens')
    ).filter(
        ApiUsageStats.user_id == current_user.id,
        ApiUsageStats.model_used.isnot(None)
    ).group_by(ApiUsageStats.model_used).order_by(desc('count')).all()
    
    # Répartition des codes de statut
    status_stats = db.session.query(
        ApiUsageStats.status_code,
        func.count(ApiUsageStats.id).label('count')
    ).filter(
        ApiUsageStats.user_id == current_user.id
    ).group_by(ApiUsageStats.status_code).order_by(desc('count')).all()
    
    return render_template('analytics/detailed.html',
                         title='Analytics détaillées',
                         endpoint_stats=endpoint_stats,
                         model_stats=model_stats,
                         status_stats=status_stats)


@bp.route('/activity')
@login_required
def activity():
    """Page des logs d'activité"""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', 'all')
    
    query = ActivityLog.query.filter_by(user_id=current_user.id)
    
    if action_filter != 'all':
        query = query.filter(ActivityLog.action.contains(action_filter))
    
    logs = query.order_by(desc(ActivityLog.created_at)).paginate(
        page=page, per_page=25, error_out=False
    )
    
    # Actions disponibles pour le filtre
    available_actions = db.session.query(
        ActivityLog.action
    ).filter_by(user_id=current_user.id).distinct().all()
    
    actions = [action[0] for action in available_actions]
    
    return render_template('analytics/activity.html',
                         title='Activité',
                         logs=logs,
                         actions=actions,
                         action_filter=action_filter)


@bp.route('/admin')
@login_required
def admin_analytics():
    """Analytics pour les administrateurs"""
    if not current_user.is_admin():
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('analytics.index'))
    
    # Statistiques générales
    admin_stats = get_admin_dashboard_stats()
    
    # Requêtes par jour (30 derniers jours)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    daily_requests = db.session.query(
        func.date(ApiUsageStats.created_at).label('date'),
        func.count(ApiUsageStats.id).label('requests'),
        func.count(func.distinct(ApiUsageStats.user_id)).label('unique_users')
    ).filter(
        ApiUsageStats.created_at >= start_date
    ).group_by(func.date(ApiUsageStats.created_at)).order_by('date').all()
    
    # Données pour le graphique
    chart_data = {
        'dates': [],
        'requests': [],
        'unique_users': []
    }
    
    for stat in daily_requests:
        # stat.date peut être une string ou un objet date selon la base de données
        if isinstance(stat.date, str):
            chart_data['dates'].append(stat.date)
        else:
            chart_data['dates'].append(stat.date.strftime('%Y-%m-%d'))
        chart_data['requests'].append(stat.requests)
        chart_data['unique_users'].append(stat.unique_users)
    
    return render_template('analytics/admin.html',
                         title='Analytics Admin',
                         admin_stats=admin_stats,
                         chart_data=chart_data)


@bp.route('/export')
@login_required
def export_data():
    """Export des données utilisateur"""
    format_type = request.args.get('format', 'json')
    days = request.args.get('days', 30, type=int)
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Récupération des données
    api_usage = ApiUsageStats.query.filter(
        ApiUsageStats.user_id == current_user.id,
        ApiUsageStats.created_at >= start_date
    ).all()
    
    activity_logs = ActivityLog.query.filter(
        ActivityLog.user_id == current_user.id,
        ActivityLog.created_at >= start_date
    ).all()
    
    if format_type == 'json':
        data = {
            'user_id': current_user.id,
            'user_email': current_user.email,
            'export_date': datetime.utcnow().isoformat(),
            'period_days': days,
            'api_usage': [
                {
                    'endpoint': usage.endpoint,
                    'method': usage.method,
                    'status_code': usage.status_code,
                    'response_time': usage.response_time,
                    'tokens_used': usage.tokens_used,
                    'model_used': usage.model_used,
                    'created_at': usage.created_at.isoformat()
                }
                for usage in api_usage
            ],
            'activity_logs': [
                {
                    'action': log.action,
                    'description': log.description,
                    'ip_address': log.ip_address,
                    'created_at': log.created_at.isoformat()
                }
                for log in activity_logs
            ]
        }
        
        response = jsonify(data)
        response.headers['Content-Disposition'] = f'attachment; filename=analytics_export_{current_user.id}_{datetime.utcnow().strftime("%Y%m%d")}.json'
        return response
    
    # Pour d'autres formats (CSV, etc.) - à implémenter si nécessaire
    return jsonify({'error': 'Format non supporté'}), 400 
