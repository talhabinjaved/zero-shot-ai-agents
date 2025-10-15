import sys
import os

# Set test mode
os.environ['GITHUB_TOKEN'] = os.environ.get('GITHUB_TOKEN', 'ghp_test_token_placeholder')
os.environ['GITHUB_OWNER'] = os.environ.get('GITHUB_OWNER', 'test-owner-placeholder')
os.environ['JULES_API_KEY'] = os.environ.get('JULES_API_KEY', 'test_jules_key_placeholder')

import sys
sys.path.insert(0, '../providers/jules')
from orchestrator import JulesOrchestrator, RepoConfig

print("=" * 60)
print("SINGLE REPO TEST - JULES")
print("=" * 60)
print()
print("⚠️  This will attempt to create a REAL repository and start a REAL Jules session")
print("⚠️  It will consume API quota if credentials are real")
print("⚠️  Using DUMMY credentials - this will FAIL but test the logic")
print()

try:
    # Skip user input for automated testing
    # input("Press ENTER to continue or Ctrl+C to cancel...")
    print("Starting test automatically...")
except KeyboardInterrupt:
    print("Test cancelled")
    exit(0)

print()

config = RepoConfig(
    owner=os.environ['GITHUB_OWNER'],
    token=os.environ['GITHUB_TOKEN'],
    max_concurrent=1
)

orchestrator = JulesOrchestrator(config, os.environ['JULES_API_KEY'])

# Load single idea
ideas = orchestrator.load_ideas('test_single_run.csv')
print(f"Loaded {len(ideas)} idea(s)")
print()

# Process single idea
if len(ideas) > 0:
    idea = ideas[0]
    print(f"Processing: {idea.title}")
    print(f"Has experiments: {idea.has_experiments}")
    print(f"Idea: {idea.idea[:100]}...")
    print()

    result = orchestrator.process_idea(idea, require_plan_approval=False)

    print()
    print("RESULT:")
    print(f"  Status: {result.get('status')}")
    print(f"  Repo: {result.get('repo')}")
    print(f"  Session ID: {result.get('session_id')}")

    if result.get('status') == 'session_started':
        print()
        print("✅ SUCCESS! Jules session started")
        print(f"   Monitor at: https://jules.google")
        print(f"   Repository: https://github.com/{result['repo']}")
    else:
        print()
        print(f"❌ FAILED: {result.get('error')}")
        print("   This is expected with dummy credentials")
else:
    print("❌ No ideas loaded")
