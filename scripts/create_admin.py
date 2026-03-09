import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User
from config import Config

def create_admin():
    app = create_app()
    
    with app.app_context():
        # Vérifie si l'admin existe déjà
        admin = User.query.filter_by(email=Config.ADMIN_EMAIL).first()
        
        if admin:
            print(f"L'administrateur {Config.ADMIN_EMAIL} existe déjà.")
            return
        
        # Crée le compte admin
        admin = User(
            name="Administrateur",
            email=Config.ADMIN_EMAIL,
            justification="Compte administrateur système",
            status="approved",
            role="admin"
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        admin.email_verified_at = db.func.now()
        admin.approved_at = db.func.now()
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"Compte administrateur créé avec succès !")
        print(f"Email: {Config.ADMIN_EMAIL}")
        print(f"Mot de passe: {Config.ADMIN_PASSWORD}")

if __name__ == '__main__':
    create_admin() 