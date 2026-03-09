from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.notifications import bp
from app.models import Notification
from app.utils.helpers import create_notification
from sqlalchemy import desc


@bp.route('/')
@login_required
def index():
    """Page principale des notifications"""
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('type', 'all')
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if filter_type != 'all':
        if filter_type == 'unread':
            query = query.filter_by(is_read=False)
        else:
            query = query.filter_by(type=filter_type)
    
    notifications = query.order_by(desc(Notification.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistiques
    stats = {
        'total': Notification.query.filter_by(user_id=current_user.id).count(),
        'unread': Notification.query.filter_by(user_id=current_user.id, is_read=False).count(),
        'info': Notification.query.filter_by(user_id=current_user.id, type='info').count(),
        'success': Notification.query.filter_by(user_id=current_user.id, type='success').count(),
        'warning': Notification.query.filter_by(user_id=current_user.id, type='warning').count(),
        'error': Notification.query.filter_by(user_id=current_user.id, type='error').count(),
    }
    
    return render_template('notifications/index.html', 
                         title='Notifications', 
                         notifications=notifications,
                         stats=stats,
                         filter_type=filter_type)


@bp.route('/api/notifications')
@login_required
def api_notifications():
    """API pour récupérer les notifications (pour les requêtes AJAX)"""
    limit = request.args.get('limit', 10, type=int)
    unread_only = request.args.get('unread_only', False, type=bool)
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    notifications = query.order_by(desc(Notification.created_at)).limit(limit).all()
    
    return jsonify({
        'notifications': [notif.to_dict() for notif in notifications],
        'unread_count': Notification.query.filter_by(
            user_id=current_user.id, 
            is_read=False
        ).count()
    })


@bp.route('/mark-as-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Marque une notification comme lue"""
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=current_user.id
    ).first_or_404()
    
    if not notification.is_read:
        notification.mark_as_read()
        db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/mark-all-as-read', methods=['POST'])
@login_required
def mark_all_as_read():
    """Marque toutes les notifications comme lues"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()
    
    for notification in notifications:
        notification.mark_as_read()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{len(notifications)} notifications marquées comme lues'
    })


@bp.route('/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Supprime une notification"""
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/clear-all', methods=['POST'])
@login_required
def clear_all():
    """Supprime toutes les notifications de l'utilisateur"""
    count = Notification.query.filter_by(user_id=current_user.id).count()
    
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{count} notifications supprimées'
    }) 
