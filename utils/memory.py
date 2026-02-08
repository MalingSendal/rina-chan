import json
import os
from datetime import datetime

MEMORY_FILE = 'data/user_memory.json'
HISTORY_DIR = 'data/chat_history'

def ensure_data_dirs():
    """Create necessary directories"""
    os.makedirs('data', exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)

def load_memory():
    """Load user memory from file"""
    ensure_data_dirs()
    
    if not os.path.exists(MEMORY_FILE):
        return create_default_memory()
    
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return create_default_memory()

def create_default_memory():
    """Create default memory structure"""
    return {
        'user_name': 'Ren',
        'personality_traits': [],
        'preferences': [],
        'interests': [],
        'relationship_history': [],
        'important_dates': [],
        'memories': [],
        'learned_facts': [],
        'conclusions_about_user': {},
        'relationship_level': 0,  # 0-100 scale
        'communication_style': 'neutral',  # How Rina perceives user's style
        'user_personality_profile': {},  # Rina's conclusions about user personality
        'conversation_count': 0,
        'last_conversation': None,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }

def save_memory(memory):
    """Save user memory to file"""
    ensure_data_dirs()
    memory['updated_at'] = datetime.now().isoformat()
    
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def extract_memory_points(user_message, bot_response):
    """Extract potential memory points from conversation
    
    This looks for patterns like:
    - "My name is..."
    - "I like..." / "I love..."
    - "I'm interested in..."
    - "I prefer..."
    - Date-related messages
    """
    memory_points = {
        'facts': [],
        'preferences': [],
        'interests': []
    }
    
    message_lower = user_message.lower()
    
    # Extract name mentions
    if 'my name is' in message_lower or "i'm" in message_lower or "i am" in message_lower:
        memory_points['facts'].append(f"User mentioned: {user_message}")
    
    # Extract likes/interests
    if any(word in message_lower for word in ['like', 'love', 'enjoy', 'interested in']):
        memory_points['interests'].append(f"Mentioned interest: {user_message}")
    
    # Extract preferences
    if any(word in message_lower for word in ['prefer', 'favorite', 'prefer']):
        memory_points['preferences'].append(f"Preference: {user_message}")
    
    # Extract birthdate mentions
    if any(word in message_lower for word in ['birthday', 'birth date', 'born on']):
        memory_points['facts'].append(f"Birthday/birth info: {user_message}")
    
    return memory_points

def analyze_user_personality(memory):
    """Analyze all memories to form conclusions about the user
    
    Returns a personality profile with Rina's conclusions
    """
    profile = {
        'traits': [],
        'values': [],
        'communication_style': 'neutral',
        'emotional_tone': 'friendly',
        'engagement_level': 'moderate'
    }
    
    if len(memory['memories']) == 0:
        return profile
    
    # Analyze conversation patterns
    recent_messages = memory['memories'][-20:]  # Last 20 messages
    
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
    
    if any(emoji in user_messages for emoji in ['❤', '💕', '😊', '🥰', ':)']):
        profile['emotional_tone'] = 'warm'
        profile['traits'].append('affectionate')
    
    if any(word in user_messages for word in ['why', 'how', 'explain', 'understand']):
        profile['traits'].append('curious')
        profile['values'].append('learning')
    
    if any(word in user_messages for word in ['fun', 'laugh', 'haha', 'lol', '😂']):
        profile['traits'].append('humorous')
        profile['communication_style'] = 'playful'
    
    if any(word in user_messages for word in ['thank', 'please', 'sorry']):
        profile['traits'].append('polite')
        profile['values'].append('respect')
    
    if any(word in user_messages for word in ['love', 'passion', 'favorite']):
        profile['traits'].append('passionate')
    
    # Engagement level
    if memory['conversation_count'] > 20:
        profile['engagement_level'] = 'highly engaged'
    elif memory['conversation_count'] > 10:
        profile['engagement_level'] = 'moderately engaged'
    
    return profile

