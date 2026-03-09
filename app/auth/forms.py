from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

class RegistrationForm(FlaskForm):
    name = StringField('Nom complet', validators=[
        DataRequired(message='Le nom est requis'),
        Length(min=2, max=100, message='Le nom doit contenir entre 2 et 100 caractères')
    ])
    
    email = StringField('Adresse email', validators=[
        DataRequired(message='L\'email est requis'),
        Email(message='Adresse email invalide')
    ])
    
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message='Le mot de passe est requis'),
        Length(min=8, message='Le mot de passe doit contenir au moins 8 caractères')
    ])
    
    password2 = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(message='La confirmation est requise'),
        EqualTo('password', message='Les mots de passe ne correspondent pas')
    ])
    
    justification = TextAreaField('Justification d\'accès à la démo', validators=[
        DataRequired(message='La justification est requise'),
        Length(min=50, max=500, message='La justification doit contenir entre 50 et 500 caractères')
    ], render_kw={"placeholder": "Expliquez pourquoi vous souhaitez accéder à notre plateforme de démonstration..."})
    
    terms = BooleanField('J\'accepte les conditions d\'utilisation', validators=[
        DataRequired(message='Vous devez accepter les conditions d\'utilisation')
    ])
    
    submit = SubmitField('S\'inscrire')
    
    def validate_email(self, email):
        # Import ici pour éviter les problèmes d'importation circulaire
        from app.models import User
        try:
            user = User.query.filter_by(email=email.data.lower()).first()
            if user:
                raise ValidationError('Cette adresse email est déjà utilisée.')
        except Exception:
            # Si la table n'existe pas encore, on ignore la validation
            pass

class LoginForm(FlaskForm):
    email = StringField('Adresse email', validators=[
        DataRequired(message='L\'email est requis'),
        Email(message='Adresse email invalide')
    ])
    
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message='Le mot de passe est requis')
    ])
    
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Adresse email', validators=[
        DataRequired(message='L\'email est requis'),
        Email(message='Adresse email invalide')
    ])
    submit = SubmitField('Réinitialiser le mot de passe')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(message='Le mot de passe est requis'),
        Length(min=8, message='Le mot de passe doit contenir au moins 8 caractères')
    ])
    
    password2 = PasswordField('Confirmer le nouveau mot de passe', validators=[
        DataRequired(message='La confirmation est requise'),
        EqualTo('password', message='Les mots de passe ne correspondent pas')
    ])
    
    submit = SubmitField('Changer le mot de passe') 