# AI Agent Experiment Orchestrator

> Automate computational experiments end-to-end using AI agents (Jules & OpenHands)

Transform experiment ideas into complete, production-ready research repositories with automated planning, execution, and comprehensive results — all powered by AI.

---

## 🎯 What It Does

This orchestrator takes **experiment ideas** (from CSV) and uses AI agents to:

1. **Plan experiments** - Design comprehensive experiment plans from scratch
2. **Write code** - Implement all necessary scripts (setup, baseline, experiments, analysis)
3. **Run experiments** - Execute via GitHub Actions with automated validation
4. **Generate results** - Create publication-quality RESULTS.md with visualizations
5. **Document everything** - Professional README with methods, findings, and next steps

**All without human intervention.**

---

## ⭐ Supported Providers

### 🥇 Jules (Recommended)
- **Status:** ⭐⭐⭐⭐⭐ Production-ready
- **API:** Full REST API automation
- **Best for:** Easiest setup, most reliable
- **Features:** Auto-planning, CI iteration, PR creation
- **URL:** https://jules.google

### 🥈 OpenHands (Excellent Alternative)
- **Status:** ⭐⭐⭐⭐⭐ Production-ready
- **API:** Conversation-based API
- **Best for:** BYO models (use your own LLM API keys)
- **Features:** Auto-planning, comprehensive workflows, flexible
- **URL:** https://app.all-hands.dev

**Note:** Augment and Cosine were tested and removed:
- **Augment:** Backend failures (100% error rate)
- **Cosine:** Architectural mismatch (CI fixer, not experiment creator)

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd zero-shot-ai-agents

# Set environment variables
export GITHUB_TOKEN=ghp_your_token_here
export GITHUB_OWNER=your_github_username
export JULES_API_KEY=your_jules_key_here  # For Jules
export OPENHANDS_API_KEY=your_key_here     # For OpenHands
```

### 2. Prepare Experiment Ideas

Create `data/ideas.csv`:
```csv
title,has_experiments,idea,experiments
Analyze Stock Trends,False,Use ML to predict stock movements from historical data,
Build Recommender,False,Create a movie recommendation system using collaborative filtering,
```

### 3. Run the Orchestrator

```bash
# Interactive mode (recommended)
./run_experiments.sh

# Or run directly
cd providers/jules
python orchestrator.py --input ../../data/ideas.csv --max-concurrent 1
```

### 4. Monitor & Review

- **Jules:** Visit https://jules.google to watch progress
- **OpenHands:** Visit https://app.all-hands.dev
- **GitHub:** Check your repos for new PRs with results

---

## 📁 Repository Structure

```
├── data/                      # Experiment ideas (CSV files)
│   └── ideas.csv             # Your experiment ideas
├── providers/
│   ├── jules/                # Jules orchestrator (⭐ Recommended)
│   │   ├── orchestrator.py   # Main orchestrator script
│   │   ├── requirements.txt  # Dependencies
│   │   └── templates/        # Repo templates
│   └── openhands/            # OpenHands orchestrator
│       ├── orchestrator.py   # Main orchestrator script
│       ├── requirements.txt  # Dependencies
│       └── templates/        # Repo templates
├── docs/                     # Documentation
│   ├── QUICKSTART.md         # Detailed setup guide
│   ├── CSV_FORMAT.md         # Input format specs
│   └── ...
├── tests/                    # Test suite
├── run_experiments.sh        # Interactive launcher
├── FIXES_APPLIED.md          # Technical fixes documentation
└── README.md                 # This file
```

---

## 🎨 Features

### ✅ Core Capabilities
- **Dual Pipeline:** AI planning OR pre-defined experiments
- **Automated Code Generation:** Scripts, tests, documentation
- **GitHub Integration:** Auto-create repos, manage branches
- **CI/CD Automation:** GitHub Actions workflows
- **Publication-Quality Results:** Visualizations, deep analysis, statistical tests
- **Error Handling:** Retry logic, comprehensive logging
- **Reproducibility:** Seeds, versions, hyperparameters documented

### 📊 Enhanced Results Quality (Fix #12)
Both Jules and OpenHands now generate:
- **Visualizations:** Model comparisons, learning curves, error distributions
- **Deep Analysis:** Error analysis, feature importance, edge cases
- **Statistical Validation:** P-values, confidence intervals
- **Implementation Details:** Code links, hyperparameters, seeds
- **Specific Next Steps:** Actionable recommendations with expected improvements

### 🛡️ Reliability Features
- **Smart .gitignore:** Results committed, models excluded
- **Timeout Handling:** 5-hour limits for complex experiments
- **Branch Detection:** Works with both `main` and `master`
- **File Update Logic:** Handles existing files correctly
- **Connection Resilience:** Auto-retry on network errors

---

## 📖 How It Works

### Workflow Overview

```
1. Read Ideas (CSV)
         ↓
2. Create GitHub Repo
         ↓
3. Seed with Templates
         ↓
4. Start AI Agent
         ↓
5. AI Plans Experiments
         ↓
6. AI Implements Code
         ↓
7. AI Runs via GitHub Actions
         ↓
8. AI Validates Results
         ↓
9. AI Generates RESULTS.md (with plots!)
         ↓
10. AI Creates PR
         ↓
