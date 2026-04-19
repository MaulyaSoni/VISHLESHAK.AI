"""
Vishleshak AI - Flask API Layer
Thin translation layer between React frontend and Python backend
"""

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_login import LoginManager

# Initialize extensions
socketio = SocketIO(cors_allowed_origins="*")
login_manager = LoginManager()


def create_app(config_name="development"):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'vishleshak-secret-key-change-in-production'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file upload
    
    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize extensions
    socketio.init_app(app)
    login_manager.init_app(app)
    
    # Register blueprints
    from .routes.auth_routes import auth_bp
    from .routes.analysis_routes import analysis_bp
    from .routes.file_routes import file_bp
    from .routes.memory_routes import memory_bp
    from .routes.report_routes import report_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(file_bp, url_prefix='/api/files')
    app.register_blueprint(memory_bp, url_prefix='/api/memory')
    app.register_blueprint(report_bp, url_prefix='/api/reports')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'ok', 'service': 'vishleshak-api'}
    
    return app
