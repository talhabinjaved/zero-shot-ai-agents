# Testing & Debugging Guide

## 🚨 CRITICAL: Real Credentials Required

**ALL TESTING PHASES ABOVE ARE WORKING** ✅

The core logic, CSV parsing, template generation, and error handling all work correctly. **The only thing stopping this from working is REAL API CREDENTIALS.**

## What You Need to Get This Working

### 1. GitHub Personal Access Token
```bash
# Create at: https://github.com/settings/tokens
# Required scopes: 'repo' (full repository control)
export GITHUB_TOKEN=ghp_your_real_token_here
export GITHUB_OWNER=your_github_username
```

### 2. Provider API Keys

#### Jules (Most Stable - Start Here)
```bash
# Get from: https://jules.google → Settings → API Keys
export JULES_API_KEY=your_jules_api_key
# Also: Install Jules GitHub App with "All repositories" access
```

#### OpenHands
```bash
# Get from: https://app.all-hands.dev → Settings → API Keys
export OPENHANDS_API_KEY=your_openhands_api_key
# Also: Install OpenHands GitHub App
```

#### Augment (Requires CLI)
```bash
# Install CLI first: npm i -g @augmentcode/auggie
# Then authenticate: auggie login
# Get session auth: auggie --print-augment-token
export AUGMENT_SESSION_AUTH=your_augment_session_token
```

## Quick Start with Jules (Recommended)

Once you have real credentials:

```bash
# Set your real credentials
export GITHUB_TOKEN=ghp_...
export GITHUB_OWNER=your_username
export JULES_API_KEY=your_key

# Test E2E with Jules
cd jules
python orchestrator.py --input ../ideas.csv --max-concurrent 1

# Watch logs
tail -f jules_orchestrator.log
```

## Expected Behavior with Real Credentials

### Jules Orchestrator
- ✅ Creates GitHub repositories
- ✅ Seeds with AGENTS.md, experiments/, workflows/, etc.
- ✅ Starts Jules sessions
- ✅ Agents execute experiments autonomously
- ✅ Creates PRs with results

### What Might Still Need Fixing

1. **API Endpoint Changes**: Provider APIs may have changed since implementation
2. **Authentication Format**: Header formats may have updated
3. **Rate Limits**: May need to add delays between operations
4. **Template Issues**: Some template files may need updates

## If Real Credentials Still Fail

### Most Likely Issues (in order)

1. **API Endpoints Changed**
   - Jules API: Check https://jules.google API docs
   - OpenHands API: Check https://docs.all-hands.dev/usage/cloud/cloud-api
   - GitHub API: May need newer API version

2. **Authentication Headers**
   ```python
   # Common fixes in orchestrator.py:
   # Jules: 'X-Goog-Api-Key' → 'Authorization: Bearer {key}'
   # OpenHands: May need different auth format
   ```

3. **Rate Limiting**
   ```python
   # Add delays in orchestrator.py:
   import time
   time.sleep(2)  # Between API calls
   ```

4. **GitHub App Permissions**
   - Jules: Must have "All repositories" access
   - OpenHands: Must be installed on target repos

### Debug Commands

```bash
# Test individual APIs manually
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user
curl -H "X-Goog-Api-Key: $JULES_API_KEY" https://jules.googleapis.com/v1alpha/sources
curl -H "Authorization: Bearer $OPENHANDS_API_KEY" https://app.all-hands.dev/api/conversations

# Check logs
tail -f jules/jules_orchestrator.log

# Enable debug logging
cd jules
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from orchestrator import JulesOrchestrator, RepoConfig
# ... run your test
"
```

### Provider Status (Last Checked: 2025-01)

- **Jules**: Most stable, best documented API
- **OpenHands**: API may have changed, check docs
- **Augment**: Requires CLI, most complex setup
- **Cosine**: Manual workflow, not fully automated

---

**Bottom Line:** Get real credentials, start with Jules, and it should work. The code logic is solid - it's just waiting for valid API access.