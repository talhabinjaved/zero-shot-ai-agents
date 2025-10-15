import os
import requests

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

# Check if owner is org or user
user_response = requests.get(f'https://api.github.com/users/{owner}', headers=headers)
if user_response.status_code != 200:
    print(f"❌ Cannot find user/org: {owner}")
    print(f"   Error: {user_response.json()}")
    exit(1)

account_type = user_response.json()['type']
print(f"✅ Found {account_type}: {owner}")

# List repos (first 5)
if account_type == 'Organization':
    repos_url = f'https://api.github.com/orgs/{owner}/repos?per_page=5'
else:
    repos_url = f'https://api.github.com/user/repos?per_page=5'

repos_response = requests.get(repos_url, headers=headers)
if repos_response.status_code == 200:
    repos = repos_response.json()
    print(f"✅ Can list repositories ({len(repos)} shown)")
    for repo in repos[:3]:
        print(f"   - {repo['full_name']}")
else:
    print(f"❌ Cannot list repos: {repos_response.status_code}")
    print(f"   Error: {repos_response.json()}")
