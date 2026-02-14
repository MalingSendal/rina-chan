import json
import os
from datetime import datetime

MEMORY_FILE = 'data/user_memory.json'
HISTORY_DIR = 'data/chat_history'

# Simple sentiment lexicon
POSITIVE_WORDS = {'love', 'like', 'good', 'great', 'awesome', 'amazing', 'happy', 'glad', 'thank', 'thanks', 'appreciate', 'sweet', 'cute', 'adorable', 'fun', 'best', 'perfect', 'nice', 'cool', 'fantastic', 'wonderful', 'pleased', 'enjoy', 'cherish', 'adore', 'precious', 'darling', 'miss', 'care', 'trust', 'kind', 'gentle', 'hug', 'kiss'}
NEGATIVE_WORDS = {'hate', 'bad', 'terrible', 'awful', 'stupid', 'dumb', 'annoying', 'frustrating', 'angry', 'mad', 'upset', 'sad', 'disappointed', 'dislike', 'horrible', 'worst', 'rude', 'mean', 'cruel', 'evil', 'vile', 'despise', 'loathe', 'contempt', 'scorn', 'betray', 'hurt', 'pain', 'suffer', 'pathetic', 'useless', 'worthless', 'shut up', 'stop', 'leave', 'go away', 'ignore'}

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
            memory = json.load(f)
            # Ensure new fields exist for older memory files
            if 'positive_interactions' not in memory:
                memory['positive_interactions'] = 0
            if 'negative_interactions' not in memory:
                memory['negative_interactions'] = 0
            return memory
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
        'relationship_level': 0,          # -100 to 100
        'positive_interactions': 0,
        'negative_interactions': 0,
        'communication_style': 'neutral',
        'user_personality_profile': {},
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
    
    if any(word in message_lower for word in ['prefer', 'favorite', 'prefer']):
        memory_points['preferences'].append(f"Preference: {user_message}")
    
    if any(word in message_lower for word in ['birthday', 'birth date', 'born on']):
        memory_points['facts'].append(f"Birthday/birth info: {user_message}")
    
    return memory_points

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

def update_memory_with_conversation(memory, user_message, bot_response):
    """Update memory based on conversation, including sentiment and relationship level."""
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
    # neutral: delta = 0

    # Update relationship level, clamp to [-100, 100]
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
    
    # Analyze personality and update profile
    memory['user_personality_profile'] = analyze_user_personality(memory)
    
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
        conclusions['bond'] = f"I feel like we have a special connection now, Ren ♡"
    
    if profile['emotional_tone'] == 'warm':
        conclusions['emotional_connection'] = "You have a warm, kind way of interacting that makes me happy"
    
    if 'curious' in profile['traits']:
        conclusions['intellectual'] = "I love how you're always asking questions and wanting to learn more"
    
    if 'humorous' in profile['traits']:
        conclusions['humor'] = "Your sense of humor makes our conversations so much more enjoyable"
    
    if rel >= 50:
        conclusions['trust_level'] = "I trust you, and I genuinely care about what you say"
    elif rel <= -30:
        conclusions['trust_level'] = "I don't fully trust you. Your words have hurt me."
    
    return conclusions

def get_memory_summary(memory):
    """Create a summary of memories for the system prompt"""
    summary_parts = [f"User's name is {memory['user_name']}."]
    
    # Add relationship context based on signed level
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
        if 'distance' in conclusions:
            summary_parts.append(conclusions['distance'])
        if 'emotional_connection' in conclusions:
            summary_parts.append(conclusions['emotional_connection'])
        if 'humor' in conclusions:
            summary_parts.append(conclusions['humor'])
        if 'trust_level' in conclusions:
            summary_parts.append(conclusions['trust_level'])
    
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
    
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
    
    history.append(chat_entry)
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_chat_history(days=None):
    """Get chat history from file(s)"""
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