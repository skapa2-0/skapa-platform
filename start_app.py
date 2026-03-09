#!/usr/bin/env python3
"""
Script de démarrage pour l'application API IA Locale avec toutes les nouvelles fonctionnalités
"""

import os
import sys
import subprocess
from datetime import datetime

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    print("🔍 Vérification des dépendances...")
    
    required_packages = [
        'flask', 'sqlalchemy', 'redis', 'plotly', 'pandas', 
        'cryptography', 'flask-socketio', 'flasgger'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Dépendances manquantes: {', '.join(missing)}")
        print("💡 Installez-les avec: pip install -r requirements.txt")
        return False
    
    print("✅ Toutes les dépendances sont présentes")
    return True

def check_database():
    """Vérifie si la base de données est initialisée"""
    print("🔍 Vérification de la base de données...")
    
    if not os.path.exists('app.db'):
        print("❌ Base de données non trouvée")
        print("💡 Initialisez-la avec: python scripts/init_db_with_features.py")
        return False
    
    print("✅ Base de données trouvée")
    return True

def check_redis():
    """Vérifie si Redis est accessible (optionnel)"""
    print("🔍 Vérification de Redis...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis est accessible")
        return True
    except Exception:
        print("⚠️  Redis non accessible - Les fonctionnalités temps réel seront limitées")
        print("💡 Installez et démarrez Redis pour les notifications en temps réel")
        return False

def show_welcome():
    """Affiche le message de bienvenue"""
    print("🎉" + "="*60 + "🎉")
    print("🚀 API IA LOCALE - NOUVELLE VERSION AMÉLIORÉE 🚀")
    print("="*64)
    print()
    print("✨ NOUVELLES FONCTIONNALITÉS INCLUSES :")
    print("   🌙 Dark Mode intelligent")
    print("   🔔 Notifications en temps réel") 
    print("   📊 Analytics avancées avec graphiques")
    print("   🔍 Audit complet et traçabilité")
    print("   📈 Statistiques d'utilisation détaillées")
    print("   🔒 Sécurité renforcée")
    print("   🎨 Interface moderne et responsive")
    print("   📦 Export de données CSV/JSON")
    print("   🔍 Recherche globale intelligente")
    print("   ⚙️  Préférences utilisateur personnalisables")
    print()
    print("📚 DOCUMENTATION API : http://localhost:5000/api-docs/")
    print()

def show_accounts():
    """Affiche les comptes disponibles"""
    print("👥 COMPTES DE TEST DISPONIBLES :")
    print("=" * 40)
    print("🔐 Administrateur :")
    print("   Email    : admin@votreplateforme.com")
    print("   Password : admin123")
    print("   Accès    : Toutes fonctionnalités + Analytics")
    print()
    print("👤 Utilisateurs de test :")
    print("   Email    : user1@example.com")
    print("   Password : password123")
    print("   Accès    : Dashboard utilisateur")
    print()
    print("   Email    : user2@example.com")
    print("   Password : password123")
    print("   Accès    : Dashboard utilisateur")
    print()

def start_application():
    """Démarre l'application Flask"""
    print("🚀 Démarrage de l'application...")
    print("📍 L'application sera accessible sur : http://localhost:5000")
    print()
    print("💡 CONSEILS D'UTILISATION :")
    print("   • Cliquez sur l'icône 🌙/☀️ pour changer le thème")
    print("   • Cliquez sur 🔔 pour voir les notifications")
    print("   • Utilisez la barre de recherche pour trouver rapidement")
    print("   • Explorez les analytics si vous êtes admin")
    print("   • Consultez la documentation API intégrée")
    print()
    print("🔄 Pour arrêter : Ctrl+C")
    print("="*60)
    
    try:
        from app import create_app, socketio
        app = create_app()
        
        # Démarrer avec SocketIO pour les notifications temps réel
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n👋 Application arrêtée proprement")
    except Exception as e:
        print(f"\n❌ Erreur lors du démarrage: {e}")
        print("💡 Vérifiez que toutes les dépendances sont installées")

def main():
    """Fonction principale"""
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    show_welcome()
    
    # Vérifications préliminaires
    if not check_dependencies():
        return 1
    
    if not check_database():
        response = input("\n❓ Voulez-vous initialiser la base de données maintenant ? (oui/non): ")
        if response.lower() in ['oui', 'o', 'yes', 'y']:
            print("🔧 Initialisation de la base de données...")
            try:
                subprocess.run([sys.executable, 'scripts/init_db_with_features.py'], 
                             input='oui\n', text=True, check=True)
                print("✅ Base de données initialisée avec succès")
            except subprocess.CalledProcessError:
                print("❌ Erreur lors de l'initialisation")
                return 1
        else:
            print("❌ Base de données requise pour démarrer")
            return 1
    
    # Vérification optionnelle de Redis
    redis_available = check_redis()
    
    print()
    show_accounts()
    
    # Demander confirmation avant démarrage
    response = input("❓ Voulez-vous démarrer l'application maintenant ? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("👋 À bientôt !")
        return 0
    
    print()
    start_application()
    return 0

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Au revoir !")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        sys.exit(1) 