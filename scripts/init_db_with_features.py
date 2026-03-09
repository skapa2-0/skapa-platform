#!/usr/bin/env python3
"""
Script d'initialisation de la base de données avec toutes les nouvelles fonctionnalités
"""

import sys
import os
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    User, ApiKey, EmailToken, AuditLog, Notification, 
    UserPreferences, ApiUsageStats, SystemMetrics
)
from app.utils.notifications import NotificationService, AuditService
from config import Config

def init_database():
    """Initialise la base de données avec les nouvelles tables"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Création des tables de base de données...")
        
        # Supprimer toutes les tables existantes (attention en production !)
        db.drop_all()
        
        # Créer toutes les tables
        db.create_all()
        
        print("✅ Tables créées avec succès !")
        
        # Créer un utilisateur admin par défaut
        create_admin_user()
        
        # Créer des données de test
        create_sample_data()
        
        print("🎉 Base de données initialisée avec succès !")

def create_admin_user():
    """Crée un utilisateur administrateur par défaut"""
    print("👤 Création de l'utilisateur administrateur...")
    
    admin = User(
        email=Config.ADMIN_EMAIL,
        name="Administrateur",
        justification="Compte administrateur système",
        status="approved",
        role="admin"
    )
    admin.set_password(Config.ADMIN_PASSWORD)
    admin.email_verified_at = datetime.utcnow()
    admin.approved_at = datetime.utcnow()
    admin.login_count = 0
    
    db.session.add(admin)
    db.session.commit()
    
    # Créer les préférences par défaut pour l'admin
    preferences = UserPreferences(user_id=admin.id)
    db.session.add(preferences)
    
    # Générer une clé API pour l'admin
    api_key, full_key = admin.generate_api_key()
    
    # Log la création de l'admin
    AuditService.log_action(
        'admin_user_created',
        admin.id,
        'user',
        admin.id,
        details={'email': admin.email}
    )
    
    # Notification de bienvenue
    NotificationService.create_notification(
        user_id=admin.id,
        title="🎉 Bienvenue sur la plateforme !",
        message="Votre compte administrateur a été créé avec succès. Vous avez accès à toutes les fonctionnalités.",
        type='success',
        action_url='/dashboard',
        action_text='Accéder au dashboard'
    )
    
    print(f"✅ Administrateur créé - Email: {admin.email}")
    print(f"🔑 Clé API générée: {full_key}")

def create_sample_data():
    """Crée des données d'exemple pour tester les fonctionnalités"""
    print("📊 Création de données d'exemple...")
    
    # Utilisateurs de test avec des adresses mail crédibles de société
    users_data = [
        {
            'email': 'alice.dupont@intra-tech.fr',
            'name': 'Alice Dupont',
            'justification': 'Responsable produit chez Intra-Tech',
            'status': 'approved'
        },
        {
            'email': 'jean.martin@dataflow.io',
            'name': 'Jean Martin',
            'justification': 'Développeur backend chez DataFlow',
            'status': 'approved'
        },
        {
            'email': 'sophie.leroy@cybernetics.com',
            'name': 'Sophie Leroy',
            'justification': 'Ingénieure IA chez Cybernetics',
            'status': 'approved'
        },
        {
            'email': 'paul.moreau@cloudyapps.fr',
            'name': 'Paul Moreau',
            'justification': 'Chef de projet chez CloudyApps',
            'status': 'approved'
        },
        {
            'email': 'emma.bernard@fintechplus.eu',
            'name': 'Emma Bernard',
            'justification': 'Analyste chez FinTech Plus',
            'status': 'approved'
        },
        {
            'email': 'julien.roux@meditech.fr',
            'name': 'Julien Roux',
            'justification': 'CTO chez MediTech',
            'status': 'approved'
        },
        {
            'email': 'claire.girard@greenpulse.com',
            'name': 'Claire Girard',
            'justification': 'Data Scientist chez GreenPulse',
            'status': 'approved'
        },
        {
            'email': 'antoine.perrin@logisys.io',
            'name': 'Antoine Perrin',
            'justification': 'Architecte cloud chez LogiSys',
            'status': 'approved'
        },
        {
            'email': 'laura.marchand@edusmart.fr',
            'name': 'Laura Marchand',
            'justification': 'Product Owner chez EduSmart',
            'status': 'approved'
        },
        {
            'email': 'vincent.dupuis@agrodata.eu',
            'name': 'Vincent Dupuis',
            'justification': 'Ingénieur logiciel chez AgroData',
            'status': 'approved'
        },
        {
            'email': 'camille.fabre@urbanai.com',
            'name': 'Camille Fabre',
            'justification': 'Chef de projet IA chez UrbanAI',
            'status': 'approved'
        },
        {
            'email': 'lucas.benoit@finovate.fr',
            'name': 'Lucas Benoit',
            'justification': 'Développeur fullstack chez Finovate',
            'status': 'approved'
        },
        {
            'email': 'marie.renard@healthsync.io',
            'name': 'Marie Renard',
            'justification': 'Responsable innovation chez HealthSync',
            'status': 'approved'
        },
        {
            'email': 'nicolas.gauthier@cyberdefense.fr',
            'name': 'Nicolas Gauthier',
            'justification': 'Expert sécurité chez CyberDefense',
            'status': 'approved'
        },
        {
            'email': 'lea.petit@mobilityhub.com',
            'name': 'Léa Petit',
            'justification': 'Lead développeuse chez MobilityHub',
            'status': 'approved'
        },
        {
            'email': 'mathieu.gerard@retailtech.fr',
            'name': 'Mathieu Gérard',
            'justification': 'Analyste data chez RetailTech',
            'status': 'approved'
        },
        {
            'email': 'julie.dupuis@clevercloud.io',
            'name': 'Julie Dupuis',
            'justification': 'DevOps chez CleverCloud',
            'status': 'approved'
        },
        {
            'email': 'thomas.lefevre@insurwise.com',
            'name': 'Thomas Lefevre',
            'justification': 'Chef de produit chez InsurWise',
            'status': 'approved'
        },
        {
            'email': 'anais.morel@bioanalytics.fr',
            'name': 'Anaïs Morel',
            'justification': 'Data analyst chez BioAnalytics',
            'status': 'approved'
        },
        {
            'email': 'sebastien.lambert@smartcity.eu',
            'name': 'Sébastien Lambert',
            'justification': 'Responsable technique chez SmartCity',
            'status': 'approved'
        },
        {
            'email': 'elodie.roussel@edutech.fr',
            'name': 'Elodie Roussel',
            'justification': 'Ingénieure pédagogique chez EduTech',
            'status': 'approved'
        },
        {
            'email': 'maxime.dupuy@foodai.com',
            'name': 'Maxime Dupuy',
            'justification': 'Lead IA chez FoodAI',
            'status': 'approved'
        },
        {
            'email': 'sandra.perez@travelgenius.io',
            'name': 'Sandra Perez',
            'justification': 'Product manager chez TravelGenius',
            'status': 'approved'
        },
        {
            'email': 'adrien.marchal@legaltech.fr',
            'name': 'Adrien Marchal',
            'justification': 'Juriste innovation chez LegalTech',
            'status': 'approved'
        },
        {
            'email': 'helene.barbier@energiq.com',
            'name': 'Hélène Barbier',
            'justification': 'Consultante IA chez EnergiQ',
            'status': 'approved'
        }
    ]
    created_users = []
    for user_data in users_data:
        user = User(**user_data)
        user.set_password('password123')
        if user.status == 'approved':
            user.email_verified_at = datetime.utcnow()
            user.approved_at = datetime.utcnow()
        
        db.session.add(user)
        db.session.flush()  # Pour obtenir l'ID
        
        # Créer les préférences
        preferences = UserPreferences(user_id=user.id)
        db.session.add(preferences)
        
        # Générer une clé API pour les utilisateurs approuvés
        if user.status == 'approved':
            api_key, _ = user.generate_api_key()
            created_users.append((user, api_key))
        else:
            created_users.append((user, None))
    
    db.session.commit()
    
    # Créer des statistiques d'utilisation factices
    create_sample_usage_stats(created_users)
    
    # Créer des métriques système
    create_sample_metrics()
    
    print(f"✅ {len(users_data)} utilisateurs de test créés")

