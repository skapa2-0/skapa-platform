from flask import request, jsonify, current_app
from app.api import bp
from app.models import ApiKey, User
from datetime import datetime, timedelta
import time
from app import db

# Dictionnaire pour le rate limiting simple (en production, utiliser Redis)
rate_limit_storage = {}

def check_rate_limit(api_key_id, limit_per_hour=100):
    """Vérifie le rate limiting pour une clé API"""
    now = time.time()
    hour_ago = now - 3600
    
    if api_key_id not in rate_limit_storage:
        rate_limit_storage[api_key_id] = []
    
    # Nettoie les anciennes entrées
    rate_limit_storage[api_key_id] = [
        timestamp for timestamp in rate_limit_storage[api_key_id] 
        if timestamp > hour_ago
    ]
    
    # Vérifie la limite
    if len(rate_limit_storage[api_key_id]) >= limit_per_hour:
        return False, 0
    
    # Ajoute la requête actuelle
    rate_limit_storage[api_key_id].append(now)
    remaining = limit_per_hour - len(rate_limit_storage[api_key_id])
    
    return True, remaining

@bp.route('/validate-key', methods=['POST'])
def validate_key():
    """Endpoint pour valider une clé API en utilisant la SECRET_KEY"""
    try:
        data = request.get_json()
        
        if not data or 'api_key' not in data:
            return jsonify({
                'valid': False,
                'error': 'Clé API manquante'
            }), 400
        
        api_key_value = data['api_key']
        
        # Vérifie si la clé fournie correspond à la SECRET_KEY
        if api_key_value != current_app.config['SECRET_KEY']:
            return jsonify({
                'valid': False,
                'error': 'Clé API invalide'
            }), 401
        
        # Récupère tous les utilisateurs approuvés avec leurs clés API actives
        approved_users_with_keys = []
        
        # Requête optimisée : seulement les utilisateurs approuvés avec clés actives
        users = User.query.filter_by(status='approved').all()
        
        for user in users:
            # Récupère les clés API actives de l'utilisateur
            active_keys = ApiKey.query.filter_by(user_id=user.id, is_active=True).all()
            
            if active_keys:  # Seulement si l'utilisateur a des clés actives
                # Prendre la clé la plus récente
                latest_key = max(active_keys, key=lambda k: k.created_at)
                
                user_data = {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'status': user.status,
                    'created_at': user.created_at.isoformat() + 'Z',
                    'api_key': latest_key.reconstruct_key() if hasattr(latest_key, 'reconstruct_key') else latest_key.key
                }
                
                approved_users_with_keys.append(user_data)
        
        # Format de réponse compatible avec le système de cache
        return jsonify(approved_users_with_keys)
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': 'Erreur interne du serveur'
        }), 500

@bp.route('/validate-single-key', methods=['POST'])
def validate_single_key():
    """Endpoint pour valider une clé API individuelle"""
    try:
        data = request.get_json()
        
        if not data or 'key_to_validate' not in data:
            return jsonify({
                'valid': False,
                'error': 'Clé à valider manquante'
            }), 400
        
        key_to_validate = data['key_to_validate']
        
        # Cherche la clé dans la base de données
        api_key = ApiKey.find_by_key(key_to_validate)
        
        if not api_key:
            return jsonify({
                'valid': False,
                'error': 'Clé API non trouvée'
            }), 404
        
        # Vérifie que l'utilisateur est approuvé
        if api_key.user.status != 'approved':
            return jsonify({
                'valid': False,
                'error': 'Utilisateur non approuvé'
            }), 403
        
        # Met à jour la date de dernière utilisation
        api_key.update_last_used()
        
        return jsonify({
            'valid': True,
            'user': {
                'id': api_key.user.id,
                'email': api_key.user.email,
                'name': api_key.user.name,
                'status': api_key.user.status
            },
            'api_key': {
                'id': api_key.id,
                'prefix': api_key.key_prefix,
                'created_at': api_key.created_at.isoformat() + 'Z',
                'last_used_at': api_key.last_used_at.isoformat() + 'Z' if api_key.last_used_at else None
            }
        })
        
    except Exception as e:
        # Log l'erreur pour le débogage
        current_app.logger.error(f"Erreur dans /api/v1/validate-key: {e}")
        return jsonify({
            'valid': False,
            'error': 'Erreur interne du serveur'
        }), 500

@bp.route('/report-usage', methods=['POST'])
def report_usage():
    """Receives token usage reports from the API gateway"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing data'}), 400

        api_key_value = data.get('api_key')
        if not api_key_value:
            return jsonify({'error': 'Missing api_key'}), 400

        api_key = ApiKey.find_by_key(api_key_value)
        if not api_key:
            return jsonify({'error': 'Invalid API key'}), 404

        user = api_key.user
        prompt_tokens = data.get('prompt_tokens', 0)
        completion_tokens = data.get('completion_tokens', 0)
        total_tokens = prompt_tokens + completion_tokens
        model = data.get('model', 'unknown')

        user.total_tokens_consumed = (user.total_tokens_consumed or 0) + total_tokens
        user.total_prompt_tokens = (user.total_prompt_tokens or 0) + prompt_tokens
        user.total_completion_tokens = (user.total_completion_tokens or 0) + completion_tokens

        from app.models import ApiUsageStats
        ApiUsageStats.log_api_usage(
            user_id=user.id,
            api_key_id=api_key.id,
            endpoint='/v1/chat/completions',
            method='POST',
            status_code=data.get('status_code', 200),
            response_time=data.get('response_time_ms'),
            tokens_used=total_tokens,
            model_used=model,
            ip_address=data.get('client_ip'),
            request_size=data.get('request_size'),
            response_size=data.get('response_size')
        )

        db.session.commit()

        return jsonify({
            'success': True,
            'total_tokens_consumed': user.total_tokens_consumed,
            'credits_remaining': user.credits
        })

    except Exception as e:
        current_app.logger.error(f"Error in report-usage: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal error'}), 500


@bp.route('/health', methods=['GET'])
def health():
    """Endpoint de santé de l'API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })