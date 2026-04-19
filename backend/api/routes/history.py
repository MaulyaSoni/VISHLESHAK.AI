"""
History routes - Chat and Analysis history from database
"""
from flask import Blueprint, request, jsonify, g
from backend.core.logger import get_logger
from database.chat_repository import ChatRepository
from database.analysis_repository import AnalysisRepository

logger = get_logger(__name__)
history_bp = Blueprint('history', __name__)

chat_repo = ChatRepository()
analysis_repo = AnalysisRepository()


def get_current_user_id():
    """Get current user ID from JWT token"""
    from flask import g
    return getattr(g, 'user_id', 1)  # Default to user 1 for dev


@history_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """GET /api/history/conversations - Get user's chat conversations"""
    try:
        user_id = get_current_user_id()
        limit = request.args.get('limit', 50, type=int)
        
        conversations = chat_repo.get_user_conversations(user_id=user_id, limit=limit)
        
        result = []
        for conv in conversations:
            result.append({
                'id': conv.id,
                'title': conv.title,
                'dataset_name': conv.dataset_name,
                'dataset_rows': conv.dataset_rows,
                'dataset_cols': conv.dataset_cols,
                'created_at': conv.created_at.isoformat() if conv.created_at else None,
                'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
                'is_archived': conv.is_archived
            })
        
        return jsonify({'conversations': result})
        
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/conversations/<int:conv_id>/messages', methods=['GET'])
def get_conversation_messages(conv_id):
    """GET /api/history/conversations/<id>/messages - Get messages for a conversation"""
    try:
        user_id = get_current_user_id()
        
        # Verify conversation belongs to user
        conv = chat_repo.get_conversation(conv_id)
        if not conv or conv.user_id != user_id:
            return jsonify({'error': 'Conversation not found'}), 404
        
        messages = chat_repo.get_messages(conv_id)
        
        result = []
        for msg in messages:
            result.append({
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'created_at': msg.created_at.isoformat() if msg.created_at else None,
                'quality_score': msg.quality_score,
                'quality_grade': msg.quality_grade
            })
        
        return jsonify({'messages': result})
        
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/conversations', methods=['POST'])
def create_conversation():
    """POST /api/history/conversations - Create new conversation"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        title = data.get('title', 'New Chat')
        dataset_info = data.get('dataset_info')
        
        conv = chat_repo.create_conversation(
            user_id=user_id,
            title=title,
            dataset_info=dataset_info
        )
        
        return jsonify({
            'id': conv.id,
            'title': conv.title,
            'created_at': conv.created_at.isoformat() if conv.created_at else None
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/conversations/<int:conv_id>/messages', methods=['POST'])
def save_message(conv_id):
    """POST /api/history/conversations/<id>/messages - Save a message"""
    try:
        user_id = get_current_user_id()
        
        # Verify conversation belongs to user
        conv = chat_repo.get_conversation(conv_id)
        if not conv or conv.user_id != user_id:
            return jsonify({'error': 'Conversation not found'}), 404
        
        data = request.get_json()
        role = data.get('role')
        content = data.get('content')
        metadata = data.get('metadata')
        
        if not role or not content:
            return jsonify({'error': 'Role and content required'}), 400
        
        msg = chat_repo.save_message(
            conversation_id=conv_id,
            role=role,
            content=content,
            metadata=metadata
        )
        
        return jsonify({
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'created_at': msg.created_at.isoformat() if msg.created_at else None
        }), 201
        
    except Exception as e:
        logger.error(f"Error saving message: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/conversations/<int:conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    """DELETE /api/history/conversations/<id> - Delete a conversation"""
    try:
        user_id = get_current_user_id()
        
        # Verify conversation belongs to user
        conv = chat_repo.get_conversation(conv_id)
        if not conv or conv.user_id != user_id:
            return jsonify({'error': 'Conversation not found'}), 404
        
        chat_repo.delete_conversation(conv_id)
        return jsonify({'status': 'deleted'})
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/analyses', methods=['GET'])
def get_analyses():
    """GET /api/history/analyses - Get user's analysis reports"""
    try:
        user_id = get_current_user_id()
        limit = request.args.get('limit', 10, type=int)
        completed_only = request.args.get('completed_only', 'true').lower() == 'true'
        
        reports = analysis_repo.get_user_reports(
            user_id=user_id,
            limit=limit,
            include_completed_only=completed_only
        )
        
        result = []
        for report in reports:
            result.append({
                'id': report.id,
                'title': report.title,
                'instruction': report.instruction,
                'mode': report.mode,
                'status': report.status,
                'dataset_name': report.dataset_name,
                'dataset_rows': report.dataset_rows,
                'dataset_cols': report.dataset_cols,
                'created_at': report.created_at.isoformat() if report.created_at else None,
                'updated_at': report.updated_at.isoformat() if report.updated_at else None,
                'executive_summary': report.executive_summary
            })
        
        return jsonify({'analyses': result})
        
    except Exception as e:
        logger.error(f"Error fetching analyses: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/analyses/<int:report_id>', methods=['GET'])
def get_analysis(report_id):
    """GET /api/history/analyses/<id> - Get full analysis report"""
    try:
        user_id = get_current_user_id()
        
        report = analysis_repo.get_report(report_id)
        if not report or report.user_id != user_id:
            return jsonify({'error': 'Report not found'}), 404
        
        full_data = analysis_repo.get_full_report_data(report_id)
        
        return jsonify({
            'id': report.id,
            'title': report.title,
            'instruction': report.instruction,
            'mode': report.mode,
            'status': report.status,
            'dataset_name': report.dataset_name,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'full_report': full_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching analysis: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/analyses/<int:report_id>', methods=['DELETE'])
def delete_analysis(report_id):
    """DELETE /api/history/analyses/<id> - Delete an analysis report"""
    try:
        user_id = get_current_user_id()
        
        report = analysis_repo.get_report(report_id)
        if not report or report.user_id != user_id:
            return jsonify({'error': 'Report not found'}), 404
        
        analysis_repo.delete_report(report_id)
        return jsonify({'status': 'deleted'})
        
    except Exception as e:
        logger.error(f"Error deleting analysis: {e}")
        return jsonify({'error': str(e)}), 500
