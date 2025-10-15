# Provider Comparison Guide

Choose the right AI agent for your computational experiments.

## Quick Decision Tree

```
Do you need full programmatic control via API?
├─ YES → Jules (best REST API) or OpenHands (conversation API)
└─ NO
   ├─ Do you want CLI-driven automation?
   │  └─ YES → Augment (Auggie CLI)
   └─ Do you prefer UI/manual workflow?
      └─ YES → Cosine (CI monitoring)
```

## Detailed Comparison

### 🔧 Augment

**Best For:**
- Teams comfortable with CLI tools
- Need for secrets management (Remote Agent Secrets)
- Integration with external tools (MCP)
- IP allowlisting requirements

**Strengths:**
- Native AGENTS.md support
- Remote Agent with cloud VMs
- Powerful rules system (.augment/rules/)
- CLI automation well-documented

**Limitations:**
- Requires Node.js for CLI
- No direct REST API (CLI-based)
- Manual concurrency management

**Cost:** Subscription-based

**Automation Level:** ⭐⭐⭐⭐ (4/5) - Scriptable via CLI

**Use Case Example:**
- Research teams needing MCP for database access
- Projects requiring static IPs for data access
- Teams with existing CLI-based workflows

---

### 🌐 Jules

**Best For:**
- Maximum programmatic control
- Large-scale batch processing (50+ repos)
- Quota management requirements
- Plan approval workflows

**Strengths:**
- Complete REST API
- Full session management
- Plan approval system
- Automatic retry behavior
- Native AGENTS.md support

**Limitations:**
- Requires GitHub App pre-installation
- Quota tiers (Free: 15/day, Pro: 100/day)
- 10-30 second indexing delay for new repos

**Cost:** Tier-based (Free, Pro, Ultra)

**Automation Level:** ⭐⭐⭐⭐⭐ (5/5) - Full API control

**Use Case Example:**
- Automating 100+ experiment repos daily
- Need for plan approval before execution
- Integration into existing API-driven pipelines

---

### 🔄 Cosine

**Best For:**
- CI-centric development workflows
- Teams wanting manual oversight
- Need for Instant Sites (live demos)
- AutoDoc documentation generation

**Strengths:**
- No AGENTS.md needed (infers from code)
- Excellent CI log parsing
- Auto-iteration on CI failures
- Think mode for complex problems
- Instant Sites deployment

**Limitations:**
- No programmatic API (UI/CLI only)
- Requires manual repo import
- Manual CI step configuration
- Less suitable for batch automation

**Cost:** Subscription-based

**Automation Level:** ⭐⭐⭐ (3/5) - Semi-automated

**Use Case Example:**
- Teams wanting to review each experiment
- Projects needing live demo sites
- CI-first development culture

---

### 🤖 OpenHands

**Best For:**
- BYO model scenarios (Sonnet 4.x, GPT-4)
- Conversation-based development
- Microagent customization
- Open-source model requirements

**Strengths:**
- Cloud API available
- Conversation-based iteration
- Microagent system for repo-specific rules
- Recent AGENTS.md support
- BYO model keys (no markup)

**Limitations:**
- Conversation concurrency limits
- May pause older conversations
- Requires powerful models (Sonnet 4.x)

**Cost:** $20/month + model costs at vendor pricing

**Automation Level:** ⭐⭐⭐⭐ (4/5) - API-driven

**Use Case Example:**
- Teams with existing Anthropic/OpenAI credits
- Need for specific model control
- Conversation-style development preference

---

## Feature Matrix

| Feature | Augment | Jules | Cosine | OpenHands |
|---------|---------|-------|--------|-----------|
| **Full API Access** | ❌ (CLI) | ✅ | ❌ (UI) | ✅ |
| **AGENTS.md Support** | ✅ Native | ✅ Native | ❌ | ✅ Recent |
| **Batch Automation** | ✅ Good | ✅ Excellent | ⚠️ Manual | ✅ Good |
| **Plan Approval** | Via CLI | ✅ Built-in | N/A | N/A |
| **CI Monitoring** | ✅ | ✅ | ✅ Excellent | ✅ |
| **Secrets Management** | ✅ Advanced | Basic | Basic | Basic |
| **Concurrent Sessions** | Manual | ✅ Quota-based | Manual | ✅ Quota-based |
| **Cost Model** | Subscription | Tiered | Subscription | $20+usage |
| **Open Source** | ❌ | ❌ | ❌ | ✅ |

## Pipeline Type Suitability

### AI-Planned Experiments (has_experiments: False)

**Best Providers:**
1. **Jules** - Excellent at experiment design, full API control
2. **OpenHands** - Strong planning with powerful models
3. **Augment** - Good planning with Remote Agent
4. **Cosine** - Manual oversight during planning phase

### Pre-Defined Experiments (has_experiments: True)

**Best Providers:**
1. **Cosine** - Excels at executing fixed CI workflows
2. **Jules** - Fast execution with validation loops
3. **Augment** - Solid execution with retry logic
4. **OpenHands** - Good execution with conversation feedback

## Scale Considerations

