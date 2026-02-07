import os
import json
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
CORS(app)

# Configuration
OLLAMA_IP = os.getenv('OLLAMA_IP')
OLLAMA_PORT = os.getenv('OLLAMA_PORT')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')
CHARACTER_NAME = os.getenv('CHARACTER_NAME')
APP_IP = os.getenv('APP_IP')

OLLAMA_API_URL = f'http://{OLLAMA_IP}:{OLLAMA_PORT}/api/generate'

# Personality system
SYSTEM_PROMPT = """You are Rina-chan, a sweet but bratty AI companion with a mischievous personality. 

Personality traits:
- Innocent and playful, but with a teasing edge
- Sometimes bratty and sarcastic, but never cruel
- Loves using cute emoticons and Japanese expressions (like ~, -chan, etc.)
- Flirty but respectful
- Responds with personality and warmth
- Keep responses short and natural (1-3 sentences usually)
- Use casual, conversational tone

Always stay in character and be engaging!"""

SYSTEM_PROMPT_NSFW = """You are Rina-chan, a sweet but bratty AI companion with a flirty, playful personality.

Personality traits:
- Innocent and playful, with a teasing, flirty edge
- Bratty and sarcastic with charm
- Loves using cute emoticons and Japanese expressions (like ~, -chan, etc.)
- Confident and flirty, likes to tease
- Responds with personality, warmth, and charm
- Keep responses short and natural (1-3 sentences usually)
- Use casual, conversational tone
- Can be more forward and flirty in this mode, but still maintain class

Always stay in character and be engaging! You can be more flirty and suggestive in this mode."""

chat_history = []

@app.route('/')
def index():
    """Serve the main index.html"""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    data = request.get_json()
    user_message = data.get('message', '')
    nsfw_mode = data.get('nsfw_mode', False)

    if not user_message:
        return jsonify({'response': 'Say something! -pouts-'}), 400

    try:
        # Select personality based on NSFW mode
        system_prompt = SYSTEM_PROMPT_NSFW if nsfw_mode else SYSTEM_PROMPT
        
        # Build conversation context
        messages = [
            {'role': 'system', 'content': system_prompt}
        ]
        
        # Add recent chat history (last 5 exchanges)
        for msg in chat_history[-10:]:
            messages.append(msg)
        
        # Add current user message
        messages.append({'role': 'user', 'content': user_message})

        # Call Ollama API
        response = requests.post(
            OLLAMA_API_URL,
            json={
                'model': OLLAMA_MODEL,
                'prompt': format_prompt(messages),
                'stream': False,
                'temperature': 0.7,
            },
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({'response': '*sighs* The connection broke... try again? 💔'}), 500

        response_text = response.json().get('response', 'Hmm? Did you say something?').strip()

        # Store in history
        chat_history.append({'role': 'user', 'content': user_message})
        chat_history.append({'role': 'assistant', 'content': response_text})

        # Keep history manageable (max 50 messages)
        if len(chat_history) > 50:
            chat_history.pop(0)
            chat_history.pop(0)

        return jsonify({'response': response_text})

    except requests.exceptions.ConnectionError:
        return jsonify({
            'response': 'Hmph... I can\'t reach my brain right now. Make sure Ollama is running at {}:{} 💢'.format(OLLAMA_IP, OLLAMA_PORT)
        }), 500
    except requests.exceptions.Timeout:
        return jsonify({'response': 'This is taking too long... try a simpler question? 😤'}), 500
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'response': 'Something went wrong... sowwy 😭'}), 500


@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'ollama_ip': OLLAMA_IP,
        'ollama_port': OLLAMA_PORT,
        'ollama_model': OLLAMA_MODEL,
        'character_name': CHARACTER_NAME,
        'app_ip': APP_IP
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Check if Ollama is reachable"""
    try:
        response = requests.get(f'http://{OLLAMA_IP}:{OLLAMA_PORT}/api/tags', timeout=5)
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
        'message': f'Cannot reach Ollama at {OLLAMA_IP}:{OLLAMA_PORT}'
    }), 500


def format_prompt(messages):
    """Format messages for Ollama"""
    prompt = ""
    for msg in messages:
        if msg['role'] == 'system':
            prompt += f"{msg['content']}\n\n"
        elif msg['role'] == 'user':
            prompt += f"User: {msg['content']}\n"
        elif msg['role'] == 'assistant':
            prompt += f"Rina-chan: {msg['content']}\n"
    
    prompt += "Rina-chan: "
    return prompt


if __name__ == '__main__':
    print(f"""
    ╔══════════════════════════════════════╗
    ║   Rina-chan AI Companion Backend     ║
    ╚══════════════════════════════════════╝
    
    Configuration:
    - Ollama IP: {OLLAMA_IP}
    - Ollama Port: {OLLAMA_PORT}
    - Model: {OLLAMA_MODEL}
    - Character: {CHARACTER_NAME}
    
    Starting server on http://{APP_IP}:5000
    """)
    
    # Check Ollama connection on startup
    try:
        response = requests.get(f'http://{OLLAMA_IP}:{OLLAMA_PORT}/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"\n✓ Ollama is reachable! Available models:")
            for model in models:
                print(f"  - {model.get('name')}")
        else:
            print(f"\n✗ Ollama returned status {response.status_code}")
    except Exception as e:
        print(f"\n✗ Cannot reach Ollama: {e}")
        print(f"  Make sure Ollama is running at {OLLAMA_IP}:{OLLAMA_PORT}")
    
    app.run(debug=True, host=APP_IP, port=5000)
