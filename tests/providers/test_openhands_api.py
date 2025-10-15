import os
import requests

# Load environment variables from .env if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

api_key = os.environ.get('OPENHANDS_API_KEY')
if not api_key:
    print("❌ OPENHANDS_API_KEY not set")
    exit(1)

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# Test: Ping API (or list conversations)
print("Testing OpenHands API...")

# Note: Exact endpoint may vary - check docs if this fails
url = 'https://app.all-hands.dev/api/conversations'
response = requests.get(url, headers=headers)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    print("✅ OpenHands API responding")
    data = response.json()
    print(f"   Response keys: {list(data.keys())}")
elif response.status_code == 401:
    print("❌ API key invalid or expired")
    print("   Get new key from: https://app.all-hands.dev → Settings")
elif response.status_code == 404:
    print("⚠️  Endpoint may have changed")
    print("   Check: https://docs.all-hands.dev/usage/cloud/cloud-api")
else:
    print(f"⚠️  Response: {response.status_code}")
    print(f"   Body: {response.text[:200]}")
    print("   API endpoint may have changed - check docs")
