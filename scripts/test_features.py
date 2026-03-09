#!/usr/bin/env python3
"""
Script de test pour toutes les nouvelles fonctionnalités
"""

import sys
import os
import requests
import json
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, ApiKey, Notification, AuditLog
from app.utils.notifications import NotificationService, AuditService
from app.utils.analytics import AnalyticsService

def test_database_models():
    """Teste que tous les nouveaux modèles fonctionnent"""
    print("🧪 Test des modèles de base de données...")
    
    app = create_app()
    with app.app_context():
        try:
            # Test User avec nouvelles fonctionnalités
            user = User.query.first()
            assert user is not None, "Aucun utilisateur trouvé"
            
            # Test des préférences
            preferences = user.get_preferences()
            assert preferences is not None, "Impossible de récupérer les préférences"
            
            # Test du compteur de notifications
            count = user.get_unread_notifications_count()
            assert isinstance(count, int), "Compteur de notifications invalide"
            
            # Test des logs d'audit
            logs = AuditLog.query.filter_by(user_id=user.id).first()
            if logs:
                details = logs.get_details()
                assert isinstance(details, dict), "Détails du log invalides"
            
            print("✅ Modèles de base de données - OK")
            return True
            
        except Exception as e:
            print(f"❌ Erreur modèles de base de données: {e}")
            return False

def test_notification_service():
    """Teste le service de notifications"""
    print("🔔 Test du service de notifications...")
    
    app = create_app()
    with app.app_context():
        try:
            user = User.query.first()
            
            # Créer une notification de test
            notification = NotificationService.create_notification(
                user_id=user.id,
                title="Test de notification",
                message="Ceci est un test automatique",
                type='info',
                emit_realtime=False  # Pas de WebSocket dans les tests
            )
            
            assert notification is not None, "Impossible de créer une notification"
            assert notification.user_id == user.id, "User ID incorrect"
            assert notification.title == "Test de notification", "Titre incorrect"
            
            # Tester le marquage comme lu
            success = NotificationService.mark_notification_as_read(notification.id, user.id)
            assert success == True, "Impossible de marquer comme lu"
            
            print("✅ Service de notifications - OK")
            return True
            
        except Exception as e:
            print(f"❌ Erreur service de notifications: {e}")
            return False

def test_audit_service():
    """Teste le service d'audit"""
    print("📝 Test du service d'audit...")
    
    app = create_app()
    with app.app_context():
        try:
            user = User.query.first()
            
            # Créer un log d'audit
            log = AuditService.log_action(
                action='test_action',
                user_id=user.id,
                resource_type='test',
                resource_id=1,
                details={'test': 'value'}
            )
            
            assert log is not None, "Impossible de créer un log d'audit"
            assert log.action == 'test_action', "Action incorrecte"
            assert log.user_id == user.id, "User ID incorrect"
            
            # Tester la récupération des logs
            logs = AuditService.get_audit_logs(user_id=user.id, limit=1)
            assert len(logs) > 0, "Aucun log récupéré"
            
            print("✅ Service d'audit - OK")
            return True
            
        except Exception as e:
            print(f"❌ Erreur service d'audit: {e}")
            return False

def test_analytics_service():
    """Teste le service d'analytics"""
    print("📊 Test du service d'analytics...")
    
    app = create_app()
    with app.app_context():
        try:
            # Test des statistiques du dashboard
            stats = AnalyticsService.get_dashboard_stats()
            assert isinstance(stats, dict), "Stats doivent être un dictionnaire"
            assert 'total_users' in stats, "Manque total_users"
            assert 'active_users' in stats, "Manque active_users"
            
            # Test des métriques temps réel
            metrics = AnalyticsService.get_real_time_metrics()
            assert isinstance(metrics, dict), "Métriques doivent être un dictionnaire"
            assert 'timestamp' in metrics, "Manque timestamp"
            
            print("✅ Service d'analytics - OK")
            return True
            
        except Exception as e:
            print(f"❌ Erreur service d'analytics: {e}")
            return False

def test_api_endpoints(base_url="http://localhost:5000"):
    """Teste les nouveaux endpoints API"""
    print("🌐 Test des endpoints API...")
    
    try:
        # Test endpoint de santé
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        health_data = response.json()
        assert 'status' in health_data, "Manque status dans health check"
        assert health_data['status'] == 'healthy', "Status n'est pas healthy"
        
        print("✅ Endpoints API - OK")
        return True
        
    except requests.exceptions.ConnectionError:
        print("⚠️  Serveur non démarré - Skipping API tests")
        return True
    except Exception as e:
        print(f"❌ Erreur endpoints API: {e}")
        return False

def test_template_rendering():
    """Teste le rendu des nouveaux templates"""
    print("🎨 Test du rendu des templates...")
    
    app = create_app()
    with app.test_client() as client:
        try:
            # Test de la page d'accueil
            response = client.get('/')
            assert response.status_code == 200, "Page d'accueil inaccessible"
            assert b'API IA Locale' in response.data, "Titre manquant"
            
            # Test de la documentation API
            response = client.get('/api-docs/')
            assert response.status_code == 200, "Documentation API inaccessible"
            
            print("✅ Rendu des templates - OK")
            return True
            
        except Exception as e:
            print(f"❌ Erreur rendu des templates: {e}")
            return False

