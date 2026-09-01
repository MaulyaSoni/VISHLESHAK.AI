"""
Test all new API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(name, method, endpoint, data=None):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        status = "✅ PASS" if response.status_code == 200 else "⚠️ FAIL"
        print(f"{status} [{response.status_code}]")
        print(f"Response: {json.dumps(response.json(), indent=2)[:300]}...")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

# Run tests
print("\n🧪 TESTING ALL NEW API ENDPOINTS")
print("="*60)

results = []

# Test 1: Health Check
results.append(test_endpoint(
    "Health Check", "GET", "/health"
))

# Test 2: Benchmarks
results.append(test_endpoint(
    "Get Benchmarks", "GET", "/api/benchmarks"
))

# Test 3: Memory
results.append(test_endpoint(
    "Get Memory", "GET", "/api/memory?filter=all&limit=10"
))

# Test 4: Chat
results.append(test_endpoint(
    "Chat with AI", "POST", "/api/chat",
    data={
        "message": "What is correlation analysis?",
        "conversation_id": "test_conv_1"
    }
))

# Test 5: Agent Status (existing)
results.append(test_endpoint(
    "Agent Jobs", "GET", "/api/agent/jobs"
))

# Test 6: Auth Check
results.append(test_endpoint(
    "Auth Health", "GET", "/api/auth/health"
))

# Summary
print(f"\n{'='*60}")
print(f"📊 TEST SUMMARY")
print(f"{'='*60}")
print(f"Total: {len(results)}")
print(f"Passed: {sum(results)}")
print(f"Failed: {len(results) - sum(results)}")
print(f"Success Rate: {(sum(results)/len(results)*100):.1f}%")

if all(results):
    print("\n✅ ALL TESTS PASSED! Production API is ready!")
else:
    print(f"\n⚠️  {len(results) - sum(results)} test(s) need attention")
