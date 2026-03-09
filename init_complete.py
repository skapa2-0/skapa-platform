from app import create_app, db
from app.models import User

def rebuild_db():
    """
    Supprime complètement la base de données, la recrée
    et ajoute un utilisateur admin par défaut.
    """
    app = create_app()
    with app.app_context():
        print("--- Début de la reconstruction de la base de données ---")
        
        print("1. Suppression de toutes les tables existantes...")
        db.drop_all()
        print("   => Tables supprimées avec succès.")
        
        print("2. Création des nouvelles tables à partir des modèles...")
        db.create_all()
        print("   => Tables créées avec succès.")

        # Création de l'utilisateur admin par défaut
        print("3. Ajout de l'utilisateur administrateur...")
        if not User.query.filter_by(email='admin@skapa.design').first():
            admin_user = User(
                email='admin@skapa.design',
                name='Kevin Hamon',
                justification='Compte administrateur initial',
                role='admin',
                status='approved'
            )
            admin_user.set_password('gc73vau5oeqTbtGn')
            db.session.add(admin_user)
            db.session.commit()
            print("   => Utilisateur 'admin@skapa.design' (mdp: 'gc73vau5oeqTbtGn') créé.")
        else:
            print("   => L'utilisateur admin existe déjà, aucune action requise.")

        print("--- Base de données reconstruite et initialisée avec succès ! ---")

if __name__ == '__main__':
    rebuild_db()
