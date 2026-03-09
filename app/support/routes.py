from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.support import bp
from app.models import SupportTicket, SupportMessage, User
from app.utils.helpers import create_notification, log_user_activity
from sqlalchemy import desc, or_


@bp.route('/')
@login_required
def index():
    """Page principale du support - liste des tickets de l'utilisateur"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = SupportTicket.query.filter_by(user_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    tickets = query.order_by(desc(SupportTicket.created_at)).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Statistiques pour l'utilisateur
    stats = {
        'total': SupportTicket.query.filter_by(user_id=current_user.id).count(),
        'open': SupportTicket.query.filter_by(user_id=current_user.id, status='open').count(),
        'in_progress': SupportTicket.query.filter_by(user_id=current_user.id, status='in_progress').count(),
        'resolved': SupportTicket.query.filter_by(user_id=current_user.id, status='resolved').count(),
        'closed': SupportTicket.query.filter_by(user_id=current_user.id, status='closed').count(),
    }
    
    return render_template('support/index.html', 
                         title='Support',
                         tickets=tickets,
                         stats=stats,
                         status_filter=status_filter)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    """Créer un nouveau ticket de support"""
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'medium')
        category = request.form.get('category', 'general')
        
        # Validation
        if not subject:
            flash('Le sujet ne peut pas être vide.', 'danger')
            return redirect(url_for('support.new_ticket'))
        
        if not message:
            flash('Le message ne peut pas être vide.', 'danger')
            return redirect(url_for('support.new_ticket'))
        
        # Création du ticket
        ticket = SupportTicket(
            user_id=current_user.id,
            subject=subject,
            message=message,
            priority=priority,
            category=category
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        # Log de l'activité
        log_user_activity(
            user_id=current_user.id,
            action='support_ticket_created',
            description=f'Ticket créé: {subject}',
            extra_data={'ticket_id': ticket.id, 'category': category, 'priority': priority}
        )
        
        # Notification pour l'utilisateur
        create_notification(
            user_id=current_user.id,
            title='Ticket créé',
            message=f'Votre ticket "{subject}" a été créé avec succès. Nous vous répondrons dans les plus brefs délais.',
            type='success',
            action_url=url_for('support.ticket_detail', ticket_id=ticket.id),
            action_text='Voir le ticket'
        )
        
        # Notification pour les admins
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            create_notification(
                user_id=admin.id,
                title='Nouveau ticket de support',
                message=f'{current_user.name} a créé un nouveau ticket: "{subject}"',
                type='info',
                action_url=url_for('support.admin_ticket_detail', ticket_id=ticket.id),
                action_text='Voir le ticket'
            )
        
        flash('Votre ticket a été créé avec succès. Nous vous répondrons rapidement !', 'success')
        return redirect(url_for('support.ticket_detail', ticket_id=ticket.id))
    
    return render_template('support/new_ticket.html', title='Nouveau ticket')


@bp.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def ticket_detail(ticket_id):
    """Détail d'un ticket de support"""
    ticket = SupportTicket.query.filter_by(
        id=ticket_id,
        user_id=current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'reply':
            # Ajouter une réponse au ticket
            content = request.form.get('message', '').strip()
            if content:
                try:
                    message = SupportMessage(
                        ticket_id=ticket.id,
                        user_id=current_user.id,
                        content=content,
                        is_staff=False
                    )
                    db.session.add(message)
                    
                    # Mettre à jour le statut du ticket si nécessaire
                    if ticket.status == 'closed':
                        ticket.status = 'open'
                        flash('Ticket rouvert avec votre réponse.', 'info')
                    
                    ticket.updated_at = datetime.utcnow()
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"Warning: Could not save message: {e}")
                    flash('Impossible d\'enregistrer votre message pour le moment. La fonctionnalité sera disponible prochainement.', 'warning')
                    return redirect(url_for('support.ticket_detail', ticket_id=ticket.id))
                
                # Notifier les admins
                from app.utils.helpers import create_notification
                admins = User.query.filter_by(role='admin').all()
                for admin in admins:
                    create_notification(
                        user_id=admin.id,
                        title='Nouvelle réponse ticket',
                        message=f'{current_user.name} a répondu au ticket #{ticket.id}: "{ticket.subject}"',
                        type='info',
                        action_url=url_for('support.admin_ticket_detail', ticket_id=ticket.id),
                        action_text='Voir le ticket'
                    )
                
                # Logger l'activité
                log_user_activity(
                    user_id=current_user.id,
                    action='ticket_reply',
                    description=f'Réponse au ticket #{ticket.id}: {ticket.subject}'
                )
                
                flash('Votre réponse a été ajoutée avec succès.', 'success')
            else:
                flash('Le message ne peut pas être vide.', 'danger')
        
        elif action == 'close':
            # Fermer le ticket (utilisateur)
            ticket.status = 'closed'
            ticket.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Logger l'activité
            log_user_activity(
                user_id=current_user.id,
                action='ticket_closed',
                description=f'Ticket fermé #{ticket.id}: {ticket.subject}'
            )
            
            flash('Ticket fermé avec succès.', 'success')
        
        elif action == 'reopen':
            # Rouvrir le ticket
            ticket.status = 'open'
            ticket.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Logger l'activité
            log_user_activity(
                user_id=current_user.id,
                action='ticket_reopened',
                description=f'Ticket rouvert #{ticket.id}: {ticket.subject}'
            )
            
            flash('Ticket rouvert avec succès.', 'success')
        
        return redirect(url_for('support.ticket_detail', ticket_id=ticket.id))
    
    # Récupérer les messages du ticket (avec gestion d'erreur)
    try:
        messages = ticket.messages.order_by(SupportMessage.created_at.asc()).all()
    except Exception as e:
        # Si la table support_messages n'existe pas encore, on continue sans messages
        print(f"Warning: Could not load messages: {e}")
        messages = []
    
    return render_template('support/ticket_detail.html', 
                         title=f'Ticket - {ticket.subject}',
                         ticket=ticket,
                         messages=messages)