def update_relationship_level(memory):
    """Update relationship intimacy level based on interaction count"""
    # Scale from 0 to 100
    # 0-5 conversations: acquaintance (0-20)
    # 5-15 conversations: friend (20-50)
    # 15-30 conversations: close friend (50-80)
    # 30+ conversations: intimate (80-100)
    
    conv_count = memory['conversation_count']
    
    if conv_count < 5:
        level = (conv_count / 5) * 20
    elif conv_count < 15:
        level = 20 + ((conv_count - 5) / 10) * 30
    elif conv_count < 30:
        level = 50 + ((conv_count - 15) / 15) * 30
    else:
        level = min(80 + ((conv_count - 30) / 30) * 20, 100)
    
    memory['relationship_level'] = int(level)
    
    return memory

def update_memory_with_conversation(memory, user_message, bot_response):
    """Update memory based on conversation"""
    memory_points = extract_memory_points(user_message, bot_response)
    
    # Add discovered facts
    for fact in memory_points['facts']:
        if fact not in memory['learned_facts']:
            memory['learned_facts'].append(fact)
    
    # Add interests
    for interest in memory_points['interests']:
        if interest not in memory['interests']:
            memory['interests'].append(interest)
    
    # Add preferences
    for preference in memory_points['preferences']:
        if preference not in memory['preferences']:
            memory['preferences'].append(preference)
    
    # Add to memories
    memory['memories'].append({
        'timestamp': datetime.now().isoformat(),
        'user_said': user_message,
        'rina_said': bot_response
    })
    
    # Keep only last 100 memories to avoid huge file
    if len(memory['memories']) > 100:
        memory['memories'] = memory['memories'][-100:]
    
    memory['conversation_count'] += 1
    memory['last_conversation'] = datetime.now().isoformat()
    
    # Analyze personality and update profile
    memory['user_personality_profile'] = analyze_user_personality(memory)
    
    # Update relationship level
    memory = update_relationship_level(memory)
    
    # Generate conclusions based on patterns
    memory['conclusions_about_user'] = generate_conclusions(memory)
    
    save_memory(memory)
    return memory

def generate_conclusions(memory):
    """Generate Rina's personal conclusions about the user"""
    conclusions = {}
    profile = memory['user_personality_profile']
    
    if profile['traits']:
        main_traits = ', '.join(profile['traits'][:3])
        conclusions['personality'] = f"Ren is very {main_traits}"
    
    if memory['interests']:
        if len(memory['interests']) > 0:
            conclusions['interests_summary'] = f"Ren is passionate about {len(memory['interests'])} different things"
    
    if memory['conversation_count'] > 10:
        conclusions['closeness'] = f"We've had many conversations together, and I'm starting to really understand you~"
    
    if memory['conversation_count'] > 20:
        conclusions['bond'] = f"I feel like we have a special connection now, Ren ♡"
    
    if profile['emotional_tone'] == 'warm':
        conclusions['emotional_connection'] = "You have a warm, kind way of interacting that makes me happy"
    
    if 'curious' in profile['traits']:
        conclusions['intellectual'] = "I love how you're always asking questions and wanting to learn more"
    
    if 'humorous' in profile['traits']:
        conclusions['humor'] = "Your sense of humor makes our conversations so much more enjoyable"
    
    if memory['relationship_level'] >= 50:
        conclusions['trust_level'] = "I trust you, and I genuinely care about what you say"
    
    return conclusions

def get_memory_summary(memory):
    """Create a summary of memories for the system prompt"""
    summary_parts = [f"User's name is {memory['user_name']}."]
    
    # Add relationship context
    rel_level = memory['relationship_level']
    if rel_level < 20:
        summary_parts.append(f"This is our early time getting to know each other.")
    elif rel_level < 50:
        summary_parts.append(f"We're building a nice friendship together.")
    elif rel_level < 80:
        summary_parts.append(f"We're getting quite close. I'm starting to feel a real bond with {memory['user_name']}.")
    else:
        summary_parts.append(f"I've grown to care deeply about {memory['user_name']}. We have a special connection.")
    
    # Add personality insights
    if memory['user_personality_profile']:
        profile = memory['user_personality_profile']
        if profile['traits']:
            traits_str = ', '.join(profile['traits'][:3])
            summary_parts.append(f"I perceive {memory['user_name']} as {traits_str}.")
        
        if profile['values']:
            values_str = ', '.join(profile['values'])
            summary_parts.append(f"Values that matter to {memory['user_name']}: {values_str}.")
    
    # Add learned conclusions
    if memory['conclusions_about_user']:
        conclusions = memory['conclusions_about_user']
        if 'closeness' in conclusions:
            summary_parts.append(conclusions['closeness'])
        if 'emotional_connection' in conclusions:
            summary_parts.append(conclusions['emotional_connection'])
        if 'humor' in conclusions:
            summary_parts.append(conclusions['humor'])
    
    # Add specific facts
    if memory['learned_facts']:
        summary_parts.append(f"Facts I know: {', '.join(memory['learned_facts'][:2])}")
    
    if memory['interests']:
        interests = ', '.join([i.replace('Mentioned interest: ', '') for i in memory['interests'][:3]])
        summary_parts.append(f"{memory['user_name']} is interested in: {interests}")
    
    return " ".join(summary_parts)

