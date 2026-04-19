"""Flask API layer"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from backend.config import get_settings

def create_app() -> Flask:
    """Create and configure Flask app"""
    settings = get_settings()
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = settings.MAX_CONTENT_LENGTH

    # Ensure DB is initialized for history/auth features (dev-friendly default user).
    try:
        from database.migrations import init_database
        init_database()

        from database.db_manager import get_db
        from database.models import User
        with get_db() as db:
            user = db.query(User).filter(User.id == 1).one_or_none()
            if user is None:
                # Minimal dev user for local history/auth flows
                db.add(User(id=1, email="dev@local", username="dev", password_hash="dev"))
    except Exception:
        # If DB init fails, API can still run (history endpoints will error).
        pass
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                settings.FRONTEND_URL,
                "http://localhost:5173",
                "http://localhost:5174",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:5174"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept"],
            "supports_credentials": True,
            "expose_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Direct routes for frontend compatibility (register FIRST)
    @app.route('/api/upload', methods=['POST', 'OPTIONS'])
    def upload():
        """POST /api/upload"""
        if request.method == 'OPTIONS':
            return '', 200
        from .routes.files import upload_file
        return upload_file()
    
    @app.route('/api/analyze', methods=['POST'])
    def analyze():
        """POST /api/analyze"""
        from .routes.analysis import analyze as analysis_endpoint
        return analysis_endpoint()
    
    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.files import files_bp
    from .routes.analysis import analysis_bp
    from .routes.datasets import datasets_bp
    from .routes.chat import chat_bp
    from .routes.agent import agent_bp
    from .routes.history import history_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(datasets_bp, url_prefix='/api/datasets')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(agent_bp, url_prefix='/api/agent')
    app.register_blueprint(history_bp, url_prefix='/api/history')
    
    # Health check
    @app.route('/api/health')
    def health_check():
        return {'status': 'ok', 'service': 'vishleshak-api', 'version': '2.0.0'}
    
    # Error handlers - ensure JSON responses
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app
