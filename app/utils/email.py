from flask import current_app, url_for, render_template
from flask_mail import Message
from app import mail, db
from app.models import EmailToken
import threading

def send_async_email(app, msg):
    """Envoie un email de manière asynchrone"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    """Fonction générique d'envoi d'email"""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    # Envoie asynchrone en développement, synchrone en production pour la simplicité
    if current_app.config.get('TESTING'):
        mail.send(msg)
    else:
        thread = threading.Thread(
            target=send_async_email,
            args=(current_app._get_current_object(), msg)
        )
        thread.start()

def send_verification_email(user):
    """Envoie l'email de vérification d'inscription"""
    # Crée le token de vérification
    token = EmailToken(user.id, 'email_verification', expires_in_hours=24)
    db.session.add(token)
    db.session.commit()
    
    # Génère l'URL de vérification
    verify_url = url_for('auth.verify_email', token=token.token, _external=True)
    
    subject = 'Vérifiez votre adresse email'
    
    text_body = f"""
Bonjour {user.name},

Merci de vous être inscrit sur notre plateforme !

Pour activer votre compte, cliquez sur le lien suivant :
{verify_url}

Ce lien expire dans 24 heures.

Si vous n'avez pas créé de compte, ignorez cet email.

Cordialement,
L'équipe de la plateforme
"""
    
    html_body = f"""
<h2>Vérification de votre adresse email</h2>
<p>Bonjour <strong>{user.name}</strong>,</p>
<p>Merci de vous être inscrit sur notre plateforme !</p>
<p>Pour activer votre compte, cliquez sur le bouton ci-dessous :</p>
<p><a href="{verify_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Vérifier mon email</a></p>
<p>Ou copiez ce lien dans votre navigateur : <br>{verify_url}</p>
<p><small>Ce lien expire dans 24 heures.</small></p>
<p>Si vous n'avez pas créé de compte, ignorez cet email.</p>
<p>Cordialement,<br>L'équipe de la plateforme</p>
"""
    
    send_email(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )

def send_approval_email(user):
    """Envoie l'email d'approbation du compte"""
    subject = 'Votre compte a été approuvé !'
    
    login_url = url_for('auth.login', _external=True)
    dashboard_url = url_for('dashboard.index', _external=True)
    
    text_body = f"""
Bonjour {user.name},

Excellente nouvelle ! Votre demande d'accès à notre plateforme de démonstration a été approuvée.

Vous pouvez maintenant vous connecter et commencer à utiliser votre clé API :
{login_url}

Une clé API a été automatiquement générée pour votre compte. Vous pourrez la consulter dans votre tableau de bord.

Bienvenue sur notre plateforme !

Cordialement,
L'équipe de la plateforme
"""
    
    html_body = f"""
<h2>Votre compte a été approuvé !</h2>
<p>Bonjour <strong>{user.name}</strong>,</p>
<p>Excellente nouvelle ! Votre demande d'accès à notre plateforme de démonstration a été approuvée.</p>
<p>Vous pouvez maintenant vous connecter et commencer à utiliser votre clé API :</p>
<p><a href="{login_url}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Se connecter</a></p>
<p>Une clé API a été automatiquement générée pour votre compte. Vous pourrez la consulter dans votre tableau de bord.</p>
<p>Bienvenue sur notre plateforme !</p>
<p>Cordialement,<br>L'équipe de la plateforme</p>
"""
    
    send_email(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )

def send_rejection_email(user):
    """Envoie l'email de rejet de la demande"""
    subject = 'Mise à jour de votre demande d\'accès'
    
    text_body = f"""
Bonjour {user.name},

Nous vous remercions pour votre intérêt pour notre plateforme de démonstration.

Après examen de votre demande, nous ne pouvons malheureusement pas vous donner accès à la version de démonstration pour le moment.

Si vous pensez qu'il s'agit d'une erreur ou si vous souhaitez plus d'informations, n'hésitez pas à nous contacter.

Cordialement,
L'équipe de la plateforme
"""
    
    html_body = f"""
<h2>Mise à jour de votre demande d'accès</h2>
<p>Bonjour <strong>{user.name}</strong>,</p>
<p>Nous vous remercions pour votre intérêt pour notre plateforme de démonstration.</p>
<p>Après examen de votre demande, nous ne pouvons malheureusement pas vous donner accès à la version de démonstration pour le moment.</p>
<p>Si vous pensez qu'il s'agit d'une erreur ou si vous souhaitez plus d'informations, n'hésitez pas à nous contacter.</p>
<p>Cordialement,<br>L'équipe de la plateforme</p>
"""
    
    send_email(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )

def send_password_reset_email(user):
    """Envoie l'email de réinitialisation de mot de passe"""
    # Crée le token de réinitialisation
    token = EmailToken(user.id, 'password_reset', expires_in_hours=2)
    db.session.add(token)
    db.session.commit()
    
    # Génère l'URL de réinitialisation
    reset_url = url_for('auth.reset_password', token=token.token, _external=True)
    
    subject = 'Réinitialisation de votre mot de passe'
    
    text_body = f"""
Bonjour {user.name},

Vous avez demandé la réinitialisation de votre mot de passe.

Pour créer un nouveau mot de passe, cliquez sur le lien suivant :
{reset_url}

Ce lien expire dans 2 heures.

Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

Cordialement,
L'équipe de la plateforme
"""
    
    html_body = f"""
<h2>Réinitialisation de votre mot de passe</h2>
<p>Bonjour <strong>{user.name}</strong>,</p>
<p>Vous avez demandé la réinitialisation de votre mot de passe.</p>
<p>Pour créer un nouveau mot de passe, cliquez sur le bouton ci-dessous :</p>
<p><a href="{reset_url}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Réinitialiser mon mot de passe</a></p>
<p>Ou copiez ce lien dans votre navigateur : <br>{reset_url}</p>
<p><small>Ce lien expire dans 2 heures.</small></p>
<p>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.</p>
<p>Cordialement,<br>L'équipe de la plateforme</p>
"""
    
    send_email(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    ) 