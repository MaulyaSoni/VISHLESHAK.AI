"""
Authentication Routes - Wraps existing auth/auth_manager.py
"""
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Import existing auth system
try:
    from auth.auth_manager import AuthManager
    auth_manager = AuthManager()
    AUTH_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Auth system not available: {e}")
    AUTH_AVAILABLE = False


def json_required(f):
    """Decorator to ensure JSON body"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['POST'])
@json_required
def login():
    """POST /api/auth/login - Authenticate user"""
    if not AUTH_AVAILABLE:
        return jsonify({'error': 'Authentication system not available'}), 503
    
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    try:
        user, token = auth_manager.login_user(email, password)
        if user:
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'full_name': user.full_name,
                    'domain': 'general'  # Default domain
                }
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """POST /api/auth/logout - Logout user"""
    logout_user()
    return jsonify({'success': True})


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """GET /api/auth/me - Get current user info"""
    if not AUTH_AVAILABLE:
        # Return anonymous user for development
        return jsonify({
            'user': {
                'id': 'anonymous',
                'email': 'anonymous@vishleshak.ai',
                'username': 'anonymous',
                'full_name': 'Anonymous User',
                'domain': 'general'
            }
        })
    
    # For now, return anonymous user
    # TODO: Implement proper session management
    return jsonify({
        'user': {
            'id': 'anonymous',
            'email': 'anonymous@vishleshak.ai',
            'username': 'anonymous',
            'full_name': 'Anonymous User',
            'domain': 'general'
        }
    })


@auth_bp.route('/register', methods=['POST'])
@json_required
def register():
    """POST /api/auth/register - Register new user"""
    if not AUTH_AVAILABLE:
        return jsonify({'error': 'Authentication system not available'}), 503
    
    data = request.get_json()
    email = data.get('email', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    
    if not email or not username or not password:
        return jsonify({'error': 'Email, username, and password required'}), 400
    
    try:
        user = auth_manager.register_user(email, username, password, full_name)
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
