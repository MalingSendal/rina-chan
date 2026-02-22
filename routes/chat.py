from flask import Blueprint, request, jsonify, send_from_directory, current_app
import requests
import os
import threading
from utils.memory import (load_memory, update_memory_with_conversation,
                          get_memory_summary, get_rina_insight, save_chat_history,
                          generate_mood, retrieve_relevant_memories,
                          update_communication_style_from_mood, summarize_text)
from config import DEFAULT_DISCORD_REN_ID, DEFAULT_USER_NAME

chat_bp = Blueprint('chat', __name__)

# ── In-memory session history (last 5 exchanges = 10 messages) ──────────────
chat_history = []
_chat_history_lock = threading.Lock()

# ── Persistent HTTP session for Ollama (connection pooling) ──────────────────
_ollama_session = requests.Session()
_ollama_session.headers.update({'Content-Type': 'application/json'})

# ── In-process memory cache  {uid: memory_dict} ─────────────────────────────
_memory_cache: dict = {}
_memory_cache_lock = threading.Lock()

# Allowed moods for validation
ALLOWED_MOODS = {
    'happy', 'joyful', 'excited', 'sad', 'depressed', 'upset', 'angry', 'mad', 'furious',
    'frightened', 'scared', 'terrified', 'sweat', 'nerveous', 'anxious', 'doya', 'smug', 'proud',
    'embarassed', 'flustered', 'dizzy', 'suprised', 'shocked', 'puzzled', 'confused', 'resentful', 'bitter'
}

# How often to perform a full memory analysis (personality, conclusions)
FULL_UPDATE_INTERVAL = 5


def _get_ollama_base():
    """Return the Ollama base URL from the current app config (no app re-creation)."""
    cfg = current_app.config
    return f'http://{cfg["OLLAMA_IP"]}:{cfg["OLLAMA_PORT"]}'


def _load_memory_cached(user_id):
    """Load memory with an in-process cache to avoid repeated file reads."""
    uid = str(user_id) if user_id else str(DEFAULT_DISCORD_REN_ID)
    with _memory_cache_lock:
        if uid in _memory_cache:
            return _memory_cache[uid]
    memory = load_memory(user_id=uid)
    with _memory_cache_lock:
        _memory_cache[uid] = memory
    return memory


def _invalidate_memory_cache(user_id):
    uid = str(user_id) if user_id else str(DEFAULT_DISCORD_REN_ID)
    with _memory_cache_lock:
        _memory_cache.pop(uid, None)


def _save_memory_async(memory, user_id):
    """Persist memory to disk in a background thread so the response isn't blocked."""
    from utils.memory import save_memory
    def _do_save():
        try:
            save_memory(memory.copy(), user_id=user_id)
        except Exception as e:
            print(f'[memory] background save error: {e}')
    threading.Thread(target=_do_save, daemon=True).start()


def _save_history_async(user_message, response_text, nsfw_mode, user_id):
    """Persist chat history to disk in a background thread."""
    def _do_save():
        try:
            save_chat_history(user_message, response_text, nsfw_mode, user_id=user_id)
        except Exception as e:
            print(f'[history] background save error: {e}')
    threading.Thread(target=_do_save, daemon=True).start()


