from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app import db, cache
from app.models import User, ApiKey, ApiUsageStats, AuditLog, SystemMetrics
import plotly.graph_objs as go
import plotly.utils
import json

class AnalyticsService:
    """Service pour les analyses et statistiques"""
    
    @staticmethod
    @cache.memoize(timeout=300)  # Cache 5 minutes
    def get_dashboard_stats():
        """Récupère les statistiques principales pour le dashboard"""
        total_users = User.query.count()
        active_users = User.query.filter_by(status='approved').count()
        pending_users = User.query.filter_by(status='pending_email_verification').count()
        total_api_keys = ApiKey.query.filter_by(is_active=True).count()
        
        # Statistiques d'aujourd'hui
        today = datetime.utcnow().date()
        today_stats = db.session.query(
            func.sum(ApiUsageStats.requests_count).label('requests'),
            func.sum(ApiUsageStats.errors_count).label('errors'),
            func.avg(ApiUsageStats.response_time_avg).label('avg_response_time')
        ).filter(ApiUsageStats.date == today).first()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'pending_users': pending_users,
            'total_api_keys': total_api_keys,
            'today_requests': today_stats.requests or 0,
            'today_errors': today_stats.errors or 0,
            'avg_response_time': round(today_stats.avg_response_time or 0, 2)
        }
    
    @staticmethod
    @cache.memoize(timeout=600)  # Cache 10 minutes
    def get_usage_chart_data(days=30):
        """Génère les données pour le graphique d'utilisation"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Requête pour récupérer les statistiques par jour
        stats = db.session.query(
            ApiUsageStats.date,
            func.sum(ApiUsageStats.requests_count).label('total_requests'),
            func.sum(ApiUsageStats.errors_count).label('total_errors')
        ).filter(
            ApiUsageStats.date.between(start_date, end_date)
        ).group_by(ApiUsageStats.date).order_by(ApiUsageStats.date).all()
        
        # Préparer les données pour Plotly
        dates = []
        requests = []
        errors = []
        
        for stat in stats:
            dates.append(stat.date.strftime('%Y-%m-%d'))
            requests.append(stat.total_requests)
            errors.append(stat.total_errors)
        
        # Créer le graphique
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=requests,
            mode='lines+markers',
            name='Requêtes',
            line=dict(color='#007bff')
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=errors,
            mode='lines+markers',
            name='Erreurs',
            line=dict(color='#dc3545'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Utilisation de l\'API (30 derniers jours)',
            xaxis_title='Date',
            yaxis_title='Nombre de requêtes',
            yaxis2=dict(
                title='Nombre d\'erreurs',
                overlaying='y',
                side='right'
            ),
            hovermode='x unified'
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    @staticmethod
    @cache.memoize(timeout=300)
    def get_user_activity_data():
        """Données d'activité des utilisateurs"""
        # Nouveaux utilisateurs par mois
        monthly_users = db.session.query(
            func.date_trunc('month', User.created_at).label('month'),
            func.count(User.id).label('count')
        ).group_by(func.date_trunc('month', User.created_at)).order_by('month').all()
        
        months = []
        counts = []
        
        for row in monthly_users:
            months.append(row.month.strftime('%Y-%m'))
            counts.append(row.count)
        
        fig = go.Figure(data=[
            go.Bar(x=months, y=counts, name='Nouveaux utilisateurs')
        ])
        
        fig.update_layout(
            title='Nouveaux utilisateurs par mois',
            xaxis_title='Mois',
            yaxis_title='Nombre d\'utilisateurs'
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    @staticmethod
    @cache.memoize(timeout=600)
    def get_top_users_by_usage(limit=10):
        """Top utilisateurs par utilisation d'API"""
        top_users = db.session.query(
            User.id, User.name, User.email,
            func.sum(ApiUsageStats.requests_count).label('total_requests')
        ).join(
            ApiKey, User.id == ApiKey.user_id
        ).join(
            ApiUsageStats, ApiKey.id == ApiUsageStats.api_key_id
        ).group_by(
            User.id, User.name, User.email
        ).order_by(
            desc('total_requests')
        ).limit(limit).all()
        
        return [{
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'total_requests': user.total_requests
        } for user in top_users]
    
    @staticmethod
    @cache.memoize(timeout=300)
    def get_error_analysis():
        """Analyse des erreurs"""
        # Erreurs par jour (7 derniers jours)
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=7)
        
        error_stats = db.session.query(
            ApiUsageStats.date,
            func.sum(ApiUsageStats.errors_count).label('errors'),
            func.sum(ApiUsageStats.requests_count).label('requests')
        ).filter(
            ApiUsageStats.date.between(start_date, end_date)
        ).group_by(ApiUsageStats.date).order_by(ApiUsageStats.date).all()
        
        error_rate_data = []
        for stat in error_stats:
            rate = (stat.errors / stat.requests * 100) if stat.requests > 0 else 0
            error_rate_data.append({
                'date': stat.date.strftime('%Y-%m-%d'),
                'error_rate': round(rate, 2),
                'errors': stat.errors,
                'requests': stat.requests
            })
        
        return error_rate_data
    
    @staticmethod
    def record_system_metric(name, value, unit=None, category=None):
        """Enregistre une métrique système"""
        return SystemMetrics.record_metric(name, value, unit, category)
    
    @staticmethod
    @cache.memoize(timeout=120)
    def get_real_time_metrics():
        """Métriques en temps réel"""
        # Requêtes de la dernière heure
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        recent_logs = AuditLog.query.filter(
            AuditLog.timestamp >= one_hour_ago
        ).count()
        
        # Utilisateurs actifs (connectés dans les 24h)
        yesterday = datetime.utcnow() - timedelta(days=1)
        active_users = User.query.filter(
            User.last_login_at >= yesterday
        ).count()
        
        return {
            'recent_activity': recent_logs,
            'active_users_24h': active_users,
            'timestamp': datetime.utcnow().isoformat()
        } 