def create_sample_usage_stats(users_with_keys):
    """Crée des statistiques d'utilisation d'exemple"""
    print("📈 Création de statistiques d'utilisation...")
    
    from datetime import datetime, timedelta
    import random
    
    # Endpoints d'exemple
    endpoints = [
        '/api/v1/chat/completions',
        '/api/v1/models',
        '/api/v1/embeddings',
        '/api/v1/completions'
    ]
    
    methods = ['GET', 'POST']
    status_codes = [200, 200, 200, 200, 201, 400, 401, 500]  # Majorité de succès
    models = ['gpt-3.5-turbo', 'gpt-4', 'text-embedding-ada-002', 'text-davinci-003']
    
    # Générer des stats pour les 30 derniers jours
    for i in range(30):
        base_date = datetime.now() - timedelta(days=i)
        
        for user, api_key in users_with_keys:
            if api_key:  # Seulement pour les utilisateurs avec des clés API
                # Générer 5-20 requêtes par jour par utilisateur
                num_requests = random.randint(5, 20)
                
                for _ in range(num_requests):
                    # Ajouter un décalage aléatoire dans la journée
                    request_time = base_date + timedelta(
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    )
                    
                    stats = ApiUsageStats(
                        user_id=user.id,
                        api_key_id=api_key.id,
                        endpoint=random.choice(endpoints),
                        method=random.choice(methods),
                        status_code=random.choice(status_codes),
                        response_time=random.uniform(50, 1500),  # 50ms à 1.5s
                        tokens_used=random.randint(10, 500),
                        model_used=random.choice(models),
                        ip_address=f"192.168.1.{random.randint(1, 254)}",
                        user_agent="Python/requests",
                        request_size=random.randint(100, 2000),
                        response_size=random.randint(200, 5000),
                        created_at=request_time
                    )
                    db.session.add(stats)
    
    db.session.commit()
    print("✅ Statistiques d'utilisation créées")

