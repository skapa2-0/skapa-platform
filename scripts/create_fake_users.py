#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour créer des utilisateurs fictifs réalistes dans la base de données
Basé sur un dataset IT France avec des profils professionnels authentiques
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, UserPreferences, Notification, ApiUsageStats, ActivityLog

# Dataset réaliste IT France
FAKE_USERS_DATA = [
    {
        "name": "Alice Dupont",
        "email": "alice.dupont@scaleway.com",
        "poste": "Ingénieure DevOps",
        "entreprise": "Scaleway",
        "justification": "Intégration d'IA dans nos pipelines CI/CD pour optimiser les déploiements automatiques et améliorer la détection d'anomalies en production."
    },
    {
        "name": "Maxime Lefebvre", 
        "email": "maxime.lefebvre@airbus.com",
        "poste": "Architecte Cloud",
        "entreprise": "Airbus",
        "justification": "Évaluation de solutions IA pour l'optimisation de nos architectures cloud et l'automatisation des processus de scaling dans l'aéronautique."
    },
    {
        "name": "Camille Morel",
        "email": "camille.morel@capgemini.com", 
        "poste": "Développeuse Front-end",
        "entreprise": "Capgemini",
        "justification": "Développement d'interfaces conversationnelles intelligentes pour nos clients et intégration de chatbots IA dans les applications web."
    },
    {
        "name": "Romain Girard",
        "email": "romain.girard@linagora.com",
        "poste": "CTO junior", 
        "entreprise": "LinaGora",
        "justification": "Recherche de solutions IA open-source pour enrichir notre stack technologique et proposer des services d'analyse intelligente à nos clients."
    },
    {
        "name": "Léa Bernard",
        "email": "lea.bernard@banquepopulaire.fr",
        "poste": "Data Scientist",
        "entreprise": "Banque Populaire",
        "justification": "Expérimentation avec des modèles IA pour l'analyse des données financières et la détection de fraudes dans le secteur bancaire."
    },
    {
        "name": "Hugo Rousseau",
        "email": "hugo.rousseau@orange.com",
        "poste": "Ingénieur Réseau", 
        "entreprise": "Orange",
        "justification": "Intégration d'IA pour l'optimisation et la surveillance intelligente de nos infrastructures réseau télécoms à grande échelle."
    },
    {
        "name": "Élodie Millet",
        "email": "elodie.millet@ati-systems.com",
        "poste": "Chef de projet IT",
        "entreprise": "ATI Systems", 
        "justification": "Pilotage de projets d'implémentation IA pour nos clients industriels et évaluation des solutions d'automatisation intelligente."
    },
    {
        "name": "Théo Mercier",
        "email": "theo.mercier@dev-id.fr",
        "poste": "Ingénieur QA",
        "entreprise": "Dev-ID",
        "justification": "Automatisation des tests avec IA pour améliorer la couverture de tests et la génération automatique de cas de test pertinents."
    },
    {
        "name": "Inès Faure",
        "email": "ines.faure@thalesgroup.com",
        "poste": "Analyste Sécurité",
        "entreprise": "Thales Group",
        "justification": "Recherche en cybersécurité utilisant l'IA pour la détection proactive de menaces et l'analyse comportementale dans les systèmes critiques."
    },
    {
        "name": "Julien Fontaine",
        "email": "julien.fontaine@air-france.com",
        "poste": "Ingénieur IA",
        "entreprise": "Air France",
        "justification": "Développement de solutions IA pour l'optimisation des opérations aériennes et l'amélioration de l'expérience client dans l'aviation."
    }
]

