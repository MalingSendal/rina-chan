from flask import Blueprint, jsonify
from utils.memory import load_memory, save_memory, clear_memory, get_chat_history

memory_bp = Blueprint('memory', __name__, url_prefix='/memory')

@memory_bp.route('/get', methods=['GET'])
def get_memory():
    """Get current user memory"""
    try:
        memory = load_memory()
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
        from flask import request
        data = request.get_json()
        memory = load_memory()
        
        # Update specific fields
        if 'user_name' in data:
            memory['user_name'] = data['user_name']
        if 'personality_traits' in data:
            memory['personality_traits'] = data['personality_traits']
        if 'preferences' in data:
            memory['preferences'] = data['preferences']
        
        save_memory(memory)
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
        memory = clear_memory()
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
        from flask import request
        days = request.args.get('days', None, type=int)
        history = get_chat_history(days)
        
        return jsonify({
            'success': True,
            'total_messages': len(history),
            'history': history[-100:]  # Return last 100 messages
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
        memory = load_memory()
        history = get_chat_history()
        
        # Determine relationship stage
        rel_level = memory['relationship_level']
        if rel_level < 20:
            relationship_stage = "🌱 Just Getting Started"
        elif rel_level < 50:
            relationship_stage = "💚 Building Friendship"
        elif rel_level < 80:
            relationship_stage = "💕 Close Companions"
        else:
            relationship_stage = "💗 Deeply Connected"
        
        stats = {
            'user_name': memory['user_name'],
            'conversation_count': memory['conversation_count'],
            'total_saved_messages': len(history),
            'learned_facts_count': len(memory['learned_facts']),
            'interests_count': len(memory['interests']),
            'preferences_count': len(memory['preferences']),
            'first_conversation': memory['created_at'],
            'last_conversation': memory['last_conversation'],
            'relationship_level': rel_level,
            'relationship_stage': relationship_stage,
            'personality_traits': memory['user_personality_profile'].get('traits', []),
            'emotional_tone': memory['user_personality_profile'].get('emotional_tone', 'friendly'),
            'engagement_level': memory['user_personality_profile'].get('engagement_level', 'moderate'),
            'rina_conclusions': memory['conclusions_about_user']
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
