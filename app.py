import os
from dotenv import load_dotenv
from flask import Flask

# Load environment variables
load_dotenv()

def create_app():
    """Application factory function"""
    app = Flask(__name__, 
                static_folder=os.path.dirname(os.path.abspath(__file__)), 
                static_url_path='')
    
    # Configuration
    app.config.from_mapping(
        OLLAMA_IP=os.getenv('OLLAMA_IP'),
        OLLAMA_PORT=os.getenv('OLLAMA_PORT'),
        OLLAMA_MODEL=os.getenv('OLLAMA_MODEL'),
        CHARACTER_NAME=os.getenv('CHARACTER_NAME'),
        APP_IP=os.getenv('APP_IP'),
        USER=os.getenv('USER'),
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key-change-me')
    )
    
    # Import and register blueprints
    from routes.chat import chat_bp
    from routes.system import system_bp
    from routes.memory import memory_bp
    
    app.register_blueprint(chat_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(memory_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Import startup logic
    from utils.startup import print_startup_info, check_ollama_connection
    from config import SYSTEM_PROMPT, SYSTEM_PROMPT_NSFW
    
    print_startup_info(app)
    check_ollama_connection(app)
    
    debug = os.getenv('FLASK_DEBUG', 'true').lower() in ('1', 'true', 'yes')
    app.run(debug=debug, host=app.config['APP_IP'], port=5000)