def create_sample_metrics():
    """Crée des métriques système d'exemple"""
    print("🔧 Création de métriques système...")
    
    import random
    
    metrics = [
        ('cpu_usage', random.uniform(10, 80), '%', 'performance'),
        ('memory_usage', random.uniform(30, 90), '%', 'performance'),
        ('disk_usage', random.uniform(20, 70), '%', 'performance'),
        ('api_response_time', random.uniform(50, 200), 'ms', 'performance'),
        ('active_connections', random.randint(5, 50), 'count', 'usage'),
        ('total_requests_today', random.randint(100, 1000), 'count', 'usage'),
        ('error_rate', random.uniform(0.1, 5.0), '%', 'errors'),
    ]
    
    for name, value, unit, category in metrics:
        metric = SystemMetrics(
            metric_name=name,
            metric_value=value,
            metric_unit=unit,
            category=category
        )
        db.session.add(metric)
    
    db.session.commit()
    print("✅ Métriques système créées")

def show_summary():
    """Affiche un résumé de l'initialisation"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*50)
        print("📋 RÉSUMÉ DE L'INITIALISATION")
        print("="*50)
        
        # Comptes utilisateurs
        total_users = User.query.count()
        admin_users = User.query.filter_by(role='admin').count()
        approved_users = User.query.filter_by(status='approved').count()
        
        print(f"👥 Utilisateurs: {total_users} total ({admin_users} admin, {approved_users} approuvés)")
        
        # Clés API
        total_keys = ApiKey.query.count()
        active_keys = ApiKey.query.filter_by(is_active=True).count()
        
        print(f"🔑 Clés API: {total_keys} total ({active_keys} actives)")
        
        # Notifications
        total_notifications = Notification.query.count()
        unread_notifications = Notification.query.filter_by(is_read=False).count()
        
        print(f"🔔 Notifications: {total_notifications} total ({unread_notifications} non lues)")
        
        # Logs d'audit
        total_logs = AuditLog.query.count()
        
        print(f"📝 Logs d'audit: {total_logs}")
        
        # Statistiques d'utilisation
        total_stats = ApiUsageStats.query.count()
        
        print(f"📊 Statistiques d'utilisation: {total_stats}")
        
        # Métriques système
        total_metrics = SystemMetrics.query.count()
        
        print(f"⚙️  Métriques système: {total_metrics}")
        
        print("\n🌐 Accès à l'application:")
        print(f"   URL: http://localhost:5000")
        print(f"   Admin: {Config.ADMIN_EMAIL} / {Config.ADMIN_PASSWORD}")
        print(f"   Test users: user1@example.com / password123")
        print(f"   API Docs: http://localhost:5000/api-docs/")
        
        print("\n🎯 Prochaines étapes:")
        print("   1. Démarrer l'application: python run.py")
        print("   2. Se connecter avec le compte admin")
        print("   3. Explorer les nouvelles fonctionnalités")
        print("   4. Tester les notifications temps réel")
        print("   5. Consulter les analytics")

if __name__ == '__main__':
    print("🚀 Initialisation de la base de données avec nouvelles fonctionnalités")
    print("⚠️  ATTENTION: Cela va supprimer toutes les données existantes !")
    
    confirm = input("Continuer ? (oui/non): ").lower().strip()
    if confirm in ['oui', 'o', 'yes', 'y']:
        init_database()
        show_summary()
    else:
        print("❌ Initialisation annulée") 