@chat_bp.route('/')
def index():
    """Serve the main index.html"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return send_from_directory(base_dir, 'index.html')


@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests with memory integration and optimizations."""
    from config import SYSTEM_PROMPT, SYSTEM_PROMPT_NSFW

    data = request.get_json() or {}
    user_message = data.get('message', '')
    nsfw_mode = data.get('nsfw_mode', False)
    user_id = data.get('user_id', None)
    user_reference = data.get('user_reference', None)

    if not user_message:
        return jsonify({'response': 'Say something! -pouts-'}), 400

    try:
        # 1. Load memory (in-process cache → file only on first access)
        memory = _load_memory_cached(user_id)
        uid_str = str(user_id) if user_id else str(DEFAULT_DISCORD_REN_ID)
        is_ren = uid_str == str(DEFAULT_DISCORD_REN_ID)

        if is_ren:
            memory['user_name'] = DEFAULT_USER_NAME
        elif user_reference:
            memory['user_name'] = user_reference

        # 2. Optionally summarize long user messages (first 3 sentences only)
        prompt_message = summarize_text(user_message, max_sentences=3, max_chars=500)
        if prompt_message != user_message:
            prompt_message += ' [summarized]'

        # 3. Build memory context (uses cached strings)
        memory_summary = get_memory_summary(memory)
        rina_insight = get_rina_insight(memory)
        relevant_items = retrieve_relevant_memories(memory, prompt_message, max_results=4)

        relevant_text = ''
        if relevant_items:
            relevant_text = '\n'.join(f"[{it['type']}]: {it['text']}" for it in relevant_items)

        # 4. Build system prompt
        system_prompt = SYSTEM_PROMPT_NSFW if nsfw_mode else SYSTEM_PROMPT
        system_prompt_with_memory = (
            f"{system_prompt}\n\n"
            f"=== YOUR KNOWLEDGE OF USER ===\n{memory_summary}\n\n"
            f"=== YOUR PERSONAL FEELINGS ===\n{rina_insight}\n"
        )
        if relevant_text:
            system_prompt_with_memory += f"\n=== RELEVANT PAST MEMORIES ===\n{relevant_text}\n"
        system_prompt_with_memory += f"\n[In your responses, refer to the user as: {memory['user_name']}]\n"

        # 5. Prepare messages for /api/chat (native multi-turn format)
        messages = [{'role': 'system', 'content': system_prompt_with_memory}]
        with _chat_history_lock:
            session_context = list(chat_history[-10:])
        messages.extend(session_context)
        messages.append({'role': 'user', 'content': prompt_message})

        # 6. Call Ollama via /api/chat with a persistent session (connection reuse)
        cfg = current_app.config
        ollama_chat_url = f'http://{cfg["OLLAMA_IP"]}:{cfg["OLLAMA_PORT"]}/api/chat'

        ollama_payload = {
            'model': cfg['OLLAMA_MODEL'],
            'messages': messages,
            'stream': False,
            'options': {
                'temperature': 0.7,
                'num_predict': 100,          # hard cap on generated tokens
                'num_ctx': int(cfg.get('OLLAMA_NUM_CTX') or 2048),
                'stop': ['\nUser:', '\nRina-chan:'],  # prevent run-on generation
            }
        }

        response = _ollama_session.post(ollama_chat_url, json=ollama_payload, timeout=120)

        if response.status_code != 200:
            return jsonify({'response': '*sighs* The connection broke... try again? 💔'}), 500

        response_text = (
            response.json()
            .get('message', {})
            .get('content', 'Hmm? Did you say something?')
            .strip()
        )

        # 7. Decide whether to run expensive full memory analysis
        conv_count = memory.get('conversation_count', 0)
        full_update = (conv_count < 5) or (conv_count % FULL_UPDATE_INTERVAL == 0)

        # 8. Update in-memory object (cheap, synchronous) — skip_save=True because
        #    we persist asynchronously below, avoiding a blocking file write on the
        #    hot path.
        update_memory_with_conversation(
            memory, user_message, response_text,
            full_update=full_update, skip_save=True
        )

        # 9. Persist memory & history asynchronously (does NOT block the response)
        _save_memory_async(memory, user_id)
        _save_history_async(user_message, response_text, nsfw_mode, user_id)

        # 10. Generate mood (lightweight keyword check)
        mood = generate_mood(memory, response_text, nsfw_mode)
        if mood not in ALLOWED_MOODS:
            mood = 'happy'
        update_communication_style_from_mood(memory, mood)

        # 11. Update session chat history (thread-safe)
        with _chat_history_lock:
            chat_history.append({'role': 'user', 'content': user_message})
            chat_history.append({'role': 'assistant', 'content': response_text})
            if len(chat_history) > 10:
                del chat_history[:2]

        return jsonify({
            'response': response_text,
            'mood': mood,
            'summarized': prompt_message != user_message
        })

    except requests.exceptions.ConnectionError:
        cfg = current_app.config
        return jsonify({
            'response': (
                f'Hmph... I can\'t reach my brain right now. '
                f'Make sure Ollama is running at {cfg["OLLAMA_IP"]}:{cfg["OLLAMA_PORT"]} 💢'
            )
        }), 500
    except requests.exceptions.Timeout:
        return jsonify({'response': 'This is taking too long... try a simpler question? 😤'}), 500
    except Exception as e:
        print(f'Error in chat endpoint: {e}')
        return jsonify({'response': 'Something went wrong... sowwy 😭'}), 500
