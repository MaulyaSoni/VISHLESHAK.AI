"""
Flask entry point - Run with: python flask_api/app.py
"""
import os
import sys

# Add parent directory to path to import existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")

from flask_api import create_app, socketio

app = create_app()

if __name__ == '__main__':
    print("🚀 Starting Vishleshak AI Flask API on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
