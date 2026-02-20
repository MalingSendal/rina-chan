from flask import Blueprint, jsonify, request
from utils.memory import load_memory, save_memory, clear_memory, get_chat_history

memory_bp = Blueprint('memory', __name__, url_prefix='/memory')

@memory_bp.route('/get', methods=['GET'])
def get_memory():
    """Get current user memory"""
    try:
        user_id = request.args.get('user_id', None)
        memory = load_memory(user_id=user_id)
        return jsonify({
            'success': True,
            'memory': memory
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@memory_bp.route('/update', methods=['POST'])
def update_memory():
    """Manually update memory (admin function)"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', None)
        memory = load_memory(user_id=user_id)
        
        if 'user_name' in data:
            memory['user_name'] = data['user_name']
        if 'personality_traits' in data:
            memory['personality_traits'] = data['personality_traits']
        if 'preferences' in data:
            memory['preferences'] = data['preferences']
        
        save_memory(memory, user_id=user_id)
        return jsonify({
            'success': True,
            'memory': memory
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@memory_bp.route('/clear', methods=['POST'])
def clear():
    """Clear all memory (admin function)"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', None)
        memory = clear_memory(user_id=user_id)
        return jsonify({
            'success': True,
            'message': 'Memory cleared',
            'memory': memory
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@memory_bp.route('/history', methods=['GET'])
def get_history():
    """Get saved chat history"""
    try:
        days = request.args.get('days', None, type=int)
        user_id = request.args.get('user_id', None)
        history = get_chat_history(days, user_id=user_id)
        
        return jsonify({
            'success': True,
            'total_messages': len(history),
            'history': history[-100:]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@memory_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get memory statistics"""
    try:
        user_id = request.args.get('user_id', None)
        memory = load_memory(user_id=user_id)
        history = get_chat_history(None, user_id=user_id)
        
        rel_level = memory.get('relationship_level', 0)
        # Determine relationship stage (now includes negative)
        if rel_level >= 80:
            relationship_stage = "💗 Deeply Connected"
        elif rel_level >= 50:
            relationship_stage = "💕 Close Companions"
        elif rel_level >= 20:
            relationship_stage = "💚 Building Friendship"
        elif rel_level >= 0:
            relationship_stage = "🌱 Just Getting Started"
        elif rel_level > -30:
            relationship_stage = "😕 Slightly Strained"
        elif rel_level > -60:
            relationship_stage = "😤 Resentful"
        else:
            relationship_stage = "💔 Hostile"
        
        stats = {
            'user_name': memory.get('user_name'),
            'conversation_count': memory.get('conversation_count', 0),
            'total_saved_messages': len(history),
            'learned_facts_count': len(memory.get('learned_facts', {})),
            'interests_count': len(memory.get('interests', {})),
            'preferences_count': len(memory.get('preferences', {})),
            'positive_interactions': memory.get('positive_interactions', 0),
            'negative_interactions': memory.get('negative_interactions', 0),
            'first_conversation': memory.get('created_at'),
            'last_conversation': memory.get('last_conversation'),
            'relationship_level': rel_level,
            'relationship_stage': relationship_stage,
            'personality_traits': memory.get('user_personality_profile', {}).get('traits', []),
            'emotional_tone': memory.get('user_personality_profile', {}).get('emotional_tone', 'friendly'),
            'engagement_level': memory.get('user_personality_profile', {}).get('engagement_level', 'moderate'),
            'rina_conclusions': memory.get('conclusions_about_user', {})
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500