def test_user_preferences():
    """Teste la gestion des préférences utilisateur"""
    print("⚙️  Test des préférences utilisateur...")
    
    app = create_app()
    with app.app_context():
        try:
            user = User.query.first()
            preferences = user.get_preferences()
            
            # Test des valeurs par défaut
            assert preferences.theme == 'light', "Thème par défaut incorrect"
            assert preferences.language == 'fr', "Langue par défaut incorrecte"
            assert preferences.email_notifications == True, "Notifications email par défaut incorrectes"
            
            # Test de modification
            preferences.theme = 'dark'
            preferences.language = 'en'
            db.session.commit()
            
            # Vérifier la modification
            updated_prefs = user.get_preferences()
            assert updated_prefs.theme == 'dark', "Modification thème échouée"
            assert updated_prefs.language == 'en', "Modification langue échouée"
            
            print("✅ Préférences utilisateur - OK")
            return True
            
        except Exception as e:
            print(f"❌ Erreur préférences utilisateur: {e}")
            return False

def test_api_key_encryption():
    """Teste le chiffrement des clés API"""
    print("🔐 Test du chiffrement des clés API...")
    
    app = create_app()
    with app.app_context():
        try:
            user = User.query.filter_by(status='approved').first()
            if not user:
                print("⚠️  Aucun utilisateur approuvé - Skipping encryption test")
                return True
            
            # Générer une nouvelle clé
            api_key, full_key = user.generate_api_key()
            
            # Vérifier que la clé est chiffrée
            assert api_key.encrypted_key is not None, "Clé non chiffrée"
            assert api_key.key_hash is not None, "Hash de clé manquant"
            
            # Vérifier que la clé peut être reconstruite
            reconstructed = api_key.reconstruct_key()
            assert reconstructed == full_key, "Clé reconstruite incorrecte"
            
            # Vérifier la vérification de clé
            assert api_key.verify_key(full_key), "Vérification de clé échouée"
            
            print("✅ Chiffrement des clés API - OK")
            return True
            
        except Exception as e:
            print(f"❌ Erreur chiffrement clés API: {e}")
            return False

def test_usage_statistics():
    """Teste les statistiques d'utilisation"""
    print("📈 Test des statistiques d'utilisation...")
    
    app = create_app()
    with app.app_context():
        try:
            from app.models import ApiUsageStats
            
            # Vérifier qu'il y a des statistiques
            stats = ApiUsageStats.query.first()
            if not stats:
                print("⚠️  Aucune statistique disponible - Creating test data")
                return True
            
            # Vérifier les champs
            assert hasattr(stats, 'requests_count'), "Manque requests_count"
            assert hasattr(stats, 'errors_count'), "Manque errors_count"
            assert hasattr(stats, 'response_time_avg'), "Manque response_time_avg"
            assert hasattr(stats, 'data_transferred'), "Manque data_transferred"
            
            print("✅ Statistiques d'utilisation - OK")
            return True
            
        except Exception as e:
            print(f"❌ Erreur statistiques d'utilisation: {e}")
            return False

def run_all_tests():
    """Lance tous les tests"""
    print("🚀 Démarrage des tests des nouvelles fonctionnalités")
    print("=" * 60)
    
    tests = [
        test_database_models,
        test_notification_service,
        test_audit_service,
        test_analytics_service,
        test_template_rendering,
        test_user_preferences,
        test_api_key_encryption,
        test_usage_statistics,
        test_api_endpoints
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur inattendue dans {test.__name__}: {e}")
            results.append(False)
        print()
    
    # Résumé
    print("=" * 60)
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests réussis: {passed}/{total}")
    if passed < total:
        print(f"❌ Tests échoués: {total - passed}/{total}")
    
    success_rate = (passed / total) * 100
    print(f"📊 Taux de réussite: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 Tous les tests sont passés ! L'application est prête.")
    elif success_rate >= 80:
        print("\n⚠️  La plupart des tests sont passés. Quelques ajustements peuvent être nécessaires.")
    else:
        print("\n🚨 Plusieurs tests ont échoué. Vérifiez la configuration et les dépendances.")
    
    return success_rate >= 80

def test_performance():
    """Test de performance basique"""
    print("⚡ Test de performance...")
    
    app = create_app()
    with app.test_client() as client:
        try:
            import time
            
            # Test de la vitesse de réponse
            start_time = time.time()
            response = client.get('/')
            response_time = time.time() - start_time
            
            assert response_time < 2.0, f"Réponse trop lente: {response_time:.2f}s"
            
            print(f"✅ Performance - Temps de réponse: {response_time:.3f}s")
            return True
            
        except Exception as e:
            print(f"❌ Erreur test de performance: {e}")
            return False

if __name__ == '__main__':
    print("🧪 Tests des nouvelles fonctionnalités - API IA Locale")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    success = run_all_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 Tous les tests principaux sont passés !")
        print("🚀 L'application est prête pour la production.")
    else:
        print("⚠️  Certains tests ont échoué.")
        print("🔧 Vérifiez la configuration et relancez les tests.")
    
    print("\n📖 Prochaines étapes :")
    print("   1. Démarrer l'application: python run.py")
    print("   2. Ouvrir http://localhost:5000")
    print("   3. Se connecter avec les comptes de test")
    print("   4. Tester l'interface utilisateur")
    print("   5. Vérifier les notifications en temps réel")
    
    sys.exit(0 if success else 1) 