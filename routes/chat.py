from flask import Blueprint, request, jsonify, send_from_directory
import requests
import os
from utils.memory import (load_memory, update_memory_with_conversation, 
                          get_memory_summary, get_rina_insight, save_chat_history, 
                          generate_mood, retrieve_relevant_memories, 
                          update_communication_style_from_mood, summarize_text)
from config import DEFAULT_DISCORD_REN_ID, DEFAULT_USER_NAME

chat_bp = Blueprint('chat', __name__)
# In-memory session history - keep last 5 exchanges (10 messages total)
chat_history = []

# Allowed moods for validation
ALLOWED_MOODS = {
    'happy','joyful','excited','sad','depressed','upset','angry','mad','furious',
    'frightened','scared','terrified','sweat','nerveous','anxious','doya','smug','proud',
    'embarassed','flustered','dizzy','suprised','shocked','puzzled','confused','resentful','bitter'
}

# How often to perform a full memory analysis (personality, conclusions)
FULL_UPDATE_INTERVAL = 5

@chat_bp.route('/')
def index():
    """Serve the main index.html"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return send_from_directory(base_dir, 'index.html')

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests with memory integration and optimizations"""
    from app import create_app
    from config import SYSTEM_PROMPT, SYSTEM_PROMPT_NSFW

    app = create_app()
    
    data = request.get_json() or {}
    user_message = data.get('message', '')
    nsfw_mode = data.get('nsfw_mode', False)
    user_id = data.get('user_id', None)
    user_reference = data.get('user_reference', None)

    if not user_message:
        return jsonify({'response': 'Say something! -pouts-'}), 400

    try:
        # 1. Load memory for this user
        memory = load_memory(user_id=user_id)
        uid_str = str(user_id) if user_id else str(DEFAULT_DISCORD_REN_ID)
        is_ren = uid_str == str(DEFAULT_DISCORD_REN_ID)
        
        # Update user name if needed
        if is_ren:
            memory['user_name'] = DEFAULT_USER_NAME
        elif user_reference:
            memory['user_name'] = user_reference

        # 2. ALWAYS summarize user message (remove word count check)
        #    Use 2 sentences max, 250 chars – keeps it short for faster LLM processing
        prompt_message = summarize_text(user_message, max_sentences=2, max_chars=250)
        # Add a note if it was actually shortened (so the AI knows it's a summary)
        if prompt_message != user_message:
            prompt_message += " [summarized]"

        # 3. Build memory context using cached summaries
        memory_summary = get_memory_summary(memory)
        rina_insight = get_rina_insight(memory)
        
        # Get relevant memories (limited to 4 items max for speed)
        relevant_items = retrieve_relevant_memories(memory, prompt_message, max_results=4)
        
        relevant_text = ''
        if relevant_items:
            relevant_text = '\n'.join(f"[{it['type']}]: {it['text']}" for it in relevant_items)

        # 4. Build system prompt with memory context
        system_prompt = SYSTEM_PROMPT_NSFW if nsfw_mode else SYSTEM_PROMPT
        system_prompt_with_memory = f"""{system_prompt}

=== YOUR KNOWLEDGE OF USER ===
{memory_summary}

=== YOUR PERSONAL FEELINGS ===
{rina_insight}
"""
        if relevant_text:
            system_prompt_with_memory += f"\n=== RELEVANT PAST MEMORIES ===\n{relevant_text}\n"
        
        system_prompt_with_memory += f"\n[In your responses, refer to the user as: {memory['user_name']}]\n"

        # 5. Prepare conversation context (last 5 exchanges only to reduce tokens)
        messages = [{'role': 'system', 'content': system_prompt_with_memory}]
        
        # Add last 5 exchanges from session history (if any)
        session_context = chat_history[-10:] if len(chat_history) > 10 else chat_history
        messages.extend(session_context)
        messages.append({'role': 'user', 'content': prompt_message})

        # 6. Call Ollama with optimized parameters
        ollama_api_url = f'http://{app.config["OLLAMA_IP"]}:{app.config["OLLAMA_PORT"]}/api/generate'
        
        response = requests.post(
            ollama_api_url,
            json={
                'model': app.config['OLLAMA_MODEL'],
                'prompt': format_prompt(messages),
                'stream': False,
                'temperature': 0.7,
                'max_tokens': 300,  # Limit response length
                'num_ctx': int(app.config.get('OLLAMA_NUM_CTX')),  # Context window
            },
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({'response': '*sighs* The connection broke... try again? 💔'}), 500

        response_text = response.json().get('response', 'Hmm? Did you say something?').strip()

        # 7. Determine if we should do a full memory update (every N messages)
        conv_count = memory.get('conversation_count', 0)
        # Do full update on first few messages or periodically
        full_update = (conv_count < 5) or (conv_count % FULL_UPDATE_INTERVAL == 0)

        # 8. Update memory with both user and bot messages (single call)
        update_memory_with_conversation(memory, user_message, response_text, full_update=full_update)

        # 9. Generate mood (lightweight)
        mood = generate_mood(memory, response_text, nsfw_mode)
        if mood not in ALLOWED_MOODS:
            mood = 'happy'
        
        # Update communication style based on mood
        update_communication_style_from_mood(memory, mood)

        # 10. Update session chat history (keep last 5 exchanges = 10 messages)
        chat_history.append({'role': 'user', 'content': user_message})
        chat_history.append({'role': 'assistant', 'content': response_text})
        
        # Keep only last 10 messages (5 exchanges)
        if len(chat_history) > 10:
            # Remove oldest 2 messages (one exchange)
            chat_history.pop(0)
            chat_history.pop(0)

        # 11. Save to per-user history file (non-blocking in production, but fine here)
        save_chat_history(user_message, response_text, nsfw_mode, user_id=user_id)

        return jsonify({
            'response': response_text, 
            'mood': mood,
            'summarized': prompt_message != user_message  # Let frontend know if summarized
        })

    except requests.exceptions.ConnectionError:
        return jsonify({
            'response': f'Hmph... I can\'t reach my brain right now. Make sure Ollama is running at {app.config["OLLAMA_IP"]}:{app.config["OLLAMA_PORT"]} 💢'
        }), 500
    except requests.exceptions.Timeout:
        return jsonify({'response': 'This is taking too long... try a simpler question? 😤'}), 500
    except Exception as e:
        print(f'Error in chat endpoint: {e}')
        return jsonify({'response': 'Something went wrong... sowwy 😭'}), 500

def format_prompt(messages):
    """Format messages for Ollama - optimized version"""
    prompt_parts = []
    
    for msg in messages:
        if msg['role'] == 'system':
            prompt_parts.append(f"{msg['content']}\n")
        elif msg['role'] == 'user':
            prompt_parts.append(f"User: {msg['content']}")
        elif msg['role'] == 'assistant':
            prompt_parts.append(f"Rina-chan: {msg['content']}")
    
    # Add final assistant prompt
    prompt_parts.append("Rina-chan: ")
    
    return '\n'.join(prompt_parts)