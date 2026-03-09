from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import User, ApiKey
from app.utils.email import send_approval_email, send_rejection_email
from functools import wraps
from datetime import datetime

def admin_required(f):
    """Décorateur pour vérifier les droits admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    # Statistiques
    total_users = User.query.count()
    pending_users = User.query.filter_by(status='pending_admin_approval').count()
    approved_users = User.query.filter_by(status='approved').count()
    active_api_keys = ApiKey.query.filter_by(is_active=True).count()
    
    stats = {
        'total_users': total_users,
        'pending_users': pending_users,
        'approved_users': approved_users,
        'active_api_keys': active_api_keys
    }
    
    return render_template('admin/index.html', title='Administration', stats=stats)

@bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    query = User.query
    
    # Filtrage par statut
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # Recherche
    if search:
        query = query.filter(
            (User.name.contains(search)) | 
            (User.email.contains(search))
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', title='Gestion des utilisateurs', 
                         users=users, status_filter=status_filter, search=search)

@bp.route('/user/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('admin/user_detail.html', title=f'Utilisateur - {user.name}', user=user)

@bp.route('/approve-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        # Vérifier si l'utilisateur peut être approuvé
        if user.status == 'approved':
            return jsonify({'success': False, 'error': 'Cet utilisateur est déjà approuvé'})
        
        # Approuver l'utilisateur
        user.status = 'approved'
        user.approved_at = datetime.utcnow()
        user.approved_by = current_user.id
        
        # Si l'email n'est pas vérifié, le vérifier automatiquement
        if not user.email_verified_at:
            user.email_verified_at = datetime.utcnow()
        
        db.session.commit()
        
        # Envoyer l'email d'approbation
        try:
            send_approval_email(user)
        except Exception as e:
            print(f"Erreur envoi email: {e}")
        
        return jsonify({
            'success': True, 
            'message': f'Utilisateur {user.name} approuvé avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/reject-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        if user.status == 'approved':
            return jsonify({'success': False, 'error': 'Impossible de rejeter un utilisateur déjà approuvé'})
        
        user.status = 'rejected'
        
        db.session.commit()
        
        # Envoyer l'email de rejet
        try:
            send_rejection_email(user)
        except Exception as e:
            print(f"Erreur envoi email: {e}")
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/suspend-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def suspend_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        if user.status == 'suspended':
            return jsonify({'success': False, 'error': 'Cet utilisateur est déjà suspendu'})
        
        if user.role == 'admin':
            return jsonify({'success': False, 'error': 'Impossible de suspendre un administrateur'})
        
        user.status = 'suspended'
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Utilisateur {user.name} suspendu avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/unsuspend-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def unsuspend_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        if user.status != 'suspended':
            return jsonify({'success': False, 'error': 'Cet utilisateur n\'est pas suspendu'})
        
        user.status = 'approved'
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Utilisateur {user.name} réactivé avec succès'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        # Empêcher la suppression de son propre compte
        if user.id == current_user.id:
            return jsonify({'success': False, 'error': 'Vous ne pouvez pas supprimer votre propre compte'})
        
        # Empêcher la suppression d'autres admins
        if user.role == 'admin':
            return jsonify({'success': False, 'error': 'Impossible de supprimer un autre administrateur'})
        
        # Supprimer d'abord les clés API associées
        ApiKey.query.filter_by(user_id=user.id).delete()
        
        # Supprimer l'utilisateur
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Utilisateur {user.name} supprimé avec succès'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api-keys')
@login_required
@admin_required
def api_keys():
    page = request.args.get('page', 1, type=int)
    api_keys = ApiKey.query.join(User).order_by(ApiKey.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistiques pour les clés API
    stats = {
        'total_keys': ApiKey.query.count(),
        'active_keys': ApiKey.query.filter_by(is_active=True).count(),
        'revoked_keys': ApiKey.query.filter_by(is_active=False).count(),
        'requests_today': 0  # À implémenter avec un système de logs
    }
    
    return render_template('admin/api_keys.html', title='Clés API', api_keys=api_keys, stats=stats)

@bp.route('/revoke-api-key/<int:key_id>', methods=['POST'])
@login_required
@admin_required
def revoke_api_key(key_id):
    try:
        api_key = ApiKey.query.get_or_404(key_id)
        
        if not api_key.is_active:
            return jsonify({'success': False, 'error': 'Cette clé est déjà révoquée'})
        
        api_key.is_active = False
        api_key.revoked_at = db.func.now()
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}) 