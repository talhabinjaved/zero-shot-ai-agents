import os
import requests
import time

# Load environment variables from .env if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

token = os.environ['GITHUB_TOKEN']
owner = os.environ['GITHUB_OWNER']

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28'
}

# Determine if org or user
user_response = requests.get(f'https://api.github.com/users/{owner}', headers=headers)
if user_response.status_code != 200:
    print(f"❌ Cannot determine account type: {user_response.status_code}")
    print(f"   Error: {user_response.json()}")
    exit(1)
account_type = user_response.json()['type']

# Create test repo
test_repo_name = f'orchestrator-test-{int(time.time())}'

if account_type == 'Organization':
    url = f'https://api.github.com/orgs/{owner}/repos'
else:
    url = f'https://api.github.com/user/repos'

payload = {
    'name': test_repo_name,
    'description': 'Test repository for orchestrator validation - safe to delete',
    'private': True,
    'auto_init': False
}

print(f"Creating test repository: {owner}/{test_repo_name}")
response = requests.post(url, headers=headers, json=payload)

if response.status_code == 201:
    repo = response.json()
    print(f"✅ Repository created: {repo['full_name']}")
    print(f"   URL: {repo['html_url']}")
    print()
    print("⚠️  CLEANUP: Delete this test repo manually or run:")
    print(f"   gh repo delete {repo['full_name']} --yes")
elif response.status_code == 422:
    print(f"⚠️  Repository already exists (this is OK for testing)")
else:
    print(f"❌ Failed to create repository: {response.status_code}")
    print(f"   Error: {response.json()}")
    exit(1)
