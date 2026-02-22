from flask import Blueprint, jsonify, current_app
import requests

system_bp = Blueprint('system', __name__)

# Reuse a single session for health-check calls
_health_session = requests.Session()


@system_bp.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    cfg = current_app.config
    return jsonify({
        'ollama_ip': cfg['OLLAMA_IP'],
        'ollama_port': cfg['OLLAMA_PORT'],
        'ollama_model': cfg['OLLAMA_MODEL'],
        'character_name': cfg['CHARACTER_NAME'],
        'app_ip': cfg['APP_IP'],
        'num_ctx': cfg.get('OLLAMA_NUM_CTX')
    })


@system_bp.route('/health', methods=['GET'])
def health_check():
    """Check if Ollama is reachable"""
    cfg = current_app.config
    try:
        response = _health_session.get(
            f'http://{cfg["OLLAMA_IP"]}:{cfg["OLLAMA_PORT"]}/api/tags',
            timeout=5
        )
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            return jsonify({
                'status': 'ok',
                'ollama_reachable': True,
                'available_models': model_names
            })
    except Exception:
        pass

    return jsonify({
        'status': 'error',
        'ollama_reachable': False,
        'message': f'Cannot reach Ollama at {cfg["OLLAMA_IP"]}:{cfg["OLLAMA_PORT"]}'
    }), 500