def get_rina_insight(memory):
    """Get Rina's personal inner thoughts about the user for her personality"""
    insights = []
    
    conclusions = memory['conclusions_about_user']
    
    if memory['relationship_level'] >= 50:
        insights.append(f"I genuinely care about {memory['user_name']}.")
    
    if 'bond' in conclusions:
        insights.append(conclusions['bond'])
    
    if memory['communication_style'] == 'playful':
        insights.append("I love our playful banter together.")
    
    if memory['conversation_count'] > 30:
        insights.append(f"After all these conversations, I feel like {memory['user_name']} really gets me.")
    
    return " ".join(insights) if insights else ""

def generate_mood(memory, bot_response, nsfw_mode=False):
    """Generate a simple mood/emotion tag for the latest response.
    Returns one of the allowed mood tags (whitelisted).
    Allowed moods: happy,joyful,excited,sad,depressed,upset,angry,mad,furious,
    frightened,scared,terrified,sweat,nerveous,anxious,doya,smug,proud,
    embarassed,flustered,dizzy,suprised,shocked,puzzled,confused
    """
    text = (bot_response or '').lower()
    # Whitelist of allowed moods
    allowed = {
        'happy','joyful','excited','sad','depressed','upset','angry','mad','furious',
        'frightened','scared','terrified','sweat','nerveous','anxious','doya','smug','proud',
        'embarassed','flustered','dizzy','suprised','shocked','puzzled','confused'
    }

    # NSFW preference can bias toward an allowed excited mood when appropriate
    if nsfw_mode and memory.get('relationship_level', 0) >= 50:
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
        # Use relationship level to bias mood into allowed list
        rl = memory.get('relationship_level', 0)
        if rl >= 80:
            mood = 'joyful'
        elif rl >= 50:
            mood = 'excited'
        else:
            mood = 'happy'

    # Safety: ensure returned mood is in allowed list; fallback to 'happy'
    if mood not in allowed:
        return 'happy'
    return mood

def save_chat_history(user_message, bot_response, nsfw_mode=False):
    """Save chat history to file"""
    ensure_data_dirs()
    
    today = datetime.now().strftime('%Y-%m-%d')
    history_file = os.path.join(HISTORY_DIR, f'chat_{today}.json')
    
    chat_entry = {
        'timestamp': datetime.now().isoformat(),
        'user': user_message,
        'bot': bot_response,
        'nsfw_mode': nsfw_mode
    }
    
    # Load existing history for today
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
    
    history.append(chat_entry)
    
    # Save updated history
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_chat_history(days=None):
    """Get chat history from file(s)
    
    Args:
        days: Number of days back to retrieve (None = all)
    """
    ensure_data_dirs()
    
    all_chats = []
    
    if not os.path.exists(HISTORY_DIR):
        return all_chats
    
    for filename in sorted(os.listdir(HISTORY_DIR), reverse=True):
        if filename.startswith('chat_') and filename.endswith('.json'):
            filepath = os.path.join(HISTORY_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    chats = json.load(f)
                    all_chats.extend(chats)
            except:
                continue
    
    return all_chats

def clear_memory():
    """Reset all memories (admin function)"""
    ensure_data_dirs()
    memory = create_default_memory()
    save_memory(memory)
    return memory
