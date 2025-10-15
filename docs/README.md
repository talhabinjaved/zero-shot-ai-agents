# AI Agent Experiment Orchestrators

## ⚠️ AI-Generated Code - Testing Required

**This repository was AI vibecoded in a single session.** While comprehensive and well-structured, it has **NOT been tested in production**. Expect bugs, API incompatibilities, and edge cases. See [TEST.md](TEST.md) for systematic debugging procedures.

---

A comprehensive repository for testing and comparing four leading AI coding agents: **Augment**, **Jules**, **Cosine**, and **OpenHands**.

This project provides automated orchestration for creating cloud-only experiment repositories that validate ideas through systematic computational experiments—without requiring any self-hosted compute infrastructure.

## What This System Does

Imagine you have 50 research ideas you want to validate computationally. Manually setting up 50 repositories, writing experiment code, configuring CI/CD, and generating documentation would take weeks.

**This system automates it:**

1. **Input:** CSV/Excel file with your ideas
2. **Process:** Orchestrator creates repos, configures AI agents, monitors execution
3. **Output:** 50 production-ready repositories with code, results, and investor-grade documentation

**Time savings:** Weeks → Hours  
**Compute cost:** $0 for you (GitHub Actions free tier + agent provider costs)  
**Setup complexity:** One Python script per provider

## Overview

Each provider has a dedicated orchestrator that:
1. Reads experiment ideas from CSV/Excel
2. Creates GitHub repositories with proper scaffolding
3. Configures the AI agent with experiment plans
4. Leverages GitHub Actions for heavy computation
5. Produces polished, investor-ready documentation

## Repository Structure

```
/
├── ideas.csv                    # Master list of experiment ideas
├── .gitignore                   # Python gitignore
├── README.md                    # This file
│
├── augment/                     # Augment orchestration
│   ├── orchestrator.py          # Main script using Auggie CLI
│   ├── AGENTS.md                # Agent instructions
│   ├── requirements.txt         # Python dependencies
│   └── templates/               # Repository templates
│       ├── experiments.yaml     # Experiment plan template
│       ├── harness.py           # CI execution harness
│       └── workflow.yml         # GitHub Actions workflow
│
├── jules/                       # Jules orchestration
│   ├── orchestrator.py          # Main script using Jules API
│   ├── AGENTS.md                # Agent instructions
│   ├── requirements.txt         # Python dependencies
│   └── templates/               # Repository templates
│       ├── experiments.yaml     # Experiment manifest template
│       ├── runner.py            # CI execution runner
│       └── workflow.yml         # GitHub Actions workflow
│
├── cosine/                      # Cosine orchestration
│   ├── orchestrator.py          # Main script (repo preparation)
│   ├── requirements.txt         # Python dependencies
│   └── templates/               # Repository templates
│       ├── experiments.yaml     # Experiment plan template
│       ├── executor.py          # CI execution executor
│       └── workflow.yml         # GitHub Actions workflow
│
└── openhands/                   # OpenHands orchestration
    ├── orchestrator.py          # Main script using OpenHands API
    ├── AGENTS.md                # Agent instructions
    ├── requirements.txt         # Python dependencies
    └── templates/               # Repository templates
        ├── microagent_repo.md   # Microagent instructions
        ├── experiments.yaml     # Experiment plan template
        ├── runner.py            # CI execution runner
        └── workflow.yml         # GitHub Actions workflow
```

## Pipeline Types

This system supports **two types of experiment pipelines**:

### 1. AI-Planned Experiments (`has_experiments: False`)
The AI agent designs the experiment plan from scratch:
- Analyzes the idea description
- Designs a comprehensive experiment strategy
- Creates ordered steps with dependencies
- Implements all necessary code
- Validates and iterates until completion

### 2. Pre-Defined Experiments (`has_experiments: True`)
The idea includes specific experiments to execute:
- Experiment plan provided in the CSV/Excel
- AI validates and implements the plan
- Focuses on faithful execution
- Still iterates on failures and optimizations

## CSV/Excel Format

Your `ideas.csv` or `ideas.xlsx` should have these columns:

```csv
title,has_experiments,idea,experiments
"Stock Market Analysis",False,"Build a model to predict stock movements using historical data",""
"Neural Architecture Comparison",True,"Compare CNN architectures for image classification","<YAML experiment plan here>"
```

**Required columns:**
- `title`: Experiment title (used for repo naming)
- `has_experiments`: Boolean (True/False, 1/0, yes/no, y/n)
- `idea`: Description of the idea to validate
- `experiments`: YAML experiment plan (required when `has_experiments` is True)

**Optional columns:**
- `data_url`: URL to dataset
- `requirements`: Additional Python packages (comma-separated)

## Setup & Usage

### Prerequisites

1. **GitHub Account**
   - Personal Access Token with `repo` scope
   - Set as `GITHUB_TOKEN` environment variable
   - Set `GITHUB_OWNER` to your username or organization

