"""
Authentication routes
"""
from flask import Blueprint, request, jsonify
from backend.services.auth_service import auth_service
from backend.core.logger import get_logger

logger = get_logger(__name__)
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """POST /api/auth/login"""
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    result = auth_service.authenticate(email, password)
    if result:
        user, token = result
        return jsonify({
            'token': token,
            'user': user.to_dict()
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """POST /api/auth/logout"""
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None
    
    if token:
        auth_service.logout(token)
    
    return jsonify({'success': True})


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """GET /api/auth/me"""
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    # Verify token and get user
    user = auth_service.get_user_by_token(token)
    if user:
        return jsonify(user.to_dict())
    
    return jsonify({'error': 'Invalid token'}), 401
