# Provider Test Experiment: Sentiment Analysis Showdown

## 🎯 Objective

Compare **Jules** vs **OpenHands** on a real-world ML experiment: building and comparing 3 different sentiment analysis approaches.

This experiment tests the AI agents' ability to:
- ✅ Plan comprehensive experiments from scratch
- ✅ Implement multiple ML approaches (traditional + modern)
- ✅ Generate publication-quality visualizations
- ✅ Perform deep error analysis
- ✅ Provide actionable insights

---

## 📊 Experiment Design

### The Task
**Sentiment Analysis on Movie Reviews**

Build 3 different approaches and compare them:

1. **Baseline: Traditional ML**
   - TF-IDF vectorization
   - Logistic Regression classifier
   - Fast, interpretable, simple

2. **Advanced: Pre-trained Embeddings**
   - Pre-trained BERT embeddings
   - Linear classifier on top
   - Better representations without fine-tuning

3. **State-of-the-art: Fine-tuned Transformer**
   - Fine-tuned DistilBERT
   - End-to-end training
   - Maximum performance

### Dataset
- **Source:** IMDB Movie Reviews
- **Size:** 5,000 reviews (subset for speed)
- **Classes:** Positive/Negative sentiment
- **Split:** 80% train / 20% test

### Metrics to Compare
- **Accuracy** - Overall correctness
- **F1-Score** - Balance of precision/recall
- **Inference Time** - Prediction speed
- **Model Size** - Memory footprint
- **Error Analysis** - What each model gets wrong

---

## 📈 Expected Visualizations

The AI agents should generate:

### 1. Model Comparison Bar Chart
- Side-by-side accuracy, F1-score
- Color-coded by approach
- Error bars showing confidence

### 2. ROC Curves
- All 3 models on same plot
- AUC scores in legend
- Demonstrates discrimination ability

### 3. Confusion Matrices
- One for each model (3 total)
- Shows FP, FN, TP, TN patterns
- Identify systematic errors

### 4. Inference Time Comparison
- Bar chart or box plot
- Time per prediction
- Throughput comparison

### 5. Error Analysis Plots
- Review length vs accuracy
- Sentiment intensity vs accuracy
- Examples of failures

### 6. Learning Curves (for fine-tuned model)
- Training vs validation loss
- Shows convergence and overfitting

---

## 🎯 Success Criteria

### Jules Should:
✅ Design complete experiment plan with all 3 models  
✅ Implement baseline, pre-trained, and fine-tuned approaches  
✅ Generate all 6 visualization types  
✅ Provide error analysis with specific examples  
✅ Create comprehensive RESULTS.md  
✅ Complete in <2 hours  

### OpenHands Should:
✅ Design complete experiment plan with all 3 models  
✅ Implement baseline, pre-trained, and fine-tuned approaches  
✅ Generate all 6 visualization types  
✅ Provide error analysis with specific examples  
✅ Create comprehensive RESULTS.md  
✅ Complete in <2 hours  

---

## 🔍 What This Tests

### Planning Ability
- Can AI design a complete ML experiment from scratch?
- Does it include proper train/test splits?
- Are baselines and controls included?
- Is the experiment rigorous and fair?

### Implementation Skills
- Can AI implement traditional ML (TF-IDF + LogReg)?
- Can AI use pre-trained models (BERT embeddings)?
- Can AI fine-tune transformers (DistilBERT)?
- Is code modular and well-documented?

### Visualization Quality
- Are plots publication-ready?
- Do visualizations tell a story?
- Are all key comparisons shown?
- Are error bars and statistics included?

### Analysis Depth
- Does AI explain WHY one model outperforms?
- Are failure cases analyzed?
- Are trade-offs discussed (speed vs accuracy)?
- Are next steps specific and actionable?

---

## 📝 How to Run This Test

### Option 1: Test Jules

```bash
cd /Users/talhadev/Projects/zero-shot-ai-agents
./run_experiments.sh

# Select: 1 (Jules)
# Input file: test_providers.csv
# Continue: y
```

**Monitor:**
- Visit https://jules.google
- Watch Jules plan and execute
- Check repo: `<username>/sentiment-analysis-showdown`

### Option 2: Test OpenHands

```bash
cd /Users/talhadev/Projects/zero-shot-ai-agents
./run_experiments.sh

# Select: 2 (OpenHands)
# Input file: test_providers.csv
# Continue: y
```

**Monitor:**
- Visit https://app.all-hands.dev
- Watch OpenHands plan and execute
- Check repo: `<username>/sentiment-analysis-showdown`

### Option 3: Test Both (Comparison)

Run Jules first, then OpenHands (or vice versa) with different repo names:

```csv
# For Jules
title,has_experiments,idea
Sentiment Analysis Showdown Jules,False,"[same idea]"

# For OpenHands
title,has_experiments,idea
Sentiment Analysis Showdown OpenHands,False,"[same idea]"
```

Then compare their:
- Experiment plans
- Code quality
- Visualization quality
- Analysis depth
- Execution time
- Final results

---

