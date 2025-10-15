import os
import requests

# Load environment variables from .env if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

api_key = os.environ.get('JULES_API_KEY')
if not api_key:
    print("❌ JULES_API_KEY not set")
    exit(1)

headers = {
    'X-Goog-Api-Key': api_key,
    'Content-Type': 'application/json'
}

# Test: List sources
print("Testing Jules API...")
url = 'https://jules.googleapis.com/v1alpha/sources'
response = requests.get(url, headers=headers)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    sources = response.json().get('sources', [])
    print(f"✅ Jules API responding")
    print(f"   Found {len(sources)} connected repositories")
    for source in sources[:3]:
        print(f"   - {source.get('name', 'unknown')}")
elif response.status_code == 401:
    print("❌ API key invalid or expired")
    print("   Get new key from: https://jules.google → Settings → API Keys")
elif response.status_code == 403:
    print("❌ API key lacks permissions")
else:
    print(f"❌ Unexpected response: {response.status_code}")
    print(f"   Body: {response.text}")
