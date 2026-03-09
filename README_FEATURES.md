# 🚀 API IA Locale - Fonctionnalités Améliorées

## 📋 Vue d'ensemble

Cette application Flask a été considérablement améliorée avec de nombreuses fonctionnalités modernes et professionnelles pour offrir une expérience utilisateur exceptionnelle dans la gestion des clés API pour l'IA locale.

## ✨ Nouvelles Fonctionnalités

### 🎨 Interface Utilisateur Moderne

- **Dark Mode** : Basculement automatique entre thème clair et sombre
- **Design Responsive** : Interface optimisée pour tous les appareils
- **Animations Fluides** : Transitions et effets visuels agréables
- **Icônes Font Awesome** : Interface riche et intuitive

### 🔔 Système de Notifications en Temps Réel

- **Notifications WebSocket** : Alertes instantanées via Socket.IO
- **Types de notifications** : Info, succès, avertissement, erreur
- **Actions contextuelles** : Boutons d'action directe dans les notifications
- **Historique complet** : Toutes les notifications sont archivées
- **Compteur en temps réel** : Badge avec nombre de notifications non lues

### 📊 Analytics et Statistiques Avancées

- **Dashboard Analytics** : Vue d'ensemble complète pour les administrateurs
- **Graphiques Interactifs** : Utilisation de Plotly.js pour des visualisations dynamiques
- **Métriques en Temps Réel** : Mise à jour automatique des statistiques
- **Top Utilisateurs** : Classement des utilisateurs les plus actifs
- **Analyse des Erreurs** : Suivi détaillé des taux d'erreur

### 🔍 Audit et Traçabilité Complète

- **Journal d'Audit** : Enregistrement de toutes les actions importantes
- **Géolocalisation IP** : Suivi des adresses IP et user agents
- **Historique Détaillé** : Timeline complète des activités utilisateur
- **Alertes de Sécurité** : Détection automatique d'activités suspectes

### 📈 Statistiques d'Utilisation Personnalisées

- **Métriques Personnelles** : Chaque utilisateur voit ses propres statistiques
- **Graphiques d'Évolution** : Suivi de l'utilisation sur 7, 30 ou 90 jours
- **Calculs Automatiques** : Temps de réponse moyen, taux de succès, données transférées
- **Export de Données** : Possibilité d'exporter les statistiques

### 🔒 Sécurité Renforcée

- **Chiffrement des Clés** : Clés API chiffrées avec Fernet
- **Rotation Sécurisée** : Génération et révocation sécurisées des clés
- **Surveillance Continue** : Monitoring automatique des activités
- **Préférences Utilisateur** : Gestion fine des paramètres de sécurité

### 🔍 Recherche Globale

- **Recherche Intelligente** : Barre de recherche globale dans l'interface
- **Résultats Contextuels** : Recherche dans les utilisateurs, clés API, logs
- **Autocomplétion** : Suggestions automatiques pendant la frappe

### 📦 Export et Sauvegarde

- **Export CSV/JSON** : Exportation des données en différents formats
- **Rapports Système** : Génération automatique de rapports complets
- **Sauvegarde Automatique** : Planification de sauvegardes régulières

### 🎯 Gestion des Préférences

- **Thème Personnalisable** : Choix entre clair, sombre ou automatique
- **Paramètres de Notification** : Contrôle fin des alertes
- **Fuseau Horaire** : Adaptation automatique à la localisation
- **Interface Personnalisée** : Layout adaptable selon les préférences

## 🛠️ Technologies Utilisées

### Backend
- **Flask** : Framework web Python
- **SQLAlchemy** : ORM pour la base de données
- **Flask-SocketIO** : WebSockets pour le temps réel
- **Flask-Caching** : Système de cache avec Redis
- **Celery** : Tâches asynchrones
- **Cryptography** : Chiffrement des données sensibles

### Frontend
- **Bootstrap 5** : Framework CSS moderne
- **Socket.IO Client** : Gestion des WebSockets côté client
- **Plotly.js** : Graphiques interactifs
- **Font Awesome** : Icônes vectorielles

### Base de Données
- **Nouveaux Modèles** :
  - `AuditLog` : Journal d'audit complet
  - `Notification` : Système de notifications
  - `UserPreferences` : Préférences utilisateur
  - `ApiUsageStats` : Statistiques d'utilisation détaillées
  - `SystemMetrics` : Métriques système globales

## 🚀 Installation et Configuration

### 1. Installation des Dépendances

```bash
pip install -r requirements.txt
```

### 2. Configuration de l'Environnement

Créez un fichier `.env` avec :

```env
# Base de données
DATABASE_URL=sqlite:///app.db

# Cache Redis
REDIS_URL=redis://localhost:6379/0

# Email (optionnel)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-mot-de-passe

# Sécurité
SECRET_KEY=votre-clé-secrète-très-longue
API_ENCRYPTION_KEY=clé-de-chiffrement-32-caractères

# Administration
ADMIN_EMAIL=admin@votre-domaine.com
ADMIN_PASSWORD=mot-de-passe-admin-fort
```

### 3. Initialisation de la Base de Données

```bash
python scripts/init_db_with_features.py
```

### 4. Démarrage de l'Application

```bash
python run.py
```

### 5. Services Additionnels (Optionnels)

#### Redis (pour le cache et les WebSockets)
```bash
# Installation Redis sur Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server
```