## 🏆 Expected Outcomes

### Repository Contents

After completion, each repo should have:

```
sentiment-analysis-showdown/
├── README.md                    # Professional documentation
├── RESULTS.md                   # Comprehensive findings
│
├── experiments/
│   └── experiments.yaml         # Complete experiment plan
│
├── scripts/
│   ├── setup.py                # Environment setup
│   ├── data_prep.py            # Download & preprocess IMDB
│   ├── baseline_tfidf.py       # TF-IDF + LogReg
│   ├── bert_embeddings.py      # Pre-trained BERT + Linear
│   ├── finetune_distilbert.py  # Fine-tuned DistilBERT
│   └── analysis.py             # Generate all plots
│
├── artifacts/
│   ├── plots/
│   │   ├── model_comparison.png
│   │   ├── roc_curves.png
│   │   ├── confusion_matrices.png
│   │   ├── inference_time.png
│   │   ├── error_analysis.png
│   │   └── learning_curves.png
│   │
│   ├── metrics.json            # All metrics
│   ├── baseline_metrics.json
│   ├── bert_metrics.json
│   └── distilbert_metrics.json
│
└── .github/workflows/
    └── run-experiments.yml     # CI automation
```

### RESULTS.md Should Include

**1. Executive Summary**
- Best model: DistilBERT (93% accuracy)
- Best speed: TF-IDF (0.5ms/prediction)
- Best trade-off: BERT embeddings (89% acc, 2ms/prediction)

**2. Visualizations (All 6)**
- Embedded with `![Title](artifacts/plots/chart.png)`

**3. Model Comparison Table**
```markdown
| Model | Accuracy | F1-Score | Inference Time | Model Size |
|-------|----------|----------|----------------|------------|
| TF-IDF + LogReg | 87% | 0.86 | 0.5ms | 2MB |
| BERT + Linear | 91% | 0.90 | 2.1ms | 420MB |
| Fine-tuned DistilBERT | 93% | 0.93 | 8.5ms | 250MB |
```

**4. Deep Analysis**
- Error analysis: What reviews each model gets wrong
- Trade-offs: Speed vs accuracy discussion
- Statistical significance: p-values for differences

**5. Next Steps**
- Specific recommendations (e.g., "Try RoBERTa for +2% accuracy")
- Expected improvements with justification

---

## 🎨 Why This Is A Good Test

### ✅ Real-World Relevance
- Sentiment analysis is a common NLP task
- Multi-model comparison is standard practice
- Trade-offs (speed/accuracy) matter in production

### ✅ Comprehensive Coverage
- Traditional ML (TF-IDF)
- Transfer learning (pre-trained BERT)
- Fine-tuning (DistilBERT)
- Covers the spectrum of approaches

### ✅ Clear Success Metrics
- Quantitative: Accuracy, F1, speed, size
- Qualitative: Error analysis, insights
- Visual: 6 different plot types

### ✅ Reasonable Scope
- 5,000 reviews (manageable size)
- DistilBERT (smaller than full BERT)
- Should complete in <2 hours

### ✅ Tests Enhanced Capabilities (Fix #12)
- Requires multiple visualizations
- Needs deep error analysis
- Demands specific insights
- Perfect test for our improvements!

---

## 📊 Comparison Criteria

After both Jules and OpenHands complete, compare:

### 1. Planning Quality (10 points)
- Experiment design rigor
- Baseline inclusion
- Sanity checks defined
- Resource estimation

### 2. Code Quality (10 points)
- Modularity and organization
- Documentation and comments
- Error handling
- Test coverage

### 3. Visualization Quality (10 points)
- All 6 plots generated?
- Publication-ready?
- Properly labeled?
- Tells a story?

### 4. Analysis Depth (10 points)
- Error analysis specificity
- Statistical significance
- Trade-off discussion
- Next steps actionable?

### 5. Execution Success (10 points)
- Completed without errors?
- All sanity checks passed?
- Results make sense?
- Time to completion?

**Total: /50 points per provider**

---

## 💡 Expected Insights

The AI agents should discover:

1. **DistilBERT wins on accuracy** (+6% over baseline)
2. **TF-IDF wins on speed** (17x faster than DistilBERT)
3. **BERT embeddings are the sweet spot** (Good accuracy + reasonable speed)
4. **Short reviews** favor traditional ML (less context needed)
5. **Long reviews** favor transformers (better long-range dependencies)
6. **Sarcasm and irony** confuse all models (but less so DistilBERT)

---

## 🚀 Ready to Test?

```bash
cd /Users/talhadev/Projects/zero-shot-ai-agents
./run_experiments.sh
```

**Input file:** `test_providers.csv`  
**Provider:** Choose Jules (1) or OpenHands (2)  
**Then:** Watch the magic happen! ✨

---

**This experiment perfectly showcases the enhanced capabilities from Fix #12:**
- 📊 Multiple visualizations (6 types!)
- 🔬 Deep error analysis
- 📈 Statistical comparisons
- 🎯 Actionable insights

**Let's see which AI agent produces the best results!** 🏆

