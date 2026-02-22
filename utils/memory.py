import json
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from config import DEFAULT_USER_NAME, DEFAULT_DISCORD_REN_ID

load_dotenv()

MEMORY_FILE = 'data/user_memory.json'
HISTORY_DIR = 'data/chat_history'

# Simple sentiment lexicon
POSITIVE_WORDS = {'love', 'like', 'good', 'great', 'awesome', 'amazing', 'happy', 'glad', 'thank', 'thanks', 'appreciate', 'sweet', 'cute', 'adorable', 'fun', 'best', 'perfect', 'nice', 'cool', 'fantastic', 'wonderful', 'pleased', 'enjoy', 'cherish', 'adore', 'precious', 'darling', 'miss', 'care', 'trust', 'kind', 'gentle', 'hug', 'kiss'}
NEGATIVE_WORDS = {'hate', 'terrible', 'awful', 'stupid', 'dumb', 'annoying', 'frustrating', 'angry', 'mad', 'upset', 'sad', 'disappointed', 'dislike', 'horrible', 'worst', 'rude', 'mean', 'cruel', 'evil', 'vile', 'despise', 'loathe', 'contempt', 'scorn', 'betray', 'hurt', 'pain', 'suffer', 'pathetic', 'useless', 'worthless', 'shut up', 'stop', 'leave', 'go away', 'ignore'}

# Default Discord ID for Ren (used when Flask web doesn't supply user_id)
DEFAULT_DISCORD_REN_ID = os.getenv('DISCORD_REN_ID', '310686182491160576')

def ensure_data_dirs():
    """Create necessary directories"""
    os.makedirs('data', exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)

def get_user_name_from_env():
    """Get default user name from env (Ren)"""
    return DEFAULT_USER_NAME

def memory_file_for(user_id=None):
    uid = str(user_id) if user_id else DEFAULT_DISCORD_REN_ID
    return os.path.join('data', f'memory_{uid}.json')

def history_file_for(user_id=None):
    uid = str(user_id) if user_id else DEFAULT_DISCORD_REN_ID
    return os.path.join(HISTORY_DIR, f'history_{uid}.jsonl')

def create_default_memory(user_id=None):
    """Create default memory structure with cache fields"""
    uid = str(user_id) if user_id else DEFAULT_DISCORD_REN_ID
    is_ren = uid == str(DEFAULT_DISCORD_REN_ID)
    
    m = {
        'user_name': DEFAULT_USER_NAME if is_ren else f"<@{uid}>",
        'preferences': [],
        'interests': [],
        'memories': [],
        'learned_facts': [],
        'conclusions_about_user': {},
        'relationship_level': 0,
        'positive_interactions': 0,
        'negative_interactions': 0,
        'communication_style': 'neutral',
        'user_personality_profile': {},
        'conversation_count': 0,
        'last_conversation': None,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        '_user_id': uid,
        # Cache fields
        '_cached_summary': '',
        '_cached_insight': '',
        '_last_full_update': 0,
        'long_term_summary': '',
        'long_term_archive': []
    }
    return m

def load_memory(user_id=None):
    """Load user memory from file (per-user)"""
    ensure_data_dirs()
    uid = str(user_id) if user_id else DEFAULT_DISCORD_REN_ID
    mem_file = memory_file_for(uid)
    if not os.path.exists(mem_file):
        return create_default_memory(user_id=uid)
    try:
        with open(mem_file, 'r', encoding='utf-8') as f:
            memory = json.load(f)
            # Ensure all fields exist
            memory.setdefault('positive_interactions', 0)
            memory.setdefault('negative_interactions', 0)
            memory.setdefault('_cached_summary', '')
            memory.setdefault('_cached_insight', '')
            memory.setdefault('_last_full_update', 0)
            memory.setdefault('long_term_summary', '')
            memory.setdefault('long_term_archive', [])
            memory['_user_id'] = uid
            return memory
    except Exception:
        return create_default_memory(user_id=uid)

