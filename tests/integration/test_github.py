import os
import requests

# Load environment variables from .env if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

token = os.environ.get('GITHUB_TOKEN')
if not token:
    print("❌ GITHUB_TOKEN not set")
    exit(1)

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json'
}

# Test token validity
response = requests.get('https://api.github.com/user', headers=headers)

if response.status_code == 200:
    user = response.json()
    print(f"✅ GitHub token valid")
    print(f"   User: {user.get('login')}")
    print(f"   Name: {user.get('name')}")
    
    # Check scopes
    scopes = response.headers.get('X-OAuth-Scopes', '').split(', ')
    print(f"   Scopes: {scopes}")
    
    if 'repo' in scopes or 'public_repo' in scopes:
        print("✅ Token has repo creation permissions")
    else:
        print("❌ Token missing 'repo' scope - cannot create repositories")
else:
    print(f"❌ GitHub token invalid: {response.status_code}")
    print(f"   Error: {response.json()}")
