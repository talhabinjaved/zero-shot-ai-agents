# CSV/Excel Format Specification

This document describes the expected format for the `ideas.csv` or `ideas.xlsx` file used by all orchestrators.

## Column Specification

### Required Columns

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `title` | String | Experiment title (used for repo naming) | "Stock Market Prediction Model" |
| `has_experiments` | Boolean | Whether experiments are pre-defined | True, False, 1, 0, yes, no, y, n |
| `idea` | String | Description of the idea to validate | "Build a model to predict stock movements..." |
| `experiments` | String/YAML | Pre-defined experiment plan (required if has_experiments=True) | See below for YAML format |

### Optional Columns

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `data_url` | String | URL to dataset | "https://example.com/data.zip" |
| `requirements` | String | Additional Python packages (comma-separated) | "tensorflow, keras, scikit-learn" |

## Boolean Parsing for `has_experiments`

The orchestrators accept multiple formats for the `has_experiments` column:

- **True values:** `True`, `1`, `yes`, `y`, `TRUE`, `YES` (case-insensitive)
- **False values:** `False`, `0`, `no`, `n`, `FALSE`, `NO` (case-insensitive)
- **Empty/missing:** Defaults to `False`

## Pipeline Types

### Type 1: AI-Planned Experiments (`has_experiments: False`)

The AI agent designs the experiment plan from scratch.

**Example CSV row:**
```csv
title,has_experiments,idea,experiments
"Stock Market Analysis",False,"Build a model to predict stock movements using historical data. Test LSTM vs Transformer architectures.",""
```

**What happens:**
1. Orchestrator creates repo with idea description
2. AI agent analyzes the idea
3. AI designs comprehensive experiment plan
4. AI creates experiments.yaml with ordered steps
5. AI implements all code and runs experiments
6. AI generates final documentation

### Type 2: Pre-Defined Experiments (`has_experiments: True`)

You provide the experiment plan; AI implements and executes it.

**Example CSV row:**
```csv
title,has_experiments,idea,experiments
"Neural Architecture Comparison",True,"Compare CNN architectures for CIFAR-10","stop_on_fail: true
config:
  random_seed: 42
  output_dir: artifacts
steps:
  - name: data_loading
    description: Load CIFAR-10 dataset
    cmd: python scripts/load_data.py
    sanity:
      - type: file_exists
        path: artifacts/data/train.pkl
    retry: 2
    timeout_minutes: 20
  - name: train_baseline_cnn
    description: Train baseline CNN
    cmd: python scripts/train_baseline.py --epochs 10
    sanity:
      - type: json_value
        path: artifacts/baseline/metrics.json
        key: accuracy
        operator: '>'
        value: 0.6
    retry: 3
    timeout_minutes: 120"
```

**What happens:**
1. Orchestrator creates repo with provided experiment YAML
2. AI agent validates the plan
3. AI implements the required code
4. AI executes experiments step-by-step
5. AI validates against sanity checks
6. AI generates final documentation

## Experiment YAML Format

When providing pre-defined experiments (`has_experiments: True`), use this YAML structure:

```yaml
# Global configuration
stop_on_fail: true  # Halt on first failure

config:
  random_seed: 42
  log_level: INFO
  output_dir: artifacts  # or results for Jules
  cache_dir: .cache

# Ordered list of experiment steps
steps:
  - name: step_identifier
    description: "Human-readable description"
    cmd: "python scripts/step_script.py --arg value"
    inputs:
      - path/to/input1.csv
      - path/to/input2.pkl
    outputs:
      - artifacts/output1.json
      - artifacts/plots/figure1.png
    resources:
      cpu: 4
      memory_gb: 16
      expected_duration_minutes: 60
    sanity:
      - type: file_exists
        path: artifacts/output1.json
      - type: json_value
        path: artifacts/metrics.json
        key: accuracy
        operator: '>='
        value: 0.7
    retry: 3
    timeout_minutes: 90

# Optional post-processing
post_process:
  - name: generate_readme
    cmd: "python scripts/generate_readme.py"
    timeout_minutes: 10
```

### Sanity Check Types

**File Existence:**
```yaml
sanity:
  - type: file_exists
    path: artifacts/output.json
```

**JSON Value Validation:**
```yaml
sanity:
  - type: json_value
    path: artifacts/metrics.json
    key: accuracy
    operator: '>='  # Operators: >=, >, <=, <, ==, !=
    value: 0.8
```

## Complete Examples

### Example 1: AI Plans Everything

```csv
title,has_experiments,idea,experiments
"Sentiment Analysis Benchmark",False,"Compare different transformer models (BERT, RoBERTa, DistilBERT) for sentiment analysis on movie reviews. Include baseline bag-of-words model.",""
```

