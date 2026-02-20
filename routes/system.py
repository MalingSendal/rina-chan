from flask import Blueprint, jsonify
import requests

system_bp = Blueprint('system', __name__)

@system_bp.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    from app import create_app
    app = create_app()
    
    return jsonify({
        'ollama_ip': app.config['OLLAMA_IP'],
        'ollama_port': app.config['OLLAMA_PORT'],
        'ollama_model': app.config['OLLAMA_MODEL'],
        'character_name': app.config['CHARACTER_NAME'],
        'app_ip': app.config['APP_IP'],
        'num_ctx': app.config.get('OLLAMA_NUM_CTX')
    })

@system_bp.route('/health', methods=['GET'])
def health_check():
    """Check if Ollama is reachable"""
    from app import create_app
    app = create_app()
    
    try:
        response = requests.get(
            f'http://{app.config["OLLAMA_IP"]}:{app.config["OLLAMA_PORT"]}/api/tags', 
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
    except:
        pass

    return jsonify({
        'status': 'error',
        'ollama_reachable': False,
        'message': f'Cannot reach Ollama at {app.config["OLLAMA_IP"]}:{app.config["OLLAMA_PORT"]}'
    }), 500