"""
Create default admin user for testing
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "app_modules"))

from app_modules.auth.auth_manager import AuthManager, AuthError

auth_manager = AuthManager()

try:
    user = auth_manager.register_user(
        email="admin@test.com",
        username="admin",
        password="Admin123!",
        full_name="Admin User"
    )
    print(f"✅ Created user: {user.email}")
    print(f"   Username: admin")
    print(f"   Password: Admin123!")
except AuthError as e:
    if "already registered" in str(e):
        print("ℹ️  User already exists - can login now!")
        print(f"   Email: admin@test.com")
        print(f"   Password: Admin123!")
    else:
        print(f"❌ Error: {e}")
