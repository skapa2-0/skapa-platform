from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.dashboard import bp
from app.models import ApiKey, Notification, UserPreferences
from app.utils.helpers import get_dashboard_stats, get_user_preferences, log_user_activity, create_notification
from datetime import datetime

@bp.route('/')
@login_required
def index():
    """Page principale du dashboard"""
    if not current_user.can_login():
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('auth.logout'))
    
    api_key = current_user.get_active_api_key()
    
    # Statistiques du dashboard
    stats = get_dashboard_stats(current_user.id, days=30)
    
    # Notifications récentes non lues
    recent_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Préférences utilisateur
    preferences = get_user_preferences(current_user.id)
    
    return render_template(
        'dashboard/index.html', 
        title='Tableau de bord', 
        api_key=api_key,
        stats=stats,
        recent_notifications=recent_notifications,
        preferences=preferences
    )

@bp.route('/generate-api-key', methods=['POST'])
@login_required
def generate_api_key():
    """Génère une nouvelle clé API"""
    if not current_user.can_login():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        api_key, full_key = current_user.generate_api_key()
        
        # Log de l'activité
        log_user_activity(
            user_id=current_user.id,
            action='api_key_generated',
            description='Nouvelle clé API générée'
        )
        
        # Notification
        create_notification(
            user_id=current_user.id,
            title='Nouvelle clé API',
            message='Votre nouvelle clé API a été générée avec succès.',
            type='success'
        )
        
        flash('Nouvelle clé API générée avec succès !', 'success')
        return jsonify({
            'success': True,
            'key': full_key
        })
    except Exception as e:
        # Log de l'erreur
        log_user_activity(
            user_id=current_user.id,
            action='api_key_generation_failed',
            description=f'Échec de génération de clé API: {str(e)}'
        )
        return jsonify({'error': 'Erreur lors de la génération de la clé'}), 500

@bp.route('/revoke-api-key', methods=['POST'])
@login_required
def revoke_api_key():
    """Révoque la clé API active"""
    if not current_user.can_login():
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    api_key = current_user.get_active_api_key()
    if not api_key:
        return jsonify({'error': 'Aucune clé API active trouvée'}), 404
    
    try:
        api_key.revoke()
        db.session.commit()
        
        # Log de l'activité
        log_user_activity(
            user_id=current_user.id,
            action='api_key_revoked',
            description='Clé API révoquée'
        )
        
        # Notification
        create_notification(
            user_id=current_user.id,
            title='Clé API révoquée',
            message='Votre clé API a été révoquée avec succès.',
            type='warning'
        )
        
        flash('Clé API révoquée avec succès.', 'info')
        return jsonify({'success': True})
    except Exception as e:
        # Log de l'erreur
        log_user_activity(
            user_id=current_user.id,
            action='api_key_revocation_failed',
            description=f'Échec de révocation de clé API: {str(e)}'
        )
        return jsonify({'error': 'Erreur lors de la révocation de la clé'}), 500

@bp.route('/profile')
@login_required
def profile():
    return render_template('dashboard/profile.html', title='Mon profil')

@bp.route('/settings')
@login_required
def settings():
    """Page des paramètres utilisateur"""
    preferences = get_user_preferences(current_user.id)
    return render_template('dashboard/settings.html', 
                         title='Paramètres', 
                         preferences=preferences)

@bp.route('/update-preferences', methods=['POST'])
@login_required
def update_preferences():
    """Mise à jour des préférences utilisateur"""
    try:
        preferences = get_user_preferences(current_user.id)
        
        # Mise à jour des préférences
        preferences.theme = request.form.get('theme', preferences.theme)
        preferences.language = request.form.get('language', preferences.language)
        preferences.notifications_email = 'notifications_email' in request.form
        preferences.notifications_browser = 'notifications_browser' in request.form
        
        dashboard_refresh = request.form.get('dashboard_refresh_rate', type=int)
        if dashboard_refresh and dashboard_refresh in [10, 30, 60, 120]:
            preferences.dashboard_refresh_rate = dashboard_refresh
        
        preferences.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log de l'activité
        log_user_activity(
            user_id=current_user.id,
            action='preferences_updated',
            description='Préférences mises à jour'
        )
        
        flash('Préférences mises à jour avec succès !', 'success')
        return redirect(url_for('dashboard.settings'))
        
    except Exception as e:
        db.session.rollback()
        flash('Erreur lors de la mise à jour des préférences.', 'danger')
        return redirect(url_for('dashboard.settings'))

@bp.route('/quick-stats')
@login_required
def quick_stats():
    """API pour les statistiques rapides du dashboard"""
    stats = get_dashboard_stats(current_user.id, days=7)
    
    # Notifications non lues
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({
        'success': True,
        'requests_today': stats['last_24h_requests'],
        'total_requests': stats['total_requests'],
        'avg_response_time': stats['avg_response_time'],
        'unread_notifications': unread_notifications
    })

@bp.route('/api-usage-chart')
@login_required
def api_usage_chart():
    """Données pour le graphique d'utilisation API"""
    days = request.args.get('days', 7, type=int)
    stats = get_dashboard_stats(current_user.id, days)
    
    return jsonify({
        'success': True,
        'chart_data': stats['chart_data']
    }) 
