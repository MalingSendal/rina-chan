from flask import Blueprint, request, jsonify, send_from_directory
import requests
import os
from utils.memory import load_memory, update_memory_with_conversation, get_memory_summary, get_rina_insight, save_chat_history, generate_mood, retrieve_relevant_memories
from config import DEFAULT_DISCORD_REN_ID, DEFAULT_USER_NAME

chat_bp = Blueprint('chat', __name__)
chat_history = []

@chat_bp.route('/')
def index():
    """Serve the main index.html"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return send_from_directory(base_dir, 'index.html')

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests with memory integration"""
    from app import create_app
    from config import SYSTEM_PROMPT, SYSTEM_PROMPT_NSFW
    from utils.memory import load_memory, save_memory, save_chat_history

    app = create_app()
    
    data = request.get_json() or {}
    user_message = data.get('message', '')
    nsfw_mode = data.get('nsfw_mode', False)
    user_id = data.get('user_id', None)
    user_reference = data.get('user_reference', None)

    if not user_message:
        return jsonify({'response': 'Say something! -pouts-'}), 400

    try:
        memory = load_memory(user_id=user_id)

        uid_str = str(user_id) if user_id else str(DEFAULT_DISCORD_REN_ID)
        is_ren = uid_str == str(DEFAULT_DISCORD_REN_ID)
        
        if is_ren:
            memory['user_name'] = DEFAULT_USER_NAME
        else:
            if user_reference:
                memory['user_name'] = user_reference

        save_memory(memory, user_id=user_id)

        update_memory_with_conversation(memory, user_message, "")

        memory_summary = get_memory_summary(memory)
        rina_insight = get_rina_insight(memory)

        # Retrieve a few relevant long-term items for this query
        relevant_items = retrieve_relevant_memories(memory, user_message, max_results=6)
        relevant_text = ''
        if relevant_items:
            parts = []
            for it in relevant_items:
                parts.append(f"[{it['type']}]: {it['text']}")
            relevant_text = '\n'.join(parts)
        
        # Extract clean username (remove <@ and > from mention format)
        user_display_name = memory['user_name']
        if user_display_name.startswith('<@') and user_display_name.endswith('>'):
            # Already in mention format, use as-is for tagging
            user_display_for_prompt = user_display_name
        else:
            user_display_for_prompt = user_display_name
        
        system_prompt = SYSTEM_PROMPT_NSFW if nsfw_mode else SYSTEM_PROMPT
        
        # Inject memory, feelings, and a short list of relevant past items
        system_prompt_with_memory = f"""{system_prompt}

    === YOUR KNOWLEDGE OF USER ===
    {memory_summary}

    === YOUR PERSONAL FEELINGS ===
    {rina_insight}

    """

        if relevant_text:
            system_prompt_with_memory += f"\n=== RELEVANT PAST MEMORIES ===\n{relevant_text}\n\n"

        system_prompt_with_memory += f"[In your responses, refer to the user as: {user_display_for_prompt}]\n"
        
        ollama_api_url = f'http://{app.config["OLLAMA_IP"]}:{app.config["OLLAMA_PORT"]}/api/generate'
        
        messages = [
            {'role': 'system', 'content': system_prompt_with_memory}
        ]
        
        for msg in chat_history[-10:]:
            messages.append(msg)
        
        messages.append({'role': 'user', 'content': user_message})

        response = requests.post(
            ollama_api_url,
            json={
                'model': app.config['OLLAMA_MODEL'],
                'prompt': format_prompt(messages),
                'stream': False,
                'temperature': 0.7,
            },
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({'response': '*sighs* The connection broke... try again? 💔'}), 500

        response_text = response.json().get('response', 'Hmm? Did you say something?').strip()

        # Now update memory with the full conversation (including bot response)
        update_memory_with_conversation(memory, user_message, response_text)

        # Generate mood tag for this response (using updated memory)
        mood = generate_mood(memory, response_text, nsfw_mode)

        # Enforce allowed mood whitelist before returning (safety)
        allowed_moods = {
            'happy','joyful','excited','sad','depressed','upset','angry','mad','furious',
            'frightened','scared','terrified','sweat','nerveous','anxious','doya','smug','proud',
            'embarassed','flustered','dizzy','suprised','shocked','puzzled','confused','resentful','bitter'
        }

        chat_history.append({'role': 'user', 'content': user_message})
        chat_history.append({'role': 'assistant', 'content': response_text})
        
        # Save chat history to per-user file
        save_chat_history(user_message, response_text, nsfw_mode, user_id=user_id)

        if len(chat_history) > 50:
            chat_history.pop(0)
            chat_history.pop(0)

        # Ensure mood is allowed
        if mood not in allowed_moods:
            mood = 'happy'

        return jsonify({'response': response_text, 'mood': mood})

    except requests.exceptions.ConnectionError:
        return jsonify({
            'response': f'Hmph... I can\'t reach my brain right now. Make sure Ollama is running at {app.config["OLLAMA_IP"]}:{app.config["OLLAMA_PORT"]} 💢'
        }), 500
    except requests.exceptions.Timeout:
        return jsonify({'response': 'This is taking too long... try a simpler question? 😤'}), 500
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'response': 'Something went wrong... sowwy 😭'}), 500

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