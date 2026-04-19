"""
Backend entry point
Run with: python backend/run.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add backend app modules (legacy packages moved under backend/app_modules)
_app_modules = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_modules")
if os.path.isdir(_app_modules):
    sys.path.insert(0, _app_modules)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from backend.api import create_app
from backend.config import get_settings

settings = get_settings()
app = create_app()

if __name__ == '__main__':
    print(f"🚀 Starting Vishleshak AI Backend v2.0.0")
    print(f"   API: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"   Frontend: {settings.FRONTEND_URL}")
    print(f"   Debug: {settings.DEBUG}")
    print()
    
    app.run(
        host=settings.API_HOST,
        port=settings.API_PORT,
        debug=settings.DEBUG,
        use_reloader=False
    )
