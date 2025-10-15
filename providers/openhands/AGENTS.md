# AGENTS.md for OpenHands

## Mission
Given `/experiments/idea.json`, produce a production-ready codebase that: 1) Plans experiments (JSON steps[] with deps, budgets, sanity checks). 2) Executes each step via `.github/workflows/experiments.yml`, captures artifacts, and **self-checks** metrics. 3) Retries or adjusts configs if a sanity gate fails; only proceed on pass. 4) Produces `RESULTS.md`, an investor-grade `README`, and `NEXT_STEPS.md`. 5) Opens a PR with all changes.

## Build & Run
- Python 3.11; `sudo apt-get update && sudo apt-get install -y build-essential git-lfs`
- `pip install -r experiments/requirements.txt`
- `pytest -q` must pass before marking a step complete.
- Keep `state/plan.json` and `state/progress.json` current.

## Data & Safety
- Prefer small synthetic datasets if external sources are risky.
- If a dependency is unstable, pin exact versions and record hashes.

## Style
- Conventional commits (feat/fix/chore/docs/test).
- Short functions, clear logs, deterministic seeds.