2. **Provider-Specific Requirements**

   **Augment:**
   - Install Auggie CLI: `npm i -g @augmentcode/auggie`
   - Authenticate: `auggie --login`
   - Get session token: `auggie --print-augment-token`
   - Set as `AUGMENT_SESSION_AUTH` environment variable

   **Jules:**
   - Create API key at [jules.google](https://jules.google)
   - Set as `JULES_API_KEY` environment variable
   - Install Jules GitHub App with "All repositories" access

   **Cosine:**
   - Install Cosine CLI: `brew install CosineAI/tap/cos`
   - Authenticate: `cos login`
   - Connect GitHub App
   - (No API key needed - uses manual import workflow)

   **OpenHands:**
   - Create account at [app.all-hands.dev](https://app.all-hands.dev)
   - Get API key from settings
   - Set as `OPENHANDS_API_KEY` environment variable
   - Install OpenHands Cloud GitHub App

### Running an Orchestrator

```bash
# 1. Navigate to provider directory
cd augment  # or jules, cosine, openhands

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Set required environment variables
export GITHUB_TOKEN="ghp_..."
export GITHUB_OWNER="your-username"
export AUGMENT_SESSION_AUTH="..."  # For Augment
# or
export JULES_API_KEY="..."         # For Jules
# or
export OPENHANDS_API_KEY="..."     # For OpenHands

# 4. Run the orchestrator
python orchestrator.py --input ../ideas.csv
```

### Command-Line Options

All orchestrators support similar options:

```bash
python orchestrator.py \
  --input ../ideas.csv \          # Input file (CSV or Excel)
  --max-concurrent 3 \             # Max concurrent operations
  --dry-run                        # Preview without executing
```

**Provider-specific options:**

- **Augment:** `--output-dir`, `--private`
- **Jules:** `--auto-approve` (skip plan approval)
- **Cosine:** `--trigger-workflows` (trigger initial CI validation)
- **OpenHands:** `--monitor-timeout` (conversation monitoring timeout)

## How Each Provider Works

### Augment
**Architecture:** CLI-driven with Remote Agent
- Creates repos and seeds with templates
- Uses Auggie CLI to invoke Augment Remote Agent
- Agent plans experiments, implements code, opens PRs
- Monitors GitHub Actions runs and iterates on failures
- Fully programmatic via CLI

**Key Features:**
- AGENTS.md support (native)
- Remote Agent Secrets for credentials
- MCP integration for external tools
- Static egress IPs for allowlisting

### Jules
**Architecture:** REST API with asynchronous sessions
- Creates repos and seeds with templates
- Starts Jules sessions via REST API
- Jules clones repo in Google-managed VM
- Generates plan, implements code, monitors CI
- Opens PRs automatically

**Key Features:**
- AGENTS.md support (native)
- Full REST API for automation
- Plan approval workflow
- Automatic retry on transient errors
- Quota management (Free/Pro/Ultra tiers)

### Cosine
**Architecture:** CLI/UI with CI monitoring
- Creates repos and seeds with templates
- User imports repos into Cosine workspace
- Configures CI step monitoring
- Cosine watches CI, reads logs, auto-iterates
- Opens/updates PRs until CI passes

**Key Features:**
- No AGENTS.md required (infers from code)
- CI-centric iteration model
- Auto-accept and Think modes
- Instant Sites for live demos
- AutoDoc for documentation

### OpenHands
**Architecture:** Cloud API with conversations
- Creates repos and seeds with templates
- Starts OpenHands Cloud conversations
- Agent implements in cloud workspace
- Monitors CI and iterates via conversation
- Opens PRs with comprehensive results

**Key Features:**
- AGENTS.md support (recently added)
- Microagent system for repo-specific guidance
- Cloud API for programmatic access
- BYO model keys (Sonnet 4.x recommended)
- Conversation-based feedback loops

## Cloud Compute Architecture

All providers use **GitHub Actions** for heavy computation:
- Standard runners: 4 vCPU, 16 GB RAM
- Larger runners: up to 96 vCPU, 384 GB RAM
- GPU runners available
- Can install any system/Python packages via apt-get/pip
- 6-hour timeout per job (can chain for longer runs)

**No self-hosting required.** All compute runs on GitHub's infrastructure.

## Experiment Workflow

### For Pre-Defined Experiments:
1. Orchestrator creates repo with provided experiment YAML
2. AI agent validates the plan
3. Implements required code and scripts
4. Executes experiments step-by-step
5. Validates against sanity checks
6. Generates comprehensive documentation

### For AI-Planned Experiments:
1. Orchestrator creates repo with idea description
2. AI agent analyzes the idea
3. Designs comprehensive experiment plan
4. Implements all code and infrastructure
5. Executes experiments step-by-step
6. Validates against sanity checks
7. Generates comprehensive documentation

## Key Features

### Sanity Checks
Every experiment step includes validation:
- File existence checks
- Metric threshold validation
- Statistical significance tests
- Automatic retry on failure

### Artifact Management
All results stored in structured directories:
- `artifacts/` or `results/` - Main outputs
- `logs/` - Execution logs
- `plots/` - Visualizations
- `state.json` - Current experiment state

### Documentation
Agents generate comprehensive documentation:
- README.md with hypothesis, methods, results
- RESULTS.md with detailed findings
- NEXT_STEPS.md with recommendations
- Error bars and statistical significance

## Comparison Matrix

| Feature | Augment | Jules | Cosine | OpenHands |
|---------|---------|-------|--------|-----------|
| **AGENTS.md Support** | ✅ Native | ✅ Native | ❌ Not needed | ✅ Recent |
| **API Automation** | CLI-based | ✅ REST API | ❌ UI/CLI only | ✅ REST API |
| **Plan Approval** | Via CLI | ✅ Optional | N/A | N/A |
| **CI Monitoring** | ✅ Via CLI | ✅ Via API | ✅ Built-in | ✅ Via API |
| **Auto-Iteration** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Concurrency Control** | Manual | ✅ Quota-based | Manual | ✅ Quota-based |
| **Cost Model** | Subscription | Tier-based | Subscription | $20/mo + BYO keys |

## Best Practices

1. **Start Small:** Test with 2-3 ideas before scaling to 50+
2. **Monitor Quotas:** Respect concurrent session limits
3. **Pin Dependencies:** Use exact versions in requirements.txt
4. **Cache Data:** Use GitHub Actions cache for datasets
5. **Break Long Jobs:** Split 6+ hour experiments into stages
6. **Use Larger Runners:** Scale resources as needed for intensive experiments
7. **Review PRs:** Always review generated code before merging

## Troubleshooting

### Repository Not Found in Jules/OpenHands
- Ensure GitHub App has access to new repos
- Wait 10-30 seconds for indexing
- Check GitHub App permissions

### Auggie CLI Not Found
- Install with: `npm i -g @augmentcode/auggie`
- Verify: `auggie --version`
- Check PATH includes npm global bin

### API Authentication Errors
- Verify environment variables are set
- Check token/key hasn't expired
- Ensure proper scopes/permissions

### CI Workflow Failures
- Check GitHub Actions logs
- Review `state.json` or sanity check results
- Agents will auto-iterate on failures

## Security Notes

- Never commit API keys or tokens to git
- Use GitHub Actions secrets for sensitive data
- Review generated code before merging
- Pin dependency versions to avoid supply chain attacks

## License

See individual provider documentation for their licensing terms.

## Contributing

This is a comparison/testing repository. For issues with individual providers:
- **Augment:** [docs.augmentcode.com](https://docs.augmentcode.com)
- **Jules:** [jules.google/docs](https://jules.google/docs)
- **Cosine:** [docs.cosine.sh](https://docs.cosine.sh)
- **OpenHands:** [docs.all-hands.dev](https://docs.all-hands.dev)

---

**Generated by AI Agent Orchestration System**  
Compare, contrast, and choose the best AI coding agent for your computational experiments.

---

## 🚀 Getting Started in 5 Minutes

**Quick test with Jules (recommended for first-time users):**

```bash
# 1. Clone and setup
git clone <this-repo>
cd openahands/jules
pip install -r requirements.txt

# 2. Set credentials
export GITHUB_TOKEN="ghp_your_token"
export GITHUB_OWNER="your-username"
export JULES_API_KEY="your_jules_key"

# 3. Test with simple idea
cat > quick_test.csv << 'EOF'
title,has_experiments,idea,experiments
"Quick Test",False,"Create a Python function that adds two numbers and test it",""
EOF

# 4. Dry run first
python orchestrator.py --input quick_test.csv --dry-run

# 5. Real run
python orchestrator.py --input quick_test.csv --auto-approve
```

**See:** [QUICKSTART.md](QUICKSTART.md) for detailed first-run instructions.

---

## 📖 Table of Contents

1. [What This System Does](#what-this-system-does)
2. [Architecture Overview](#architecture-overview)
3. [Pipeline Types Explained](#pipeline-types)
4. [Provider Deep Dives](#how-each-provider-works)
5. [CSV/Excel Format](#csvexcel-format)
6. [Setup & Installation](#setup--usage)
7. [Testing & Debugging](#testing--debugging)
8. [Advanced Usage](#advanced-usage)
9. [Comparison Matrix](#comparison-matrix)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [FAQ](#frequently-asked-questions)

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────┐
│   ideas.csv     │  Your experiment ideas (CSV/Excel)
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Orchestrator   │  Python script (one per provider)
│  (Local/Laptop) │  - Reads CSV
└────────┬────────┘  - Creates GitHub repos
         │           - Seeds templates
         │           - Starts AI agent
         │
         v
┌─────────────────┐
│   AI Agent      │  Provider's cloud service
│  (Cloud VM)     │  - Plans experiments (if needed)
└────────┬────────┘  - Implements code
         │           - Opens PRs
         │           - Monitors CI
         │
         v
┌─────────────────┐
│ GitHub Actions  │  Hosted compute (no cost to you)
│ (Cloud Runner)  │  - Runs experiments
└────────┬────────┘  - Validates results
         │           - Uploads artifacts
         │
         v
┌─────────────────┐
│  Final Repo     │  Production-ready output
│  (GitHub)       │  - Working code
└─────────────────┘  - Comprehensive README
                     - Results & visualizations
                     - Next steps documented
```

### Data Flow

1. **You provide:** CSV with titles, ideas, optional experiments
2. **Orchestrator creates:** GitHub repos with templates
3. **AI agent receives:** Instructions based on pipeline type
4. **Agent produces:** Experiment plan (if needed) + implementation
5. **GitHub Actions runs:** Experiments with sanity checks
6. **Agent iterates:** On failures until success
7. **You receive:** Polished repos with results

### Why This Architecture?

**No Self-Hosting Required:**
- AI agents run in provider's cloud (Augment VMs, Jules VMs, etc.)
- Heavy compute runs on GitHub Actions (free tier available)
- You only run a lightweight Python orchestrator locally

**Scalable:**
- Process 1 or 100 ideas with same script
- Concurrent execution with quota management
- Automatic retry and error recovery

**Provider-Agnostic:**
- Same CSV works for all providers
- Switch providers by changing directory
- Compare results across providers

---

## 🔀 Pipeline Types Explained

This system supports **two fundamentally different workflows:**

### Pipeline 1: AI-Planned Experiments

**When to use:** You have an idea but don't know how to validate it experimentally.

**What happens:**
1. You provide: "Build a recommendation engine using collaborative filtering"
2. AI analyzes the idea
3. AI designs: Data collection → Baseline → Main experiment → Analysis
4. AI implements all code
5. AI runs and validates
6. AI generates documentation

**Example CSV entry:**
```csv
title,has_experiments,idea,experiments
"Recommendation Engine",False,"Build a collaborative filtering recommender for movies. Compare user-based vs item-based approaches. Evaluate with RMSE and coverage metrics.",""
```

**AI's responsibilities:**
- ✅ Design experiment methodology
- ✅ Choose datasets
- ✅ Select evaluation metrics
- ✅ Implement all code
- ✅ Run experiments
- ✅ Interpret results

**Your responsibilities:**
- ✅ Provide clear idea description
- ✅ Review final PR
- ✅ Validate results make sense

---

### Pipeline 2: Pre-Defined Experiments

**When to use:** You know exactly what experiments to run.

**What happens:**
1. You provide: Complete YAML experiment plan
2. AI validates the plan
3. AI implements the code
4. AI executes as specified
5. AI validates results
6. AI generates documentation

**Example CSV entry:**
```csv
title,has_experiments,idea,experiments
"CNN Comparison",True,"Compare ResNet-18 vs EfficientNet-B0 on CIFAR-10","stop_on_fail: true
config:
  random_seed: 42
steps:
  - name: load_cifar10
    cmd: python scripts/load_data.py --dataset cifar10
    sanity:
      - type: file_exists
        path: artifacts/data/train.pkl
    timeout_minutes: 20
  - name: train_resnet
    cmd: python scripts/train.py --model resnet18 --epochs 50
    sanity:
      - type: json_value
        path: artifacts/resnet/metrics.json
        key: val_accuracy
        operator: '>'
        value: 0.75
    timeout_minutes: 180"
```

**AI's responsibilities:**
- ✅ Validate plan is sound
- ✅ Implement required code
- ✅ Execute plan faithfully
- ✅ Handle failures/retries
- ✅ Generate documentation

**Your responsibilities:**
- ✅ Provide complete experiment plan
- ✅ Define sanity checks
- ✅ Specify resource requirements
- ✅ Review final PR

---

## 🎯 When to Use Which Pipeline

### Use AI-Planned (has_experiments: False) When:

- ✅ You're exploring a new idea
- ✅ You're not sure what experiments to run
- ✅ You want the AI to design the methodology
- ✅ You trust the AI's judgment
- ✅ You're doing exploratory research

**Pros:**
- Less work for you
- AI may suggest experiments you didn't think of
- Good for brainstorming
- Faster to set up

**Cons:**
- Less control over exact experiments
- May not match your specific hypotheses
- Requires reviewing AI's plan
- More prone to AI misunderstanding

---

### Use Pre-Defined (has_experiments: True) When:

- ✅ You have a specific hypothesis to test
- ✅ You know the exact methodology
- ✅ You need reproducible results
- ✅ You're following a research protocol
- ✅ You want precise control

**Pros:**
- Exact control over experiments
- Reproducible methodology
- AI focuses on implementation quality
- Easier to validate correctness

**Cons:**
- More work upfront (writing YAML)
- Requires understanding experiment design
- Need to specify all steps explicitly
- More rigid (less AI creativity)

---

## 🧪 Experimental Validation Workflow

### Sanity Checks Explained

Every experiment step includes **sanity checks** - automated validations that must pass before proceeding.

**Why sanity checks matter:**
- Catch errors early (before wasting hours on invalid data)
- Ensure reproducibility (same checks every run)
- Enable auto-retry (AI knows what "success" means)
- Build confidence (objective validation)

**Common sanity check types:**

1. **File Existence**
   ```yaml
   sanity:
     - type: file_exists
       path: artifacts/model.pkl
   ```
   Verifies: Output file was created

2. **Metric Threshold**
   ```yaml
   sanity:
     - type: json_value
       path: artifacts/metrics.json
       key: accuracy
       operator: '>='
       value: 0.7
   ```
   Verifies: Model meets minimum performance

3. **Statistical Tests** (custom implementation)
   ```yaml
   sanity:
     - type: custom
       cmd: python scripts/validate_distribution.py
   ```
   Verifies: Results are statistically significant

### Retry Logic

When sanity checks fail:
1. **AI analyzes** the failure (reads logs, metrics)
2. **AI adjusts** code/parameters (fixes bugs, tunes hyperparams)
3. **AI retries** the step (up to configured limit)
4. **If still failing:** AI escalates (asks for human guidance or stops)

**Example retry scenario:**
```
Attempt 1: Model accuracy = 0.45 (fails >= 0.7 check)
→ AI: "Low accuracy, trying different learning rate"
Attempt 2: Model accuracy = 0.68 (still fails)
→ AI: "Still low, trying different architecture"
Attempt 3: Model accuracy = 0.73 (passes!)
→ AI: "Proceeding to next step"
```

---

## 🔬 Deep Dive: How Each Provider Handles Dual Pipelines

### Augment Implementation

**AI-Planned Mode:**
```
Orchestrator → Auggie CLI → "REQUIRES YOU TO PLAN THE EXPERIMENTS"
                           → Augment Remote Agent analyzes idea
                           → Generates experiments.yaml from scratch
                           → Implements code
                           → Opens PR with plan + implementation
```

**Pre-Defined Mode:**
```
Orchestrator → Seeds repo with provided YAML
           → Auggie CLI → "PRE-DEFINED EXPERIMENTS - execute faithfully"
                       → Augment validates plan
                       → Implements code
                       → Opens PR with implementation
```

**Unique aspects:**
- Uses `.augment/rules/` for additional guidance
- Remote Agent runs in Ubuntu 22.04 VM
- Can use MCP tools for external integrations
- Strong emphasis on AGENTS.md

---

### Jules Implementation

**AI-Planned Mode:**
```
Orchestrator → Jules API → create_session("DESIGN THE EXPERIMENT PLAN from scratch")
                        → Jules VM clones repo
                        → Generates plan
                        → Requires plan approval (optional)
                        → Implements code
                        → Opens PR
```

**Pre-Defined Mode:**
```
Orchestrator → Seeds repo with provided YAML
           → Jules API → create_session("PRE-DEFINED EXPERIMENTS")
                      → Jules validates plan
                      → Implements code
                      → Opens PR
```

**Unique aspects:**
- Full REST API control (sessions, activities, messages)
- Plan approval workflow (can auto-approve)
- Reads `results/state.json` for feedback
- Quota management across tiers

---

### Cosine Implementation

**AI-Planned Mode:**
```
Orchestrator → Creates repo
           → Generates COSINE_SETUP.md
           → User imports into Cosine
           → User creates task: "Design and execute experiments for {idea}"
           → Cosine plans + implements
           → Monitors CI
           → Auto-iterates on failures
```

**Pre-Defined Mode:**
```
Orchestrator → Seeds repo with provided YAML
           → User imports into Cosine
           → User creates task: "Execute experiments in experiments.yaml"
           → Cosine implements code
           → Monitors CI steps
           → Auto-iterates on failures
```

**Unique aspects:**
- No programmatic task creation (manual import)
- Excellent CI log parsing
- Doesn't use AGENTS.md (infers from code)
- Instant Sites for live demos

---

### OpenHands Implementation

**AI-Planned Mode:**
```
Orchestrator → OpenHands API → start_conversation("DESIGN THE EXPERIMENT PLAN")
                             → OpenHands analyzes idea
                             → Reads AGENTS.md + microagent
                             → Generates plan
                             → Implements code
                             → Opens PR
```

**Pre-Defined Mode:**
```
Orchestrator → Seeds repo with provided YAML
           → OpenHands API → start_conversation("PRE-DEFINED EXPERIMENTS")
                          → OpenHands validates plan
                          → Implements code
                          → Opens PR
```

**Unique aspects:**
- Conversation-based API
- Dual guidance (AGENTS.md + .openhands/microagents/repo.md)
- BYO model keys (Claude Sonnet 4.x recommended)
- Can send messages mid-conversation for feedback

---

## 📊 Detailed CSV/Excel Specification

### Column Descriptions

#### `title` (String, Required)
**Purpose:** Human-readable experiment title  
**Usage:** Repository naming (slugified), session titles, logging  
**Examples:**
- "Stock Market Prediction with LSTM"
- "A/B Test: Email Subject Lines"
- "CNN vs Transformer for Image Classification"

**Constraints:**
- Max 100 characters (will be truncated)
- Special characters will be removed for repo name
- Should be unique within the CSV

---

#### `has_experiments` (Boolean, Required)
**Purpose:** Determines pipeline type  
**Usage:** Routes to AI-planned vs pre-defined workflow

**Accepted values:**
| Input | Parsed As | Pipeline |
|-------|-----------|----------|
| `True`, `TRUE`, `true` | True | Pre-defined |
| `1` | True | Pre-defined |
| `yes`, `YES`, `y`, `Y` | True | Pre-defined |
| `False`, `FALSE`, `false` | False | AI-planned |
| `0` | False | AI-planned |
| `no`, `NO`, `n`, `N` | False | AI-planned |
| (empty) | False | AI-planned |

**Common mistakes:**
- ❌ Using "Yes" with no experiments provided
- ❌ Using "No" with experiments provided (ignored)
- ❌ Typos like "Ture" or "Flase"

---

#### `idea` (String, Required)
**Purpose:** Description of the idea to validate  
**Usage:** Agent prompt, repository README, documentation

**For AI-Planned (has_experiments: False):**
Be as detailed as possible:
```
"Build a recommendation engine using collaborative filtering. Compare user-based 
and item-based approaches. Use MovieLens-100K dataset. Evaluate with RMSE, 
precision@10, and coverage. Include popularity baseline for comparison. Test with 
different similarity metrics (cosine, Pearson)."
```

**For Pre-Defined (has_experiments: True):**
Can be concise (experiments YAML has the details):
```
"Compare optimizer algorithms (Adam, SGD, RMSprop) on CIFAR-10"
```

**Tips:**
- Mention datasets if specific ones needed
- Specify evaluation metrics
- Note constraints (time, compute, data size)
- Include baseline comparisons desired

---

#### `experiments` (String/YAML, Conditional)
**Purpose:** Pre-defined experiment plan  
**Required when:** `has_experiments: True`  
**Format:** Valid YAML experiment specification

**Full specification:** See [CSV_FORMAT.md](CSV_FORMAT.md)

**Minimal example:**
```yaml
stop_on_fail: true
steps:
  - name: data_prep
    cmd: python scripts/prep.py
    sanity:
      - type: file_exists
        path: data/train.csv
    timeout_minutes: 30
```

**Production example:**
```yaml
stop_on_fail: true
config:
  random_seed: 42
  output_dir: artifacts
  
steps:
  - name: environment_setup
    description: "Verify Python environment and dependencies"
    cmd: "python scripts/verify_env.py"
    sanity:
      - type: file_exists
        path: artifacts/env_check.json
      - type: json_value
        path: artifacts/env_check.json
        key: python_version
        operator: '>='
        value: "3.8"
    retry: 2
    timeout_minutes: 10
    
  - name: data_acquisition
    description: "Download and preprocess dataset"
    cmd: "python scripts/get_data.py --source kaggle --dataset imdb-reviews"
    inputs: []
    outputs:
      - artifacts/data/train.csv
      - artifacts/data/test.csv
    resources:
      cpu: 4
      memory_gb: 8
      expected_duration_minutes: 45
    sanity:
      - type: file_exists
        path: artifacts/data/train.csv
      - type: json_value
        path: artifacts/data/stats.json
        key: num_samples
        operator: '>'
        value: 10000
    retry: 3
    timeout_minutes: 60
    
  - name: baseline_experiment
    description: "Naive Bayes baseline"
    cmd: "python scripts/baseline_nb.py --data artifacts/data/ --output artifacts/baseline/"
    inputs:
      - artifacts/data/train.csv
      - artifacts/data/test.csv
    outputs:
      - artifacts/baseline/model.pkl
      - artifacts/baseline/metrics.json
    resources:
      cpu: 4
      memory_gb: 16
      expected_duration_minutes: 30
    sanity:
      - type: file_exists
        path: artifacts/baseline/metrics.json
      - type: json_value
        path: artifacts/baseline/metrics.json
        key: test_f1
        operator: '>'
        value: 0.6
    retry: 2
    timeout_minutes: 45
```

**See complete examples:** [CSV_FORMAT.md](CSV_FORMAT.md)

---

## 🧰 Advanced Usage

### Batch Processing Strategies

#### Strategy 1: Sequential (Safe)
```bash
python orchestrator.py --input ideas.csv --max-concurrent 1
```
- Processes one idea at a time
- Easy to debug
- Slow but safe

#### Strategy 2: Moderate Parallelism (Recommended)
```bash
python orchestrator.py --input ideas.csv --max-concurrent 3
```
- Balances speed and stability
- Respects free tier quotas
- Good for 10-50 ideas

#### Strategy 3: Maximum Speed (Advanced)
```bash
# Jules Pro: 15 concurrent
python orchestrator.py --input ideas.csv --max-concurrent 15

# OpenHands: depends on plan
python orchestrator.py --input ideas.csv --max-concurrent 10
```
- Fastest processing
- Requires paid tier
- Monitor quota closely

### Filtering Ideas

```bash
# Process only AI-planned experiments
python -c "
import pandas as pd
df = pd.read_csv('ideas.csv')
ai_planned = df[df['has_experiments'] == False]
ai_planned.to_csv('ai_planned_only.csv', index=False)
"
python orchestrator.py --input ai_planned_only.csv
```

### Resume After Failure

```bash
# If orchestrator crashes, remove completed repos from CSV
python -c "
import pandas as pd
df = pd.read_csv('ideas.csv')
completed_titles = ['Title1', 'Title2']  # Fill from logs
remaining = df[~df['title'].isin(completed_titles)]
remaining.to_csv('remaining.csv', index=False)
"
python orchestrator.py --input remaining.csv
```

### Custom Repository Naming

Modify orchestrator.py:
```python
# In create_experiment_repo():
repo_name = f"experiment-{idea.title[:30]}-{int(time.time())}"  # Add timestamp
# or
repo_name = f"{prefix}-{slugify(idea.title)}"  # Add prefix
```

---

## 🐛 Testing & Debugging

**⚠️ Critical:** This code is **untested**. Follow systematic testing procedure.

### Testing Order (DO NOT SKIP STEPS)

1. **Phase 1:** Environment validation → [TEST.md#phase-1](TEST.md#phase-1-environment-validation-15-minutes)
2. **Phase 2:** CSV parsing → [TEST.md#phase-2](TEST.md#phase-2-csv-parsing-tests-10-minutes)
3. **Phase 3:** GitHub API → [TEST.md#phase-3](TEST.md#phase-3-github-api-tests-20-minutes)
4. **Phase 4:** Unit tests → [TEST.md#phase-4](TEST.md#phase-4-orchestrator-unit-tests-30-minutes)
5. **Phase 5:** Single repo → [TEST.md#phase-5](TEST.md#phase-5-single-repo-test-30-minutes)
6. **Phase 6:** Agent integration → [TEST.md#phase-6](TEST.md#phase-6-agent-integration-tests-45-minutes)
7. **Phase 7:** End-to-end → [TEST.md#phase-7](TEST.md#phase-7-end-to-end-test-60-minutes)
8. **Phase 8:** Error handling → [TEST.md#phase-8](TEST.md#phase-8-error-handling-tests-30-minutes)
9. **Phase 9:** Debug failures → [TEST.md#phase-9](TEST.md#phase-9-debugging-specific-failures)
10. **Phase 10:** Batch test → [TEST.md#phase-10](TEST.md#phase-10-full-batch-test-optional-2-hours)

**Estimated debugging time:** 4-8 hours

**See complete testing guide:** [TEST.md](TEST.md)

### Quick Debugging Commands

```bash
# Check CSV format
python -c "import pandas as pd; print(pd.read_csv('ideas.csv').head())"

# Test GitHub API
python -c "import os, requests; r = requests.get('https://api.github.com/user', headers={'Authorization': f'Bearer {os.environ[\"GITHUB_TOKEN\"]}'}); print(r.status_code, r.json().get('login'))"

# Test dependencies
python -c "import pandas, requests, yaml; print('OK')"

# Validate YAML in CSV
python -c "import pandas as pd, yaml; df = pd.read_csv('ideas.csv'); [print(f'{i}: {yaml.safe_load(row.experiments) if pd.notna(row.experiments) and row.experiments else \"empty\"}') for i, row in df.iterrows()]"

# Check environment variables
env | grep -E 'GITHUB_|AUGMENT_|JULES_|OPENHANDS_'
```

### Most Likely Bugs

Based on AI-generated code patterns:

1. **API endpoints outdated** (404 errors)
   - Fix: Check provider docs for current endpoints
   - Update: API base URLs in orchestrator.py

2. **Authentication header format** (401 errors)
   - Fix: Check docs for current auth format
   - Update: Headers in Client classes

3. **Response format changes** (KeyError)
   - Fix: Check API response structure
   - Update: Response parsing logic

4. **Template file paths** (FileNotFoundError)
   - Fix: Verify running from correct directory
   - Update: Path construction in `_copy_template_files()`

5. **CSV encoding issues** (UnicodeDecodeError)
   - Fix: Specify encoding in pd.read_csv()
   - Try: `pd.read_csv('ideas.csv', encoding='utf-8')`

---

## 🔍 Monitoring & Observability

### Logging Output Explained

**Normal execution:**
```
2025-10-14 12:00:00 - INFO - Loaded 3 experiment ideas
2025-10-14 12:00:00 - INFO -   - 1 with pre-defined experiments
2025-10-14 12:00:00 - INFO -   - 2 requiring AI planning
2025-10-14 12:00:05 - INFO - Created repository: user/idea-1
2025-10-14 12:00:10 - INFO - Seeding repository: user/idea-1
2025-10-14 12:00:15 - INFO - Starting Jules session for user/idea-1
2025-10-14 12:00:15 - INFO -   Pipeline type: AI planning required
2025-10-14 12:00:20 - INFO - Created Jules session: sessions/abc123
```

**Error patterns:**
```
❌ ERROR - Failed to create repository: 422
   → Repository name conflict or validation failed

❌ ERROR - API authentication failed: 401
   → Invalid or expired API key

⚠️  WARNING - Repository already exists, using existing
   → Not an error, continuing with existing repo

❌ ERROR - Template file not found: templates/workflow.yml
   → Running from wrong directory or missing template
```

### Provider-Specific Monitoring

**Augment:**
- CLI output in logs
- Check https://augmentcode.com for agent status
- PR notifications via GitHub

**Jules:**
- Session IDs in logs
- Monitor at https://jules.google
- Check quota usage in dashboard

**Cosine:**
- Repository URLs in logs
- Import repos manually
- Monitor CI in Cosine dashboard

**OpenHands:**
- Conversation IDs in logs
- Monitor at https://app.all-hands.dev
- Check conversation status

---

## 🎓 Learning Path: From Zero to Production

### Week 1: Single Provider, AI-Planned

1. **Day 1:** Setup Jules environment
2. **Day 2:** Test with 1 simple idea
3. **Day 3:** Debug issues, refine prompts
4. **Day 4:** Test with 3 ideas
5. **Day 5:** Review generated code quality

**Goal:** Understand AI-planned workflow completely

### Week 2: Single Provider, Pre-Defined

1. **Day 1:** Design experiment YAML manually
2. **Day 2:** Test with 1 pre-defined experiment
3. **Day 3:** Debug YAML validation
4. **Day 4:** Test with 3 pre-defined experiments
5. **Day 5:** Compare quality vs AI-planned

**Goal:** Master pre-defined workflow

### Week 3: Multi-Provider Comparison

1. **Day 1:** Setup Augment
2. **Day 2:** Run same idea on Augment and Jules
3. **Day 3:** Setup OpenHands
4. **Day 4:** Compare all three results
5. **Day 5:** Document findings

**Goal:** Choose best provider for your needs

### Week 4: Scale to Production

1. **Day 1:** Prepare 20-50 real ideas
2. **Day 2:** Batch process with chosen provider
3. **Day 3:** Monitor and debug
4. **Day 4:** Review all generated repos
5. **Day 5:** Merge best implementations

**Goal:** Production-scale automation

---

## 📚 Complete Documentation Index

### Getting Started
- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup guide
- [TEST.md](TEST.md) - **Systematic testing & debugging (START HERE)**
- [CSV_FORMAT.md](CSV_FORMAT.md) - Input format specification
- [env.example](env.example) - Environment variable template

### Technical Documentation
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Code implementation details
- [PROVIDER_COMPARISON.md](PROVIDER_COMPARISON.md) - Choosing the right provider
- [COMPLETION_REPORT.md](COMPLETION_REPORT.md) - Quality metrics & verification

### Provider-Specific
- `augment/AGENTS.md` - Augment agent instructions
- `jules/AGENTS.md` - Jules agent instructions
- `openhands/AGENTS.md` - OpenHands agent instructions
- `openhands/templates/microagent_repo.md` - OpenHands microagent spec

### Planning
- [plan.md](plan.md) - Original system design document

---

## ⚡ Performance & Scalability

### Benchmarks (Estimated)

**Single idea processing:**
- Repository creation: ~5-10 seconds
- Template seeding: ~10-20 seconds
- Agent session start: ~5-10 seconds
- **Total orchestrator time:** ~30-60 seconds per idea

**Agent execution time:**
- AI-planned simple idea: 5-15 minutes
- AI-planned complex idea: 15-45 minutes
- Pre-defined simple: 10-30 minutes
- Pre-defined complex: 30-120 minutes

**Batch processing:**
- 10 ideas (concurrent=3): ~20-40 minutes
- 50 ideas (concurrent=10): ~60-180 minutes
- 100 ideas (concurrent=15): ~120-360 minutes

### Resource Usage

**Orchestrator (local):**
- CPU: <10%
- Memory: ~100-500 MB
- Network: Minimal (API calls only)

**GitHub Actions (cloud):**
- Standard runner: 4 vCPU, 16 GB RAM
- Larger runner: up to 96 vCPU, 384 GB RAM
- Storage: Artifacts cached/uploaded

**Agent (cloud):**
- Augment: Remote Agent VM
- Jules: Google-managed VM
- Cosine: Platform-managed
- OpenHands: Cloud workspace

### Cost Estimates

**GitHub Actions (free tier):**
- 2,000 minutes/month free (private repos)
- Unlimited for public repos
- $0.008/minute after free tier

**Estimated for 50 experiments:**
- If each uses 60 min: 3,000 minutes = $8
- With free tier: $0-8

**Provider costs:**
- Augment: Subscription (~$20-40/mo)
- Jules: Free (15/day) to Pro (100/day)
- Cosine: Subscription
- OpenHands: $20/mo + model costs (~$10-50)

**Total for 50 experiments:** $30-100

---

## 🔐 Security & Compliance

### Credential Management

**DO:**
- ✅ Use environment variables
- ✅ Keep .env in .gitignore
- ✅ Use GitHub Secrets for CI
- ✅ Rotate credentials regularly
- ✅ Use minimal required scopes

**DON'T:**
- ❌ Commit credentials to git
- ❌ Share credentials via Slack/email
- ❌ Use overly permissive tokens
- ❌ Log credentials
- ❌ Hardcode in source

### Data Privacy

**Generated repos may contain:**
- Experiment results (potentially sensitive)
- Datasets (check licensing)
- Model outputs (may include training data)

**Recommendations:**
- Use private repositories
- Review data handling in generated code
- Don't use confidential data without approval
- Check compliance (GDPR, HIPAA, etc.)

### Code Review

**Always review generated code before merging:**
- Check for security vulnerabilities
- Verify data handling is appropriate
- Ensure dependencies are from trusted sources
- Look for hardcoded credentials (shouldn't be any)
- Validate experiment methodology

### Compliance Features

**Augment:**
- SOC 2 Type II certified
- ISO/IEC 42001 (AI governance)
- Trust center: https://trust.augmentcode.com

**Jules:**
- Google's security standards
- Enterprise options available

**Cosine:**
- Check provider for details

**OpenHands:**
- Open source option available
- BYO model (data stays with your provider)

---

## ❓ Frequently Asked Questions

### General Questions

**Q: Which provider should I start with?**  
A: **Jules**. It has the most complete REST API, best documentation, and easiest automation. See [PROVIDER_COMPARISON.md](PROVIDER_COMPARISON.md).

**Q: Can I use this with public repositories?**  
A: Yes, just be aware that experiment results will be public. Modify orchestrator to set `private=False`.

**Q: How much does this cost?**  
A: Provider subscription ($0-40/month) + GitHub Actions ($0-8 for 50 experiments with free tier) + model costs if BYO keys. **Total: $20-100/month** depending on provider.

**Q: Can I run experiments locally instead of GitHub Actions?**  
A: Not recommended. The whole point is cloud-only compute. But you could modify workflows to run locally.

### Technical Questions

**Q: What if my experiments need GPUs?**  
A: Use GitHub's GPU runners in the workflow.yml files. Change `runs-on: ubuntu-latest` to `runs-on: ubuntu-latest-gpu`. Costs ~$0.07/minute.

**Q: Can experiments run longer than 6 hours?**  
A: GitHub Actions has a 6-hour limit. Split long experiments into multiple jobs or use job chaining.

**Q: What if I have 1000 ideas?**  
A: Process in batches of 50-100. Monitor quotas. Consider Jules Ultra (300 tasks/day, 60 concurrent).

**Q: Can I customize the experiment templates?**  
A: Yes! Edit files in `<provider>/templates/`. Changes apply to all future repos.

**Q: Will this work with GitLab or Bitbucket?**  
A: No, currently GitHub-only. Would need significant refactoring.

### Debugging Questions

**Q: Why does my repository have no files?**  
A: Check `put_file()` responses. Likely a GitHub API error. Run Phase 3 tests in TEST.md.

**Q: Why isn't the agent starting?**  
A: Check provider logs/dashboard. Verify GitHub App access. Wait 30 seconds for indexing.

**Q: Why do I get "403 Forbidden"?**  
A: GitHub token lacks permissions. Ensure 'repo' scope. Check org membership.

**Q: What if experiments.yaml has syntax errors?**  
A: Run Phase 2.2 test in TEST.md to validate YAML before running orchestrator.

---

## 🤝 Contributing & Support

### Reporting Bugs

1. Run through TEST.md debugging phases
2. Collect logs from orchestrator.log
3. Note exact error message and stack trace
4. Provide CSV row that failed
5. Open GitHub issue with details

### Fixing Bugs

1. Create branch: `fix/provider-specific-issue`
2. Fix and test with TEST.md procedures
3. Update TEST.md if new test needed
4. Submit PR with explanation

### Adding Features

Potential enhancements:
- Progress bars with `tqdm`
- Concurrent processing with `ThreadPoolExecutor`
- Cost estimation before running
- Results dashboard
- Email notifications
- Webhook integration
- More sanity check types

---

## 📜 License & Attribution

### Code License
This orchestration code: MIT License (or your choice)

### Provider Licenses
- **Augment:** Check augmentcode.com
- **Jules:** Check jules.google
- **Cosine:** Check cosine.sh
- **OpenHands:** Check all-hands.dev

### Attribution
Prompts and architecture adapted from official provider documentation:
- Augment: https://docs.augmentcode.com
- Jules: https://jules.google/docs + https://developers.google.com/jules/api
- Cosine: https://docs.cosine.sh
- OpenHands: https://docs.all-hands.dev

### Disclaimer

**This code is provided AS-IS with NO WARRANTY.**

- AI-generated code, not production-tested
- API endpoints may have changed
- Provider features may have evolved
- Use at your own risk
- Always review generated code
- Test thoroughly before production use

---

## 🎯 Success Stories (Future)

*This section will be updated as users test and deploy the system.*

**Expected outcomes after debugging:**
- ✅ Automated creation of 50+ experiment repos
- ✅ AI-generated experiment plans
- ✅ Working code with tests
- ✅ Comprehensive documentation
- ✅ Reproducible results
- ✅ Time savings of 80-95%

**Share your success story!** Open an issue or PR to add your experience.

---

## 📞 Getting Help

### Documentation Priority

1. **Having issues?** → Start with [TEST.md](TEST.md)
2. **CSV questions?** → See [CSV_FORMAT.md](CSV_FORMAT.md)
3. **Quick setup?** → See [QUICKSTART.md](QUICKSTART.md)
4. **Choosing provider?** → See [PROVIDER_COMPARISON.md](PROVIDER_COMPARISON.md)
5. **API questions?** → Check provider's official docs

### Support Channels

**For orchestrator bugs:**
- GitHub Issues in this repo

**For provider API/features:**
- Augment: https://docs.augmentcode.com
- Jules: https://jules.google/docs
- Cosine: https://docs.cosine.sh
- OpenHands: https://docs.all-hands.dev

**For GitHub Actions:**
- https://docs.github.com/actions

---

## 🏆 Acknowledgments

This system synthesizes best practices from:
- AI coding agent communities
- Research automation workflows
- CI/CD optimization patterns
- Experiment tracking systems

**Inspired by:** The vision of AI-automated research and the potential for computational idea validation at scale.

**Built with:** Claude (Anthropic), extensive documentation research, and systematic software engineering principles.

---

**Ready to start testing?** → [TEST.md](TEST.md)  
**Want quick setup?** → [QUICKSTART.md](QUICKSTART.md)  
**Need help choosing?** → [PROVIDER_COMPARISON.md](PROVIDER_COMPARISON.md)

---

*Last updated: 2025-10-14*  
*Version: 1.0.0-alpha (untested)*  
*Status: AI-generated, requires testing and debugging*
