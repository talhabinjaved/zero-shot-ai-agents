# Quick Start Guide

Get up and running with AI agent experiment orchestration in 5 minutes.

## Step 1: Choose Your Provider

Pick one to start (you can test others later):

- **Augment** - Best CLI automation, requires Node.js
- **Jules** - Best API automation, easiest to scale
- **Cosine** - Best CI monitoring, requires manual setup
- **OpenHands** - Best for custom models, conversation-based

## Step 2: Install Prerequisites

### All Providers Need:
```bash
# Python 3.8+
python --version

# GitHub CLI (recommended but optional)
gh --version
```

### Provider-Specific:

**Augment:**
```bash
npm i -g @augmentcode/auggie
auggie --login
auggie --print-augment-token  # Save this
```

**Jules:**
- Visit [jules.google](https://jules.google)
- Go to Settings → API Keys
- Create new API key
- Install Jules GitHub App with "All repositories" access

**Cosine:**
```bash
brew install CosineAI/tap/cos  # macOS
# or: curl -fsSL https://cosine.sh/install | bash  # Linux
cos login
```

**OpenHands:**
- Visit [app.all-hands.dev](https://app.all-hands.dev)
- Sign up and go to Settings
- Generate API key
- Install OpenHands Cloud GitHub App

## Step 3: Set Environment Variables

### For Augment:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_OWNER="your-github-username"
export AUGMENT_SESSION_AUTH="your_augment_token"
```

### For Jules:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_OWNER="your-github-username"
export JULES_API_KEY="your_jules_api_key"
```

### For Cosine:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_OWNER="your-github-username"
# No API key needed - uses manual import
```

### For OpenHands:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_OWNER="your-github-username"
export OPENHANDS_API_KEY="your_openhands_key"
```

## Step 4: Create Your Ideas File

Create a simple test file:

```bash
cat > test_ideas.csv << 'EOF'
title,has_experiments,idea,experiments
"Hello World Test",False,"Create a simple Python script that prints hello world and runs a basic test",""
EOF
```

## Step 5: Run the Orchestrator

```bash
# For Augment:
cd augment
pip install -r requirements.txt
python orchestrator.py --input ../test_ideas.csv --dry-run  # Test first
python orchestrator.py --input ../test_ideas.csv             # Real run

# For Jules:
cd jules
pip install -r requirements.txt
python orchestrator.py --input ../test_ideas.csv --dry-run  # Test first
python orchestrator.py --input ../test_ideas.csv             # Real run

# For Cosine:
cd cosine
pip install -r requirements.txt
python orchestrator.py --input ../test_ideas.csv --dry-run  # Test first
python orchestrator.py --input ../test_ideas.csv             # Real run

# For OpenHands:
cd openhands
pip install -r requirements.txt
python orchestrator.py --input ../test_ideas.csv --dry-run  # Test first
python orchestrator.py --input ../test_ideas.csv             # Real run
```

## Step 6: Monitor Progress

### Augment:
- Check logs: `tail -f orchestrator.log`
- Augment will open PRs automatically
- Review at: https://augmentcode.com

### Jules:
- Check logs: `tail -f jules_orchestrator.log`
- Monitor sessions at: https://jules.google
- Approve plans when prompted

### Cosine:
- Check logs: `tail -f cosine_orchestrator.log`
- Import repos into Cosine workspace
- Configure CI monitoring in Project Settings
- Monitor at: https://cosine.sh

### OpenHands:
- Check logs: `tail -f openhands_orchestrator.log`
- Monitor conversations at: https://app.all-hands.dev
- Check for PRs in your GitHub repositories

## Expected Output

The orchestrator will:
1. ✅ Create GitHub repository (e.g., `your-org/hello-world-test`)
2. ✅ Seed with templates (AGENTS.md, experiments.yaml, workflows, etc.)
3. ✅ Start agent session/conversation
4. ✅ Log progress to console and file
5. ✅ Print summary with repository URLs

**Example output:**
```
2025-10-14 12:00:00 - INFO - Loaded 1 experiment ideas
2025-10-14 12:00:00 - INFO -   - 0 with pre-defined experiments
2025-10-14 12:00:00 - INFO -   - 1 requiring AI planning
2025-10-14 12:00:05 - INFO - Created repository: your-org/hello-world-test
2025-10-14 12:00:10 - INFO - Seeding repository: your-org/hello-world-test
2025-10-14 12:00:15 - INFO - Repository seeded successfully
2025-10-14 12:00:20 - INFO - Starting Jules session for your-org/hello-world-test
2025-10-14 12:00:25 - INFO -   Pipeline type: AI planning required
2025-10-14 12:00:30 - INFO - Created Jules session: sessions/abc123...
2025-10-14 12:00:30 - INFO - Batch processing completed:
2025-10-14 12:00:30 - INFO -   Jules sessions started: 1
2025-10-14 12:00:30 - INFO -   Failed: 0
```

## Testing Pre-Defined Experiments

Try a pre-defined experiment:

```bash
cat > test_predefined.csv << 'EOF'
title,has_experiments,idea,experiments
"Simple Math Test",True,"Test basic arithmetic functions","stop_on_fail: true
steps:
  - name: test_addition
    description: Test addition function
    cmd: python -c 'assert 2+2==4; print(\"Addition OK\")'
    sanity:
      - type: file_exists
        path: /dev/null
    retry: 1
    timeout_minutes: 5"
EOF

python orchestrator.py --input ../test_predefined.csv
```

## Troubleshooting Quick Fixes

### "GITHUB_TOKEN not set"
```bash
export GITHUB_TOKEN="ghp_..."  # Get from https://github.com/settings/tokens
```

### "Repository already exists"
- Orchestrator will use existing repo (logged as warning)
- Or manually delete the repo and re-run

### "Auggie not found"
```bash
npm i -g @augmentcode/auggie
which auggie  # Should show path
```

### "Jules source not found"
- Wait 30 seconds for Jules to index new repo
- Verify Jules GitHub App has repo access
- Check app is installed with "All repositories"

### "Rate limit exceeded"
- Reduce `--max-concurrent` value
- Wait and retry
- Check your API quota/tier

## Next Steps

1. ✅ Test with simple ideas first
2. ✅ Review generated repositories
3. ✅ Examine AI-generated code
4. ✅ Monitor CI workflow runs
5. ✅ Check final documentation quality

Then scale to your real experiment ideas!

## Advanced Usage

### Batch Processing Multiple Ideas
```bash
# Create ideas.csv with 10-50 ideas
python orchestrator.py --input ideas.csv --max-concurrent 3
```

### Custom Configuration
```bash
# Augment with custom output directory
python orchestrator.py --input ideas.csv --output-dir ~/experiments

# Jules with auto-approve (no plan approval needed)
python orchestrator.py --input ideas.csv --auto-approve

# Cosine with workflow triggering
python orchestrator.py --input ideas.csv --trigger-workflows
```

### Monitoring Long-Running Experiments
```bash
# OpenHands with extended timeout
python orchestrator.py --input ideas.csv --monitor-timeout 240
```

## Getting Help

- **CSV Format:** See `CSV_FORMAT.md`
- **Full Documentation:** See `README.md`
- **Implementation Details:** See `IMPLEMENTATION_SUMMARY.md`
- **Provider Docs:**
  - Augment: https://docs.augmentcode.com
  - Jules: https://jules.google/docs
  - Cosine: https://docs.cosine.sh
  - OpenHands: https://docs.all-hands.dev

---

**Ready to start?** Pick a provider, set your credentials, and run your first experiment! 🚀