#### Celery (pour les tâches asynchrones)
```bash
# Dans un terminal séparé
celery -A app.celery worker --loglevel=info
```

## 🎮 Utilisation

### Interface Administrateur

1. **Connexion** : Utilisez les identifiants admin configurés
2. **Analytics** : Accédez à `/analytics` pour voir les statistiques globales
3. **Export** : Téléchargez les données via les boutons d'export
4. **Monitoring** : Surveillez les métriques en temps réel

### Interface Utilisateur

1. **Dashboard** : Vue d'ensemble personnalisée de votre utilisation
2. **Notifications** : Cliquez sur la cloche pour voir les alertes
3. **Thème** : Basculez entre clair/sombre avec l'icône lune/soleil
4. **Recherche** : Utilisez la barre de recherche globale
5. **Statistiques** : Consultez vos métriques dans l'onglet "Utilisation"

## 📚 Documentation API

L'application inclut une documentation interactive Swagger accessible à `/api-docs/`

### Nouveaux Endpoints

- `GET /analytics/api/dashboard-stats` : Statistiques générales
- `GET /analytics/api/usage-chart` : Données pour graphiques
- `GET /notifications/api/notifications` : Liste des notifications
- `POST /notifications/api/notifications/{id}/read` : Marquer comme lu
- `GET /dashboard/api/user-stats` : Statistiques utilisateur

## 🔧 Architecture

```
app/
├── analytics/          # Module analytics
├── notifications/      # Module notifications  
├── utils/             # Services utilitaires
│   ├── analytics.py   # Service analytics
│   ├── notifications.py # Service notifications
│   └── export.py      # Service export
├── models.py          # Modèles étendus
└── templates/         # Templates améliorés
    ├── analytics/     # Templates analytics
    └── dashboard/     # Dashboard amélioré
```

## 🎨 Personnalisation

### Thèmes

L'application supporte les thèmes clair et sombre avec persistence locale :

```javascript
// Basculer le thème
function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}
```

### Notifications Personnalisées

```python
from app.utils.notifications import NotificationService

# Créer une notification
NotificationService.create_notification(
    user_id=user.id,
    title="Titre de la notification",
    message="Message détaillé",
    type='success',  # info, success, warning, error
    action_url='/lien-action',
    action_text='Voir détails'
)
```

## 📊 Métriques et Monitoring

### Métriques Collectées

- **Utilisation API** : Nombre de requêtes, erreurs, temps de réponse
- **Activité Utilisateur** : Connexions, actions, préférences
- **Performance Système** : CPU, mémoire, bande passante
- **Sécurité** : Tentatives de connexion, IP suspectes

### Alertes Automatiques

- Dépassement de limites de taux
- Activité suspecte détectée
- Erreurs répétées
- Changements de configuration

## 🔐 Sécurité

### Mesures Implémentées

- **Chiffrement** : Toutes les clés API sont chiffrées
- **Audit Trail** : Traçabilité complète des actions
- **Rate Limiting** : Protection contre les abus
- **Session Management** : Gestion sécurisée des sessions
- **IP Tracking** : Surveillance des adresses IP

## 🚀 Déploiement Production

### Recommandations

1. **Base de données** : Utilisez PostgreSQL plutôt que SQLite
2. **Cache** : Configurez Redis pour la production
3. **Proxy** : Utilisez Nginx comme reverse proxy
4. **SSL** : Activez HTTPS avec certificats valides
5. **Monitoring** : Intégrez avec des outils comme Sentry
6. **Backups** : Configurez des sauvegardes automatiques

### Variables d'Environnement Production

```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=clé-production-très-sécurisée
MAIL_SERVER=smtp.votreserveur.com
MONITORING_ENABLED=true
BACKUP_ENABLED=true
```

## 🧪 Tests

### Données de Test

Le script d'initialisation crée automatiquement :
- 1 compte administrateur
- 3 utilisateurs de test
- 30 jours de statistiques fictives
- Notifications d'exemple
- Métriques système

### Comptes de Test

- **Admin** : admin@votreplateforme.com / admin123
- **Utilisateur 1** : user1@example.com / password123
- **Utilisateur 2** : user2@example.com / password123
- **Utilisateur 3** : user3@example.com / password123

## 🎯 Roadmap

### Fonctionnalités Futures

- [ ] **API Webhooks** : Notifications push vers services externes
- [ ] **Authentification 2FA** : Sécurité renforcée avec TOTP
- [ ] **Gestion d'Équipes** : Organisations et permissions avancées
- [ ] **API Rate Limiting Avancé** : Quotas personnalisés par utilisateur
- [ ] **Intégration CI/CD** : Génération automatique de clés pour les pipelines
- [ ] **Monitoring Avancé** : Intégration Prometheus/Grafana
- [ ] **Machine Learning** : Détection d'anomalies par IA

## 🆘 Support

### Résolution de Problèmes

1. **WebSockets ne fonctionnent pas** : Vérifiez que Redis est démarré
2. **Graphiques vides** : Consultez la console pour les erreurs JavaScript
3. **Notifications manquantes** : Vérifiez la configuration Socket.IO
4. **Erreurs de cache** : Redémarrez Redis

### Contact

- **Email** : support@votreplateforme.com
- **Documentation** : `/api-docs/`
- **Issues** : Utilisez le système de tickets intégré

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

---

*Développé avec ❤️ pour une expérience utilisateur exceptionnelle* 