@bp.route('/admin')
@login_required
def admin_index():
    """Interface admin pour la gestion des tickets"""
    if not current_user.is_admin():
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('support.index'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    category_filter = request.args.get('category', 'all')
    assigned_filter = request.args.get('assigned', 'all')
    search = request.args.get('search', '')
    
    query = SupportTicket.query
    
    # Filtres
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if priority_filter != 'all':
        query = query.filter_by(priority=priority_filter)
    
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)
    
    if assigned_filter == 'assigned':
        query = query.filter(SupportTicket.assigned_to.isnot(None))
    elif assigned_filter == 'unassigned':
        query = query.filter(SupportTicket.assigned_to.is_(None))
    elif assigned_filter != 'all':
        query = query.filter_by(assigned_to=int(assigned_filter))
    
    # Recherche
    if search:
        query = query.join(User).filter(
            or_(
                SupportTicket.subject.contains(search),
                SupportTicket.message.contains(search),
                User.name.contains(search),
                User.email.contains(search)
            )
        )
    
    tickets = query.order_by(desc(SupportTicket.created_at)).paginate(
        page=page, per_page=15, error_out=False
    )
    
    # Statistiques admin
    stats = {
        'total': SupportTicket.query.count(),
        'open': SupportTicket.query.filter_by(status='open').count(),
        'in_progress': SupportTicket.query.filter_by(status='in_progress').count(),
        'resolved': SupportTicket.query.filter_by(status='resolved').count(),
        'unassigned': SupportTicket.query.filter(SupportTicket.assigned_to.is_(None)).count(),
        'high_priority': SupportTicket.query.filter_by(priority='high').count(),
        'urgent': SupportTicket.query.filter_by(priority='urgent').count(),
    }
    
    # Liste des admins pour l'assignation
    admins = User.query.filter_by(role='admin').all()
    
    return render_template('support/admin_index.html',
                         title='Gestion des tickets',
                         tickets=tickets,
                         stats=stats,
                         admins=admins,
                         status_filter=status_filter,
                         priority_filter=priority_filter,
                         category_filter=category_filter,
                         assigned_filter=assigned_filter,
                         search=search)


@bp.route('/admin/ticket/<int:ticket_id>')
@login_required
def admin_ticket_detail(ticket_id):
    """Détail admin d'un ticket"""
    if not current_user.is_admin():
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('support.index'))
    
    ticket = SupportTicket.query.get_or_404(ticket_id)
    admins = User.query.filter_by(role='admin').all()
    
    return render_template('support/admin_ticket_detail.html',
                         title=f'Ticket - {ticket.subject}',
                         ticket=ticket,
                         admins=admins)


@bp.route('/admin/update-ticket/<int:ticket_id>', methods=['POST'])
@login_required
def update_ticket(ticket_id):
    """Mise à jour d'un ticket par un admin"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
    
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    try:
        status = request.form.get('status')
        priority = request.form.get('priority')
        assigned_to = request.form.get('assigned_to')
        resolution = request.form.get('resolution', '').strip()
        
        # Mise à jour des champs
        if status:
            old_status = ticket.status
            ticket.status = status
            if status == 'resolved' and old_status != 'resolved':
                ticket.resolved_at = db.func.now()
        
        if priority:
            ticket.priority = priority
        
        if assigned_to:
            ticket.assigned_to = int(assigned_to) if assigned_to != 'none' else None
        
        if resolution:
            ticket.resolution = resolution
        
        ticket.updated_at = db.func.now()
        db.session.commit()
        
        # Log de l'activité
        log_user_activity(
            user_id=current_user.id,
            action='support_ticket_updated',
            description=f'Ticket mis à jour: {ticket.subject}',
            extra_data={'ticket_id': ticket.id, 'status': ticket.status}
        )
        
        # Notification pour l'utilisateur
        status_messages = {
            'in_progress': 'Votre ticket est maintenant en cours de traitement.',
            'resolved': 'Votre ticket a été résolu.',
            'closed': 'Votre ticket a été fermé.'
        }
        
        if status in status_messages:
            create_notification(
                user_id=ticket.user_id,
                title='Mise à jour de votre ticket',
                message=f'{status_messages[status]} Ticket: "{ticket.subject}"',
                type='info',
                action_url=url_for('support.ticket_detail', ticket_id=ticket.id),
                action_text='Voir le ticket'
            )
        
        return jsonify({'success': True, 'message': 'Ticket mis à jour avec succès'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/knowledge-base')
def knowledge_base():
    """Base de connaissances publique"""
    return render_template('support/knowledge_base.html', 
                         title='Base de connaissances')


@bp.route('/faq')
def faq():
    """Page FAQ"""
    return render_template('support/faq.html', title='Questions fréquentes') 