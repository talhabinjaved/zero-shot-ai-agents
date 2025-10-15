# OpenHands Repository Microagent

## Repository Purpose
This repository contains automated computational experiments. The experiments are defined in `experiments/experiments.yaml` and executed via GitHub Actions CI/CD pipelines.

## Experiment Structure
```
experiments/experiments.yaml    # Main experiment configuration
runner.py                       # Script to execute individual experiment steps
.github/workflows/             # GitHub Actions workflows for CI/CD
artifacts/                      # Generated results, logs, and outputs
```

## CI/CD Workflow
- **run_step**: Executes individual experiment steps with sanity checks
- **run_pipeline**: Runs the complete experiment pipeline
- **validate**: Validates experiment configuration before execution
- **run_large_scale**: Handles resource-intensive experiments

## Sanity Check Protocol
Each experiment step includes sanity checks that must pass:
- **file_exists**: Verify expected output files are created
- **json_value**: Validate metrics meet minimum thresholds

When sanity checks fail, OpenHands should:
1. Analyze the failure logs in `artifacts/logs/`
2. Identify the root cause (missing dependencies, incorrect parameters, etc.)
3. Fix the code, configuration, or parameters
4. Commit changes and allow CI to retry

## Experiment Steps
Experiments are structured as ordered steps with dependencies:

1. **environment_setup**: Verify dependencies and environment
2. **data_preparation**: Load and preprocess data
3. **baseline_experiment**: Run baseline comparison
4. **main_experiment**: Execute the primary experiment
5. **analysis_and_reporting**: Generate results and visualizations

## Artifact Management
- **artifacts/step_results/**: Detailed results for each step execution
- **artifacts/logs/**: Command outputs and error messages
- **artifacts/sanity_*.json**: Sanity check results
- **artifacts/experiment_results.json**: Overall experiment summary

## Code Quality Standards
- Use type hints and clear docstrings
- Handle exceptions appropriately
- Log important events and errors
- Follow consistent naming conventions
- Write deterministic code with fixed random seeds

## Dependencies
- **requirements.txt**: Core Python dependencies
- **experiments/requirements.txt**: Experiment-specific packages
- System dependencies installed via apt-get in CI

## Configuration Files
- **experiments/experiments.yaml**: Main experiment plan
- **experiments/idea.json**: Original idea description and metadata
- **AGENTS.md**: General agent instructions (loaded by OpenHands)

## Error Handling
- Steps can retry up to the configured limit with exponential backoff
- Sanity check failures trigger OpenHands iteration
- Timeouts are enforced per step to prevent hanging CI jobs

## Success Criteria
An experiment is successful when:
1. All steps complete without errors
2. All sanity checks pass
3. Required artifacts are generated
4. Results are properly logged and summarized

## OpenHands Workflow
1. Monitor CI job execution and logs
2. When a step fails sanity checks, analyze the failure
3. Modify code, configuration, or scripts to fix the issue
4. Commit changes and let CI retry the step
5. Continue until all steps pass or manual intervention is needed

## Communication
- Use conventional commit messages for all changes
- Update progress in `artifacts/` directory
- Generate comprehensive README when experiments complete
- Document any assumptions or limitations in results
