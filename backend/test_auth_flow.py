import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("TESTING AUTH FLOW")
print("=" * 60)

# Step 1: Try to register
print("\n1️⃣  REGISTERING USER...")
register_url = f"{BASE_URL}/api/auth/register"
register_data = {
    "username": "admin",
    "email": "admin@test.com",
    "password": "admin123"
}

try:
    response = requests.post(register_url, json=register_data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("   ✅ User registered successfully!")
    elif response.status_code == 400:
        print("   ℹ️  User already exists (this is OK)")
    else:
        print(f"   ❌ Unexpected error")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 2: Try to login
print("\n2️⃣  LOGGING IN...")
login_url = f"{BASE_URL}/api/auth/login"
login_data = {
    "email": "admin@test.com",
    "password": "admin123"
}

try:
    response = requests.post(login_url, json=login_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
        print("   ✅ LOGIN SUCCESSFUL!")
        print(f"   Token: {data.get('token', 'N/A')[:50]}...")
        print(f"   User: {data.get('user', {})}")
    else:
        error_data = response.json()
        print(f"   Error Response: {json.dumps(error_data, indent=2)}")
        print("   ❌ LOGIN FAILED!")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 3: Check database directly
print("\n3️⃣  CHECKING DATABASE...")
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app_modules.database.db_manager import DatabaseManager
    from app_modules.database.user_repository import UserRepository
    
    db_manager = DatabaseManager()
    with db_manager.get_db() as db:
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_email("admin@test.com")
        
        if user:
            print(f"   ✅ User found in database!")
            print(f"      ID: {user.id}")
            print(f"      Email: {user.email}")
            print(f"      Username: {user.username}")
            print(f"      Active: {user.is_active}")
        else:
            print("   ❌ User NOT found in database!")
            print("   This is why login is failing!")
except Exception as e:
    print(f"   ❌ Database check error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
