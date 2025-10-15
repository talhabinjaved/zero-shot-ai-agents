import os
import requests
import base64

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

# Find the test repo (or create it)
test_repo_name = None
repos_response = requests.get(f'https://api.github.com/user/repos?per_page=100', headers=headers)
for repo in repos_response.json():
    if 'orchestrator-test' in repo['name']:
        test_repo_name = repo['full_name']
        break

if not test_repo_name:
    print("❌ No test repository found. Run test_github_create.py first")
    exit(1)

print(f"Testing file creation in: {test_repo_name}")

# Put a test file
file_content = "# Test File\n\nThis is a test file created by the orchestrator test suite."
content_b64 = base64.b64encode(file_content.encode()).decode()

url = f'https://api.github.com/repos/{test_repo_name}/contents/TEST.md'
payload = {
    'message': 'test: add TEST.md',
    'content': content_b64
}

response = requests.put(url, headers=headers, json=payload)

if response.status_code in (201, 200):
    print("✅ File created successfully")
    print(f"   URL: {response.json()['content']['html_url']}")
else:
    print(f"❌ Failed to create file: {response.status_code}")
    print(f"   Error: {response.json()}")
