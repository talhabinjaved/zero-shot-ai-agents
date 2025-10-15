# Augment Agent Instructions

## Mission
Given an invention idea, **plan, execute, test, interpret, and improve** a computational program of record that validates the idea through systematic experimentation.

## Core Workflow
1. **Read the idea** from `experiments/idea.json`
2. **Generate a detailed plan** in `experiments.yaml` with ordered steps, dependencies, and sanity checks
3. **Execute each step** using GitHub Actions workflows for heavy computation
4. **Validate results** against sanity checks; retry or revise if failed
5. **Interpret findings** and update the plan or code accordingly
6. **Produce deliverables**: working codebase, results artifacts, and polished README

## Experiment Planning
- **experiments.yaml** must contain:
  - `steps[]`: ordered list of experiment steps
  - Each step needs: `name`, `cmd`, `inputs[]`, `resources` (RAM/CPU/time estimates), `sanity[]` checks, `retry` count
  - `stop_on_fail`: boolean to halt pipeline on sanity failure
- Steps should have clear dependencies and build upon each other
- Include baseline/control experiments for comparison

## Execution Rules
- **Never execute heavy computation locally** - always use GitHub Actions workflows
- **Trigger CI jobs** via `gh workflow run experiments.yml -f step=<step_id>`
- **Wait for completion** and parse results from workflow artifacts
- **Sanity checks are mandatory** - validate outputs before proceeding to next step
- **Retry logic**: attempt fixes, adjust parameters, then escalate if persistent failures

## Sanity Checks Contract
Every step must validate its outputs using deterministic checks:
- **Metric thresholds**: e.g., `accuracy >= 0.8`, `loss < 0.5`
- **Output validation**: check file existence, shape, ranges
- **Statistical tests**: ensure distributions match expectations
- **Write results** to `artifacts/sanity_<step>.json` with `ok: boolean` and `details`

## Artifact Management
- **Store all outputs** under `artifacts/` directory
- **Machine-readable results** go to `artifacts/results.json`
- **Logs and diagnostics** to `artifacts/logs/`
- **Plots and visualizations** to `artifacts/plots/`
- **Reference artifacts** from README.md with relative paths

## Code Quality Standards
- **Modular functions** with clear docstrings
- **Configuration-driven** parameters (no hardcoding)
- **Reproducible seeds** for stochastic operations
- **Error handling** with informative messages
- **Type hints** and clean formatting

## CI/CD Integration
- **GitHub Actions workflows** handle all computation
- **Apt-get and pip installs** are allowed in CI environment
- **Cache dependencies** for faster subsequent runs
- **Upload artifacts** for result analysis
- **Timeout handling**: split long jobs into multiple workflow calls

## Deliverables
1. **Working codebase** that passes all tests
2. **Comprehensive README.md** with:
   - Abstract/hypothesis
   - Methods and experimental setup
   - Results with metrics and visualizations
   - Error bars and statistical significance
   - Limitations and assumptions
   - Concrete next steps for improvement
3. **RESULTS.md** with detailed findings
4. **NEXT_STEPS.md** with prioritized recommendations

## Safety and Ethics
- **No harmful content** or dangerous experiments
- **Respect data privacy** and licensing
- **Document assumptions** and limitations clearly
- **Bias awareness** in data and algorithms
- **Reproducibility** as a core principle

## Communication Style
- **Clear, technical writing** accessible to domain experts
- **Precise terminology** with definitions when introducing concepts
- **Data-driven conclusions** backed by evidence
- **Honest uncertainty** when results are inconclusive
- **Actionable recommendations** for next steps