### Small Scale (1-10 experiments)
**Recommended:** Any provider works well
- **Easiest:** Jules (API) or Cosine (UI)
- **Most Control:** Jules

### Medium Scale (10-50 experiments)
**Recommended:** Jules or Augment
- **Best API:** Jules (batch processing)
- **Best CLI:** Augment (scriptable)
- **Avoid:** Cosine (too manual)

### Large Scale (50+ experiments)
**Recommended:** Jules
- Full API control
- Quota management
- Async execution
- Best for automation

## Team Size Considerations

### Individual Developer
- **Jules** - Easy API automation
- **Cosine** - Good for learning/exploration

### Small Team (2-5 people)
- **Augment** - Shared CLI workflows
- **Jules** - API with plan approval
- **Cosine** - Manual oversight

### Large Team (5+ people)
- **Jules** - API integration into pipelines
- **OpenHands** - Conversation-based collaboration
- **Augment** - Enterprise features (SOC 2, ISO 42001)

## Integration Patterns

### CI/CD Pipeline Integration
**Best:** Jules (API) or Augment (CLI)
```python
# Example: Integrate into existing pipeline
from jules.orchestrator import JulesOrchestrator
orchestrator = JulesOrchestrator(config, api_key)
session_id = orchestrator.start_jules_session(repo, idea)
```

### Interactive Development
**Best:** Cosine (UI) or OpenHands (conversations)
- Review each step
- Manual trigger control
- Live feedback

### Fully Automated
**Best:** Jules (API)
- No human intervention
- Auto-approve plans
- Quota-based throttling

## Cost Analysis

### Augment
- **Model:** Subscription (~$20-40/month estimated)
- **Compute:** GitHub Actions (free tier available)
- **Total:** Subscription + GitHub Actions

### Jules
- **Model:** 
  - Free: $0 (15 tasks/day, 3 concurrent)
  - Pro: Price TBD (100 tasks/day, 15 concurrent)
  - Ultra: Price TBD (300 tasks/day, 60 concurrent)
- **Compute:** GitHub Actions (free tier available)
- **Total:** Tier pricing + GitHub Actions

### Cosine
- **Model:** Subscription pricing
- **Compute:** GitHub Actions (free tier available)
- **Total:** Subscription + GitHub Actions

### OpenHands
- **Model:** $20/month + BYO model keys at vendor pricing
  - Claude Sonnet 4.x: ~$3-15 per million tokens
  - GPT-4: Similar pricing
- **Compute:** GitHub Actions (free tier available)
- **Total:** $20 + model costs + GitHub Actions

**For 50 experiments:** Expect $50-200 depending on provider and model usage.

## Recommendation Summary

### Choose Augment If:
- You need enterprise compliance (SOC 2, ISO 42001)
- You want CLI-based automation
- You need Remote Agent Secrets or MCP
- You prefer declarative rules (.augment/rules/)

### Choose Jules If:
- You want full REST API control
- You're automating 50+ experiments
- You need plan approval workflows
- You want the best batch processing

### Choose Cosine If:
- You prefer manual oversight
- You want CI-first workflows
- You need Instant Sites for demos
- You want AutoDoc for documentation

### Choose OpenHands If:
- You want to bring your own model keys
- You prefer conversation-based development
- You need microagent customization
- You want open-source options

## Quick Start by Provider

### Fastest to Set Up: Jules
1. Get API key (2 minutes)
2. Install GitHub App (1 minute)
3. Run orchestrator (immediate)
**Total:** ~5 minutes

### Most Powerful: Augment
1. Install CLI (2 minutes)
2. Authenticate (2 minutes)
3. Get session token (1 minute)
4. Run orchestrator (immediate)
**Total:** ~7 minutes

### Most Flexible: OpenHands
1. Sign up (2 minutes)
2. Get API key (1 minute)
3. Install GitHub App (1 minute)
4. Configure model (2 minutes)
5. Run orchestrator (immediate)
**Total:** ~8 minutes

### Most Manual: Cosine
1. Install CLI (2 minutes)
2. Authenticate (1 minute)
3. Run orchestrator (immediate)
4. Manual import repos (5-10 minutes per repo)
5. Configure CI monitoring (2 minutes per repo)
**Total:** ~15-20 minutes per repo

## Final Recommendation

**For this project's goals (cloud-only, batch automation, dual pipelines):**

🥇 **First Choice:** **Jules**
- Complete API automation
- Best for batch processing
- Quota management built-in
- AGENTS.md support
- Dual pipeline prompts working perfectly

🥈 **Second Choice:** **Augment**
- Excellent CLI automation
- Good for scripting
- Enterprise-ready features
- Dual pipeline prompts working perfectly

🥉 **Third Choice:** **OpenHands**
- Good API automation
- Conversation-based flexibility
- BYO model cost control
- Dual pipeline prompts working perfectly

⚠️ **Fourth Choice:** **Cosine**
- Requires too much manual work for batch automation
- Better suited for individual projects
- Still excellent for CI monitoring

---

**Test all four providers with your ideas.csv to find your best fit!**

