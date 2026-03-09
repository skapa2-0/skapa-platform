from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp
from app.auth.forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from app.models import User, EmailToken
from app.utils.email import send_verification_email, send_password_reset_email
from datetime import datetime
from urllib.parse import urlparse

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data.lower(),
            justification=form.justification.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Envoie l'email de vérification
        send_verification_email(user)
        
        flash('Inscription réussie ! Vérifiez votre email pour activer votre compte.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Inscription', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and user.check_password(form.password.data):
            # Vérifier le statut de l'utilisateur
            if user.status == 'pending_email_verification':
                flash('Veuillez d\'abord vérifier votre adresse e-mail. Un nouveau lien vient de vous être envoyé.', 'warning')
                send_verification_email(user)
                return redirect(url_for('auth.login'))

            if user.status == 'pending_admin_approval':
                flash('Votre compte est en attente d\'approbation par un administrateur.', 'info')
                return redirect(url_for('auth.login'))
            
            if not user.can_login():
                flash('Accès non autorisé ou compte suspendu. Contactez l\'administrateur.', 'danger')
                return redirect(url_for('auth.login'))

            # Connexion réussie
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('dashboard.index')
            return redirect(next_page)
        else:
            flash('Email ou mot de passe incorrect.', 'danger')
    
    return render_template('auth/login.html', title='Connexion', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/verify-email/<token>')
def verify_email(token):
    email_token = EmailToken.find_valid_token(token, 'email_verification')
    
    if not email_token:
        flash('Token de vérification invalide ou expiré.', 'danger')
        return redirect(url_for('auth.login'))
    
    user = email_token.user
    user.email_verified_at = db.func.now()
    user.status = 'pending_admin_approval'
    email_token.use_token()
    
    db.session.commit()
    
    flash('Email vérifié avec succès ! Votre compte est maintenant en attente d\'approbation.', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            send_password_reset_email(user)
        flash('Si cette adresse email existe, vous recevrez un lien de réinitialisation.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', title='Mot de passe oublié', form=form)

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    email_token = EmailToken.find_valid_token(token, 'password_reset')
    if not email_token:
        flash('Token de réinitialisation invalide ou expiré.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = email_token.user
        user.set_password(form.password.data)
        email_token.use_token()
        db.session.commit()
        
        flash('Votre mot de passe a été réinitialisé avec succès.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Réinitialiser le mot de passe', form=form) 