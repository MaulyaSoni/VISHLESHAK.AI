import requests
import json

# Test login endpoint
url = "http://localhost:8000/api/auth/login"
data = {
    "email": "admin@test.com",
    "password": "Admin123!"
}

print("Testing login endpoint...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")
print()

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