def create_fake_users():
    """Crée des utilisateurs fictifs réalistes dans la base de données"""
    
    app = create_app()
    with app.app_context():
        print("🚀 Création d'utilisateurs fictifs réalistes...")
        print("=" * 60)
        
        created_users = []
        
        for user_data in FAKE_USERS_DATA:
            # Vérifier si l'utilisateur existe déjà
            existing_user = User.query.filter_by(email=user_data["email"]).first()
            if existing_user:
                print(f"⚠️  Utilisateur {user_data['name']} ({user_data['email']}) existe déjà")
                continue
            
            # Créer l'utilisateur
            user = User(
                name=user_data["name"],
                email=user_data["email"], 
                justification=user_data["justification"],
                status='approved',  # Directement approuvé
                role='user',
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                email_verified_at=datetime.utcnow() - timedelta(days=random.randint(0, 5)),
                approved_at=datetime.utcnow() - timedelta(days=random.randint(0, 3))
            )
            
            # Mot de passe par défaut sécurisé
            user.set_password('Demo2024!')
            
            db.session.add(user)
            db.session.flush()  # Pour obtenir l'ID
            
            # Créer les préférences par défaut
            preferences = UserPreferences(
                user_id=user.id,
                theme=random.choice(['auto', 'light', 'dark']),
                language='fr',
                notifications_email=True,
                notifications_browser=True,
                dashboard_refresh_rate=random.choice([10, 30, 60])
            )
            db.session.add(preferences)
            
            # Générer une clé API
            api_key, full_key = user.generate_api_key()
            
            # Créer quelques statistiques d'usage fictives pour rendre réaliste
            base_date = user.created_at
            for i in range(random.randint(5, 25)):
                usage_date = base_date + timedelta(days=random.randint(0, 20))
                
                # Statistiques d'usage variées selon le profil
                endpoint_weights = {
                    "Ingénieur": ["/chat/completions", "/completions", "/models"],
                    "Data Scientist": ["/chat/completions", "/embeddings", "/fine-tunes"], 
                    "DevOps": ["/chat/completions", "/models", "/files"],
                    "Default": ["/chat/completions", "/models"]
                }
                
                profile_type = "Default"
                if "Ingénieur" in user_data["poste"]:
                    profile_type = "Ingénieur"
                elif "Data Scientist" in user_data["poste"]:
                    profile_type = "Data Scientist"
                elif "DevOps" in user_data["poste"]:
                    profile_type = "DevOps"
                
                endpoint = random.choice(endpoint_weights[profile_type])
                
                usage = ApiUsageStats(
                    user_id=user.id,
                    api_key_id=api_key.id,
                    endpoint=endpoint,
                    method="POST",
                    status_code=random.choices([200, 429, 500], weights=[85, 10, 5])[0],
                    response_time=random.uniform(100, 2000),
                    tokens_used=random.randint(50, 1500),
                    model_used="kr-7b-instruct",
                    ip_address=f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
                    created_at=usage_date
                )
                db.session.add(usage)
            
            # Créer quelques logs d'activité
            activities = [
                ("user_registered", "Inscription sur la plateforme"),
                ("email_verified", "Email vérifié avec succès"),
                ("account_approved", "Compte approuvé par l'administrateur"),
                ("api_key_generated", "Première clé API générée"),
                ("first_api_call", "Première utilisation de l'API")
            ]
            
            for j, (action, description) in enumerate(activities):
                log_date = user.created_at + timedelta(hours=j*2)
                activity = ActivityLog(
                    user_id=user.id,
                    action=action,
                    description=description,
                    ip_address=f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
                    created_at=log_date
                )
                db.session.add(activity)
            
            created_users.append(user)
            print(f"✅ Créé: {user.name} ({user_data['poste']} chez {user_data['entreprise']})")
        
        # Sauvegarder tous les changements
        db.session.commit()
        
        print("=" * 60)
        print(f"🎉 {len(created_users)} utilisateurs fictifs créés avec succès!")
        
        # Créer des notifications de bienvenue pour les nouveaux utilisateurs
        print("\n📧 Création des notifications de bienvenue...")
        
        for user in created_users:
            # Notification de bienvenue
            welcome_notif = Notification(
                user_id=user.id,
                title="Bienvenue sur la plateforme IA !",
                message=f"Bonjour {user.name.split()[0]} ! Votre compte a été approuvé. Découvrez toutes les fonctionnalités de notre API IA locale.",
                type='success',
                action_url='/dashboard',
                action_text='Découvrir le dashboard',
                created_at=user.approved_at + timedelta(minutes=10)
            )
            db.session.add(welcome_notif)
            
            # Notification sur les nouvelles fonctionnalités
            features_notif = Notification(
                user_id=user.id,
                title="Nouvelles fonctionnalités disponibles",
                message="Analytics avancés, système de support, mode sombre et bien plus ! Explorez toutes les améliorations.",
                type='info',
                action_url='/analytics',
                action_text='Voir les analytics',
                created_at=user.approved_at + timedelta(hours=1)
            )
            db.session.add(features_notif)
            
            # Notification clé API
            api_notif = Notification(
                user_id=user.id,
                title="Clé API générée",
                message="Votre clé API a été générée automatiquement. Vous pouvez la consulter dans votre dashboard.",
                type='info',
                action_url='/dashboard',
                action_text='Voir ma clé API',
                created_at=user.approved_at + timedelta(hours=2)
            )
            db.session.add(api_notif)
        
        db.session.commit()
        print(f"✅ Notifications créées pour tous les utilisateurs")
        
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES UTILISATEURS CRÉÉS:")
        print("=" * 60)
        
        for user_data in FAKE_USERS_DATA:
            user = User.query.filter_by(email=user_data["email"]).first()
            if user:
                api_key = user.get_active_api_key()
                usage_count = ApiUsageStats.query.filter_by(user_id=user.id).count()
                
                print(f"""
👤 {user.name}
   📧 Email: {user.email}
   🏢 Poste: {user_data['poste']} chez {user_data['entreprise']}
   🔑 Clé API: {api_key.key_prefix}... (Active)
   📊 Utilisations simulées: {usage_count} requêtes
   🔐 Mot de passe: Demo2024!
   ✅ Statut: Approuvé et prêt à utiliser
                """)
        
        print("=" * 60)
        print("🎯 INSTRUCTIONS POUR TESTER:")
        print("1. Connectez-vous avec n'importe quel email ci-dessus")
        print("2. Mot de passe: Demo2024!")
        print("3. Explorez le dashboard avec données réalistes")
        print("4. Testez les analytics avec historique simulé") 
        print("5. Consultez les notifications de bienvenue")
        print("=" * 60)

if __name__ == "__main__":
    create_fake_users() 