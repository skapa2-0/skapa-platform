from flask import render_template
from app.main import bp

@bp.route('/')
def index():
    return render_template('main/index.html', title='Accueil')

@bp.route('/about')
def about():
    return render_template('main/about.html', title='À propos')

@bp.route('/pricing')
def pricing():
    return render_template('main/pricing.html', title='Pricing')

@bp.route('/terms')
def terms():
    return render_template('main/terms.html', title='Conditions d\'utilisation')

@bp.route('/tutorials')
def tutorials():
    return render_template('main/tutorials.html', title='Tutoriels & Documentation') 