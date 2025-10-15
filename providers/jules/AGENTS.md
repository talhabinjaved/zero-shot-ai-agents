# AGENTS.md for Jules

## Purpose
This repo is an automated research workspace. A Jules session will plan, execute, sanity-check, and interpret a sequence of experiments defined in `experiments/manifest.yaml`.

## Setup
- Python 3.12; install with: `pip install -r requirements.txt`
- Cache datasets/models under `.cache/` (safe to create)
- Run CI job locally: `python scripts/run_experiment.py --step <id>`

## Contract for Agents
- Read `experiments/manifest.yaml` (ordered steps with `sanity` rules).
- For each step:
  1. Generate code under `src/` or `notebooks/`.
  2. Run `scripts/run_experiment.py --step <id>`.
  3. Parse `results/state.json` for `status`, metrics, and any `replan_suggestion`.
  4. If sanity fails, adjust the plan (hyperparams, data cleaning) and retry **once**, then ask for guidance if still failing.
- On completion:
  - Update `RESULTS.md` and the **README** (abstract → methods → results → next steps).
  - Open a PR with diffs, summary, and TODOs.

## Safety & Limits
- Prefer deterministic seeds.
- No long-running dev servers in setup scripts.
- If a package install fails, try a compatible version and explain the choice in the PR description.
