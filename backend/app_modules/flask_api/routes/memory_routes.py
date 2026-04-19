"""
Memory Routes - Handles memory stats and clearing
"""
from flask import Blueprint, jsonify
from flask_login import login_required, current_user

memory_bp = Blueprint('memory', __name__)

# Import existing memory system
try:
    from core.enhanced_memory import EnhancedMemory
    memory = EnhancedMemory()
    MEMORY_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Memory system not available: {e}")
    MEMORY_AVAILABLE = False


@memory_bp.route('/stats', methods=['GET'])
@login_required
def get_memory_stats():
    """GET /api/memory/stats - Get memory statistics"""
    if not MEMORY_AVAILABLE:
        return jsonify({
            'hot_turns': 0,
            'tier2_datasets': 0,
            'tier3_exists': False,
            'top_datasets': []
        })
    
    try:
        # Get memory stats for current user
        user_id = str(current_user.id)
        stats = memory.get_stats(user_id)
        
        return jsonify({
            'hot_turns': stats.get('hot_turns', 0),
            'tier2_datasets': stats.get('tier2_count', 0),
            'tier3_exists': stats.get('tier3_exists', False),
            'top_datasets': stats.get('top_datasets', [])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/dataset/<hash>', methods=['DELETE'])
@login_required
def clear_dataset_memory(hash: str):
    """DELETE /api/memory/dataset/:hash - Clear memory for a specific dataset"""
    if not MEMORY_AVAILABLE:
        return jsonify({'error': 'Memory system not available'}), 503
    
    try:
        user_id = str(current_user.id)
        memory.clear_dataset(user_id, hash)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@memory_bp.route('/all', methods=['DELETE'])
@login_required
def clear_all_memory():
    """DELETE /api/memory/all - Clear all memory for user"""
    if not MEMORY_AVAILABLE:
        return jsonify({'error': 'Memory system not available'}), 503
    
    try:
        user_id = str(current_user.id)
        memory.clear_all(user_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
