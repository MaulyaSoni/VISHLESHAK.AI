"""
Socket.IO handlers for proactive flag push notifications
"""
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user

# Store connected clients
connected_clients = {}


def register_socket_handlers(socketio):
    """Register all Socket.IO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Client connected"""
        if current_user.is_authenticated:
            user_id = str(current_user.id)
            join_room(user_id)
            connected_clients[user_id] = True
            emit('connected', {'status': 'connected', 'user_id': user_id})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Client disconnected"""
        if current_user.is_authenticated:
            user_id = str(current_user.id)
            leave_room(user_id)
            connected_clients.pop(user_id, None)
    
    @socketio.on('join')
    def handle_join(data):
        """Join a room for session-specific updates"""
        session_id = data.get('session_id')
        if session_id:
            join_room(session_id)
            emit('joined', {'session_id': session_id})


def emit_proactive_flag(user_id: str, severity: str, icon: str, message: str):
    """
    Emit a proactive flag to a specific user
    Called by proactive_engine.py after analysis completes
    """
    from flask_api import socketio
    
    socketio.emit('proactive_flag', {
        'severity': severity,
        'icon': icon,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }, room=str(user_id))


def emit_to_session(session_id: str, event_type: str, data: dict):
    """Emit an event to all clients in a session room"""
    from flask_api import socketio
    
    socketio.emit(event_type, {
        **data,
        'timestamp': datetime.now().isoformat()
    }, room=session_id)


# Import at bottom to avoid circular imports
from datetime import datetime