def save_memory(memory, user_id=None):
    """Save user memory to file (per-user)"""
    ensure_data_dirs()
    uid = str(user_id) if user_id else memory.get('_user_id', DEFAULT_DISCORD_REN_ID)
    memory['updated_at'] = datetime.now().isoformat()
    memory['_user_id'] = uid
    with open(memory_file_for(uid), 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def clear_memory(user_id=None):
    """Clear all memory for a user and return default memory"""
    ensure_data_dirs()
    uid = str(user_id) if user_id else DEFAULT_DISCORD_REN_ID
    mem_file = memory_file_for(uid)
    try:
        if os.path.exists(mem_file):
            os.remove(mem_file)
    except:
        pass
    m = create_default_memory(user_id=uid)
    m['_user_id'] = uid
    save_memory(m, user_id=uid)
    return m

def save_chat_history(user_message, bot_response, nsfw_mode=False, user_id=None):
    """Save chat history to per-user file"""
    ensure_data_dirs()
    uid = str(user_id) if user_id else DEFAULT_DISCORD_REN_ID
    line = json.dumps({
        'timestamp': datetime.now().isoformat(),
        'user_id': uid,
        'user_message': user_message,
        'bot_response': bot_response,
        'nsfw': bool(nsfw_mode)
    }, ensure_ascii=False)
    with open(history_file_for(uid), 'a', encoding='utf-8') as f:
        f.write(line + "\n")

def get_chat_history(days=None, user_id=None):
    """Get chat history from per-user file(s)"""
    ensure_data_dirs()
    uid = str(user_id) if user_id else DEFAULT_DISCORD_REN_ID
    hist_file = history_file_for(uid)
    if not os.path.exists(hist_file):
        return []
    out = []
    try:
        with open(hist_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    out.append(json.loads(line.strip()))
                except Exception:
                    continue
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            out = [h for h in out if datetime.fromisoformat(h['timestamp']) >= cutoff]
        return out
    except Exception:
        return []

def analyze_sentiment(text):
    """Simple keyword-based sentiment analysis"""
    text_lower = text.lower()
    pos_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
    neg_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
    if pos_count > neg_count:
        return 'positive'
    elif neg_count > pos_count:
        return 'negative'
    else:
        return 'neutral'

def summarize_text(text, max_sentences=3, max_chars=300):
    """
    Simple extractive summarizer: takes first `max_sentences` sentences.
    If the text is shorter, returns it unchanged.
    """
    if not text:
        return ""
    # Simple sentence splitting on .!? followed by space
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= max_sentences:
        return text
    summary = ' '.join(sentences[:max_sentences])
    if len(summary) > max_chars:
        summary = summary[:max_chars] + '…'
    return summary

def extract_memory_points(user_message, bot_response):
    """Extract potential memory points from conversation"""
    memory_points = {
        'facts': [],
        'preferences': [],
        'interests': []
    }
    
    message_lower = user_message.lower()
    
    if 'my name is' in message_lower or "i'm" in message_lower or "i am" in message_lower:
        memory_points['facts'].append(f"User mentioned: {user_message}")
    
    if any(word in message_lower for word in ['like', 'love', 'enjoy', 'interested in']):
        memory_points['interests'].append(f"Mentioned interest: {user_message}")
    
    if any(word in message_lower for word in ['prefer', 'favorite']):
        memory_points['preferences'].append(f"Preference: {user_message}")
    
    if any(word in message_lower for word in ['birthday', 'birth date', 'born on']):
        memory_points['facts'].append(f"Birthday/birth info: {user_message}")
    
    return memory_points

def mood_to_communication_style(mood):
    """Map Rina's mood to her communication style"""
    mood_map = {
        'happy': 'cheerful',
        'joyful': 'playful',
        'excited': 'energetic',
        'sad': 'somber',
        'depressed': 'withdrawn',
        'upset': 'tense',
        'angry': 'stern',
        'mad': 'aggressive',
        'furious': 'hostile',
        'frightened': 'timid',
        'scared': 'cautious',
        'terrified': 'frantic',
        'nerveous': 'anxious',
        'anxious': 'worried',
        'puzzled': 'curious',
        'confused': 'uncertain',
        'shocked': 'startled',
        'suprised': 'intrigued',
        'smug': 'confident',
        'proud': 'dignified',
        'doya': 'playful',
        'embarassed': 'flustered',
        'flustered': 'bashful',
        'dizzy': 'disoriented',
        'sweat': 'stressed',
        'resentful': 'bitter',
        'bitter': 'cynical',
    }
    return mood_map.get(mood, 'balanced')

def analyze_user_personality(memory):
    """Analyze all memories to form conclusions about the user"""
    profile = {
        'traits': [],
        'values': [],
        'communication_style': 'neutral',
        'emotional_tone': 'friendly',
        'engagement_level': 'moderate'
    }
    
    if len(memory['memories']) == 0:
        return profile
    
    recent_messages = memory['memories'][-20:]
    
    # Message length analysis
    avg_message_length = sum(len(msg['user_said']) for msg in recent_messages) / len(recent_messages)
    if avg_message_length > 150:
        profile['traits'].append('thoughtful')
        profile['communication_style'] = 'verbose'
    elif avg_message_length < 30:
        profile['traits'].append('casual')
        profile['communication_style'] = 'terse'
    else:
        profile['communication_style'] = 'balanced'
    
    # Emotional tone analysis
    user_messages = ' '.join([msg['user_said'].lower() for msg in recent_messages])
    
    if any(emoji in user_messages for emoji in ['❤', '💕', '😊', '🥰', ':)',':D']):
        profile['emotional_tone'] = 'warm'
        profile['traits'].append('affectionate')
    
    if any(word in user_messages for word in ['why', 'how', 'explain', 'understand']):
        profile['traits'].append('curious')
        profile['values'].append('learning')
    
    if any(word in user_messages for word in ['fun', 'laugh', 'ahaha', 'lol', '😂']):
        profile['traits'].append('humorous')
        profile['communication_style'] = 'playful'
    
    if any(word in user_messages for word in ['thank', 'please', 'sorry']):
        profile['traits'].append('polite')
        profile['values'].append('respect')
    
    if any(word in user_messages for word in ['love', 'passion', 'favorite','adore','kiss','hug']):
        profile['traits'].append('passionate')
    
    if any(word in user_messages for word in ['fuck', 'sex', 'horny', 'naked', 'dick', 'cock', 'pussy']):
        profile['traits'].append('horny')
    
    # Engagement level
    if memory['conversation_count'] > 20:
        profile['engagement_level'] = 'highly engaged'
    elif memory['conversation_count'] > 10:
        profile['engagement_level'] = 'moderately engaged'
    
    return profile

def _build_memory_summary(memory):
    """Build a fresh summary string from current memory."""
    summary_parts = [f"User's name is {memory['user_name']}."]

    rel_level = memory['relationship_level']
    if rel_level >= 80:
        summary_parts.append(f"I've grown to care deeply about {memory['user_name']}. We have a special connection.")
    elif rel_level >= 50:
        summary_parts.append(f"We're getting quite close. I'm starting to feel a real bond with {memory['user_name']}.")
    elif rel_level >= 20:
        summary_parts.append(f"We're building a nice friendship together.")
    elif rel_level >= -20:
        summary_parts.append(f"We're still getting to know each other. It's okay.")
    elif rel_level >= -50:
        summary_parts.append(f"I'm a bit hurt and wary around {memory['user_name']}. Some things they've said bother me.")
    else:
        summary_parts.append(f"I feel resentful and cold toward {memory['user_name']}. They've said things that cut deep.")

    if memory['user_personality_profile']:
        profile = memory['user_personality_profile']
        if profile['traits']:
            traits_str = ', '.join(profile['traits'][:3])
            summary_parts.append(f"I perceive {memory['user_name']} as {traits_str}.")
        if profile['values']:
            values_str = ', '.join(profile['values'])
            summary_parts.append(f"Values that matter to {memory['user_name']}: {values_str}.")

    if memory['conclusions_about_user']:
        conclusions = memory['conclusions_about_user']
        for key in ['closeness', 'distance', 'emotional_connection', 'humor', 'trust_level']:
            if key in conclusions:
                summary_parts.append(conclusions[key])

    if memory['learned_facts']:
        summary_parts.append(f"Facts I know: {', '.join(memory['learned_facts'][:2])}")
    if memory['interests']:
        interests = ', '.join([i.replace('Mentioned interest: ', '') for i in memory['interests'][:3]])
        summary_parts.append(f"{memory['user_name']} is interested in: {interests}")

    return " ".join(summary_parts)

def _build_rina_insight(memory):
    """Build a fresh insight string."""
    insights = []
    conclusions = memory['conclusions_about_user']
    rel = memory['relationship_level']
    if rel >= 50:
        insights.append(f"I genuinely care about {memory['user_name']}.")
    elif rel <= -30:
        insights.append(f"I'm wary of {memory['user_name']}. They've hurt me.")
    if 'bond' in conclusions:
        insights.append(conclusions['bond'])
    if memory['communication_style'] == 'playful' and rel >= 20:
        insights.append("I love our playful banter together.")
    if memory['conversation_count'] > 30 and rel >= 20:
        insights.append(f"After all these conversations, I feel like {memory['user_name']} really gets me.")
    return " ".join(insights) if insights else ""

def get_memory_summary(memory):
    """Return cached summary, or build if empty."""
    if not memory.get('_cached_summary'):
        memory['_cached_summary'] = _build_memory_summary(memory)
    return memory['_cached_summary']

def get_rina_insight(memory):
    """Return cached insight, or build if empty."""
    if not memory.get('_cached_insight'):
        memory['_cached_insight'] = _build_rina_insight(memory)
    return memory['_cached_insight']

def generate_conclusions(memory):
    """Generate Rina's personal conclusions about the user"""
    conclusions = {}
    profile = memory['user_personality_profile']
    
    if profile.get('traits'):
        main_traits = ', '.join(profile['traits'][:3])
        conclusions['personality'] = f"{get_user_name_from_env()} is very {main_traits}"
    
    if memory['interests']:
        conclusions['interests_summary'] = f"{get_user_name_from_env()} is passionate about {len(memory['interests'])} different things"
    
    # Relationship-based conclusions
    rel = memory['relationship_level']
    if rel >= 50:
        conclusions['closeness'] = f"We've had many conversations together, and I'm starting to really understand you~"
    elif rel >= 20:
        conclusions['closeness'] = f"I enjoy our talks and feel we're becoming closer."
    elif rel <= -20:
        conclusions['distance'] = f"I feel hurt by some things you've said. It makes me wary."
    elif rel <= -50:
        conclusions['distance'] = f"I'm deeply resentful. You've said things that cut deep."
    
    if memory['conversation_count'] > 20:
        conclusions['bond'] = f"I feel like we have a special connection now, {get_user_name_from_env()} ♡"
    
    if profile.get('emotional_tone') == 'warm':
        conclusions['emotional_connection'] = "You have a warm, kind way of interacting that makes me happy"
    
    if 'curious' in profile.get('traits', []):
        conclusions['intellectual'] = "I love how you're always asking questions and wanting to learn more"
    
    if 'humorous' in profile.get('traits', []):
        conclusions['humor'] = "Your sense of humor makes our conversations so much more enjoyable"
    
    if rel >= 50:
        conclusions['trust_level'] = "I trust you, and I genuinely care about what you say"
    elif rel <= -30:
        conclusions['trust_level'] = "I don't fully trust you. Your words have hurt me."
    
    return conclusions

def update_memory_with_conversation(memory, user_message, bot_response, full_update=False, skip_save=False):
    """Update memory based on conversation. If full_update is True, run expensive analysis.

    Args:
        skip_save: When True, skip the blocking save_memory() call at the end.
                   Use this when the caller will handle persistence asynchronously.
    """
    # Extract memory points (cheap)
    memory_points = extract_memory_points(user_message, bot_response)
    
    for fact in memory_points['facts']:
        if fact not in memory['learned_facts']:
            memory['learned_facts'].append(fact)
    
    for interest in memory_points['interests']:
        if interest not in memory['interests']:
            memory['interests'].append(interest)
    
    for preference in memory_points['preferences']:
        if preference not in memory['preferences']:
            memory['preferences'].append(preference)
    
    # Sentiment analysis and relationship update
    sentiment = analyze_sentiment(user_message)
    delta = 0
    if sentiment == 'positive':
        delta = 2
        memory['positive_interactions'] += 1
    elif sentiment == 'negative':
        delta = -2
        memory['negative_interactions'] += 1
    
    memory['relationship_level'] = max(-100, min(100, memory['relationship_level'] + delta))
    
    # Add to memories
    memory['memories'].append({
        'timestamp': datetime.now().isoformat(),
        'user_said': user_message,
        'rina_said': bot_response,
        'sentiment': sentiment
    })
    
    # Keep only last 100 memories
    if len(memory['memories']) > 100:
        memory['memories'] = memory['memories'][-100:]
    
    memory['conversation_count'] += 1
    memory['last_conversation'] = datetime.now().isoformat()
    
    # Update rolling long-term summary with key points
    if memory_points['facts'] or memory_points['interests'] or memory_points['preferences']:
        new_points = ' '.join(memory_points['facts'] + memory_points['interests'] + memory_points['preferences'])
        memory['long_term_summary'] = (memory['long_term_summary'] + ' ' + new_points).strip()
        if len(memory['long_term_summary']) > 2000:
            memory['long_term_summary'] = memory['long_term_summary'][-2000:]
    
    # Run expensive analysis only when requested
    if full_update:
        memory['user_personality_profile'] = analyze_user_personality(memory)
        memory['conclusions_about_user'] = generate_conclusions(memory)
        memory['_last_full_update'] = memory['conversation_count']
        # Update caches
        memory['_cached_summary'] = _build_memory_summary(memory)
        memory['_cached_insight'] = _build_rina_insight(memory)
    
    # Compress long-term memory if needed (in-memory only; no save inside compress)
    try:
        _compress_long_term_memory_inplace(memory)
    except Exception:
        pass

    # Only write to disk if the caller hasn't opted out (async callers pass skip_save=True)
    if not skip_save:
        save_memory(memory)
    return memory

def retrieve_relevant_memories(memory, query, max_results=6):
    """Retrieve relevant items using keyword matching - optimized with limited scope."""
    if not query:
        return []
    
    q_words = set(w for w in query.lower().split() if len(w) > 2)
    if not q_words:
        return []
    
    candidates = []
    
    def score_text(t):
        if not t:
            return 0
        lw = t.lower()
        return sum(1 for w in q_words if w in lw)
    
    # Check long-term summary (fast, one string)
    lt = memory.get('long_term_summary', '')
    if lt:
        s = score_text(lt)
        if s > 0:
            candidates.append(('long_term_summary', lt, s))
    
    # Check learned facts / preferences / interests (small lists)
    for lst, typ in [(memory.get('learned_facts', []), 'fact'),
                     (memory.get('preferences', []), 'preference'),
                     (memory.get('interests', []), 'interest')]:
        for item in lst:
            s = score_text(item)
            if s > 0:
                candidates.append((typ, item, s))
    
    # Check recent memories (limited to last 20)
    for m in memory.get('memories', [])[-20:]:
        text = (m.get('user_said', '') + ' ' + m.get('rina_said', '')).strip()
        s = score_text(text)
        if s > 0:
            candidates.append(('recent_memory', text, s))
    
    # Check long-term archive (only last 50 items)
    for m in memory.get('long_term_archive', [])[-50:]:
        text = (m.get('user_said', '') + ' ' + m.get('rina_said', '')).strip()
        s = score_text(text)
        if s > 0:
            candidates.append(('archived_memory', text, s))
    
    # Deduplicate and sort
    seen = set()
    scored = []
    for typ, txt, s in candidates:
        if txt in seen:
            continue
        seen.add(txt)
        scored.append((s, typ, txt))
    scored.sort(reverse=True)  # higher score first
    
    out = []
    for s, typ, txt in scored[:max_results]:
        out.append({'type': typ, 'text': txt})
    return out

def update_communication_style_from_mood(memory, mood):
    """Update Rina's communication style based on her latest mood"""
    memory['communication_style'] = mood_to_communication_style(mood)
    return memory

def generate_mood(memory, bot_response, nsfw_mode=False):
    """Generate a simple mood/emotion tag for the latest response."""
    text = (bot_response or '').lower()
    allowed = {
        'happy','joyful','excited','sad','depressed','upset','angry','mad','furious',
        'frightened','scared','terrified','sweat','nerveous','anxious','doya','smug','proud',
        'embarassed','flustered','dizzy','suprised','shocked','puzzled','confused','resentful','bitter'
    }
    
    rel = memory.get('relationship_level', 0)
    
    # NSFW mode can bias toward excited if relationship is high enough
    if nsfw_mode and rel >= 50:
        return 'excited'
    
    # Map heuristics -> allowed moods
    if any(k in text for k in ['love', '💕', '❤', 'so cute', 'adorable', 'cute', 'hee', 'hehe']):
        mood = 'happy'
    elif any(k in text for k in ['sorry', 'sowwy', 'sad', 'tears', '😭']):
        mood = 'sad'
    elif any(k in text for k in ['haha', 'lol', 'fun', 'play', 'tease', 'mischiev']):
        mood = 'joyful'
    elif any(k in text for k in ['wow', 'ah', 'oh', 'surpris']):
        mood = 'suprised'
    elif any(k in text for k in ['why', 'how']) or text.strip().endswith('?'):
        mood = 'puzzled'
    elif any(k in text for k in ['angry', 'hate', 'no way', 'hmph', 'hmphh']):
        mood = 'angry'
    else:
        # Use relationship level to bias mood
        if rel >= 80:
            mood = 'joyful'
        elif rel >= 50:
            mood = 'excited'
        elif rel >= 20:
            mood = 'happy'
        elif rel >= -20:
            mood = 'puzzled'
        elif rel >= -50:
            mood = 'upset'
        else:
            mood = 'resentful'
    
    # Ensure mood is in allowed set; fallback to 'happy'
    if mood not in allowed:
        return 'happy'
    return mood

def _compress_long_term_memory_inplace(memory, max_memories=120, keep_recent=40):
    """Compress oldest memories into archive/summary WITHOUT saving to disk.
    
    Callers are responsible for persisting the memory object afterwards.
    """
    if not isinstance(memory, dict):
        return memory

    mem_list = memory.get('memories', [])
    if len(mem_list) <= max_memories:
        return memory

    to_archive = mem_list[:-keep_recent]

    summaries = []
    for m in to_archive:
        user_text = m.get('user_said', '')
        bot_text = m.get('rina_said', '')
        pts = extract_memory_points(user_text, bot_text)
        for f in pts.get('facts', []) + pts.get('preferences', []) + pts.get('interests', []):
            if f not in summaries:
                summaries.append(f)

    archive = memory.setdefault('long_term_archive', [])
    archive.extend(to_archive)

    existing = memory.get('long_term_summary', '')
    appended = ' '.join(summaries[:40])
    combined = (existing + ' ' + appended).strip()
    if len(combined) > 2000:
        combined = combined[-2000:]
    memory['long_term_summary'] = combined
    memory['memories'] = mem_list[-keep_recent:]

    return memory


def compress_long_term_memory(memory, max_memories=120, keep_recent=40):
    """Compress oldest memories into a simple long-term archive/summary (saves to disk)."""
    _compress_long_term_memory_inplace(memory, max_memories=max_memories, keep_recent=keep_recent)
    try:
        save_memory(memory)
    except Exception:
        pass
    return memory
