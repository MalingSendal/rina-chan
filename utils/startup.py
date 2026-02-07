import requests

def print_startup_info(app):
    """Print startup information"""
    print(f"""
    ╔══════════════════════════════════════╗
    ║   Rina-chan AI Companion Backend     ║
    ╚══════════════════════════════════════╝
    
    Configuration:
    - Ollama IP: {app.config['OLLAMA_IP']}
    - Ollama Port: {app.config['OLLAMA_PORT']}
    - Model: {app.config['OLLAMA_MODEL']}
    - Character: {app.config['CHARACTER_NAME']}
    
    Starting server on http://{app.config['APP_IP']}:5000
    """)

def check_ollama_connection(app):
    """Check Ollama connection on startup"""
    try:
        response = requests.get(
            f'http://{app.config["OLLAMA_IP"]}:{app.config["OLLAMA_PORT"]}/api/tags', 
            timeout=5
        )
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"\n✓ Ollama is reachable! Available models:")
            for model in models:
                print(f"  - {model.get('name')}")
        else:
            print(f"\n✗ Ollama returned status {response.status_code}")
    except Exception as e:
        print(f"\n✗ Cannot reach Ollama: {e}")
        print(f"  Make sure Ollama is running at {app.config['OLLAMA_IP']}:{app.config['OLLAMA_PORT']}")