11. Review & Merge
```

### Example Input (CSV)
```csv
title,has_experiments,idea,experiments
Test Neural Networks,False,Compare CNN vs RNN vs Transformer on MNIST,
```

### Example Output (GitHub Repo)
```
your-username/test-neural-networks/
├── README.md              # Professional documentation
├── RESULTS.md             # Comprehensive findings with visualizations
├── experiments/
│   └── experiments.yaml   # Complete experiment plan
├── scripts/
│   ├── setup.py          # Environment setup
│   ├── data_prep.py      # Data preprocessing
│   ├── baseline.py       # Baseline experiments
│   ├── experiment.py     # Main experiments
│   └── analysis.py       # Results analysis
├── artifacts/
│   ├── plots/
│   │   ├── model_comparison.png
│   │   ├── learning_curves.png
│   │   └── confusion_matrix.png
│   ├── metrics.json      # All metrics
│   └── results/          # Detailed results
└── .github/workflows/
    └── run-experiments.yml  # CI automation
```

---

## 🔧 Requirements

### System Requirements
- **Python:** 3.8 or higher
- **Git:** For repository management
- **Network:** Internet connection for API calls

### API Keys Required

**For Jules:**
```bash
export GITHUB_TOKEN=ghp_your_github_token
export GITHUB_OWNER=your_github_username
export JULES_API_KEY=your_jules_api_key
```

**For OpenHands:**
```bash
export GITHUB_TOKEN=ghp_your_github_token
export GITHUB_OWNER=your_github_username
export OPENHANDS_API_KEY=your_openhands_key
```

### Get API Keys
- **GitHub Token:** https://github.com/settings/tokens (requires `repo` scope)
- **Jules API Key:** https://jules.google → Settings → API Keys
- **OpenHands Key:** https://app.all-hands.dev → Settings

---

## 💰 Cost Estimates

### Jules
- **Free Tier:** 15 experiments/day - $0/month
- **Pro Tier:** 100 experiments/day - ~$30-50/month
- **Ultra Tier:** 300 experiments/day - ~$100-200/month

### OpenHands
- **Cloud:** ~$10-100/month (usage-based)
- **Self-hosted:** Your own LLM API costs

### GitHub Actions
- **Free:** 2,000 minutes/month
- **Additional:** $0.008/minute
- **Typical:** $0-20/month for moderate usage

**Total:** $0-300/month depending on usage

---

## 📚 Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Detailed setup guide
- **[CSV_FORMAT.md](docs/CSV_FORMAT.md)** - Input file format
- **[FIXES_APPLIED.md](FIXES_APPLIED.md)** - All 12 technical fixes applied
- **[TEST.md](docs/TEST.md)** - Testing guide

---

## 🧪 Testing

```bash
# Test CSV parsing
python -m pytest tests/integration/test_csv_parsing.py

# Test GitHub API
python -m pytest tests/integration/test_github.py

# Test provider APIs
python -m pytest tests/providers/test_jules_api.py
python -m pytest tests/providers/test_openhands_api.py
```

---

## 🎯 Example Use Cases

### Research
- **A/B Testing:** Compare different ML architectures
- **Hyperparameter Tuning:** Find optimal configurations
- **Algorithm Comparison:** Benchmark approaches
- **Reproducibility:** Automated reproducible experiments

### Development
- **Proof of Concepts:** Quickly validate ideas
- **Baseline Implementations:** Generate starting points
- **Code Generation:** Automate boilerplate
- **Documentation:** Auto-generate comprehensive docs

### Education
- **Learning Projects:** Build complete ML projects
- **Course Assignments:** Automated project scaffolding
- **Tutorials:** Generate working examples

---

## 🏆 Success Metrics

**Test Results (Current):**
- ✅ **Jules:** 100% success rate (multiple test runs)
- ✅ **OpenHands:** 100% success rate (tested successfully)
- ✅ **Artifacts committed:** Yes (Fix #11)
- ✅ **Visualizations generated:** Yes (Fix #12)
- ⭐ **Results quality:** 5/5 stars (publication-ready)

**Fixes Applied:** 12 major improvements
- GitHub file handling, branch detection, workflow syntax
- Repository indexing, error logging, timeout handling
- Artifacts preservation, results quality enhancement
- Connection resilience, prompt improvements

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Test thoroughly** - Run the test suite
2. **Document changes** - Update docs for any new features
3. **Follow style** - Match existing code patterns
4. **Test both providers** - Ensure Jules and OpenHands work

---

## 🐛 Troubleshooting

### Common Issues

**"Repository not indexed"** (Jules)
- Wait 20 seconds after repo creation
- Jules auto-retries up to 6 times

**"Connection aborted"**
- Auto-retry logic handles this (Fix #10)
- Transient network errors automatically recovered

**"Artifacts not showing up"**
- Fixed in v2.0 (Fix #11)
- New repos automatically commit artifacts

**"Results lack visualizations"**
- Fixed in v2.0 (Fix #12)
- Both providers now generate comprehensive visualizations

---

## 📊 Changelog

### v2.0 (Current) - Jules & OpenHands Only
- ✅ 12 major fixes applied
- ✅ Enhanced results quality (visualizations, deep analysis)
- ✅ Artifacts preservation
- ✅ Connection resilience
- ❌ Removed Augment (backend failures)
- ❌ Removed Cosine (architectural mismatch)

### v1.0 (Original)
- Initial 4-provider support
- Basic experiment orchestration

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🌟 Acknowledgments

- **Jules** by Google Labs - Excellent AI coding agent
- **OpenHands** by All-Hands - Flexible conversation-based agent
- **GitHub** - Platform for automation and hosting

---

## 📞 Support

- **Issues:** Open a GitHub issue
- **Documentation:** Check `docs/` directory
- **Technical Details:** See `FIXES_APPLIED.md`

---

**Ready to automate your experiments? Run `./run_experiments.sh` to get started!** 🚀