### Example 2: Pre-Defined Simple Experiments

```csv
title,has_experiments,idea,experiments
"Quick A/B Test",True,"Test two email subject lines","stop_on_fail: true
steps:
  - name: setup
    cmd: python scripts/setup.py
    sanity: []
    retry: 1
  - name: run_test
    cmd: python scripts/ab_test.py --variants 2
    sanity:
      - type: file_exists
        path: results/test_results.json
    retry: 2"
```

### Example 3: Complex Pre-Defined Experiments

```csv
title,has_experiments,idea,experiments
"Deep Learning Optimization Study",True,"Compare Adam, SGD, and RMSprop optimizers","stop_on_fail: true
config:
  random_seed: 42
  output_dir: artifacts
steps:
  - name: prepare_data
    description: Load and split ImageNet subset
    cmd: python scripts/prepare_imagenet.py --subset 10000
    sanity:
      - type: file_exists
        path: artifacts/data/train.h5
      - type: json_value
        path: artifacts/data/stats.json
        key: num_samples
        operator: '>'
        value: 8000
    retry: 3
    timeout_minutes: 60
  - name: train_adam
    description: Train with Adam optimizer
    cmd: python scripts/train.py --optimizer adam --epochs 50
    sanity:
      - type: json_value
        path: artifacts/adam/metrics.json
        key: val_accuracy
        operator: '>'
        value: 0.7
    retry: 2
    timeout_minutes: 240
  - name: train_sgd
    description: Train with SGD optimizer
    cmd: python scripts/train.py --optimizer sgd --epochs 50
    sanity:
      - type: json_value
        path: artifacts/sgd/metrics.json
        key: val_accuracy
        operator: '>'
        value: 0.65
    retry: 2
    timeout_minutes: 240
  - name: compare_results
    description: Statistical comparison of optimizers
    cmd: python scripts/compare.py --results artifacts/*/metrics.json
    sanity:
      - type: file_exists
        path: artifacts/comparison/report.md
    retry: 1
    timeout_minutes: 30"
```

## Tips for Writing Good Ideas

### For AI-Planned Experiments:
- Be specific about the hypothesis to test
- Mention baseline comparisons desired
- Specify evaluation metrics if known
- Include dataset preferences
- Note any constraints (time, compute, etc.)

**Good example:**
```
"Evaluate whether LSTM or Transformer models perform better on time-series forecasting for stock prices. Use 5 years of S&P 500 data. Compare RMSE and directional accuracy. Include naive baseline."
```

**Poor example:**
```
"Do machine learning on stocks"
```

### For Pre-Defined Experiments:
- Provide complete, valid YAML
- Include clear sanity checks for each step
- Specify resource requirements
- Set appropriate timeouts
- Define retry counts

## Validation

The orchestrators will validate:
- CSV/Excel can be parsed
- Required columns are present
- Boolean values can be parsed
- YAML in `experiments` column is valid (when has_experiments=True)
- Step names are unique within a plan

## Common Mistakes

❌ **Wrong:** Using `description` instead of `idea`
```csv
title,has_experiments,description,experiments  # Wrong column name
```

✅ **Correct:** Using `idea`
```csv
title,has_experiments,idea,experiments
```

---

❌ **Wrong:** Not providing experiments when has_experiments=True
```csv
title,has_experiments,idea,experiments
"Test",True,"Some idea",""  # Empty experiments!
```

✅ **Correct:** Providing YAML when has_experiments=True
```csv
title,has_experiments,idea,experiments
"Test",True,"Some idea","stop_on_fail: true\nsteps: [...]"
```

---

❌ **Wrong:** Invalid YAML syntax
```csv
title,has_experiments,idea,experiments
"Test",True,"Some idea","steps: - name: bad syntax without proper indentation"
```

✅ **Correct:** Valid YAML
```csv
title,has_experiments,idea,experiments
"Test",True,"Some idea","steps:\n  - name: proper_step\n    cmd: python script.py"
```

## Testing Your CSV

Before running the orchestrator, test your CSV:

```python
import pandas as pd

# Load and inspect
df = pd.read_csv('ideas.csv')
print(df.columns)
print(df.head())

# Check for required columns
required = ['title', 'has_experiments', 'idea', 'experiments']
missing = [col for col in required if col not in df.columns]
if missing:
    print(f"Missing columns: {missing}")
else:
    print("✅ All required columns present")

# Check has_experiments parsing
for idx, row in df.iterrows():
    has_exp = row['has_experiments']
    print(f"Row {idx}: has_experiments = {has_exp} (type: {type(has_exp)})")
```

---

**Questions?** Check the main README.md or individual provider documentation.

