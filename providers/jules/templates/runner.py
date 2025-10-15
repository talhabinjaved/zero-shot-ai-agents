#!/usr/bin/env python3
"""
Experiment Runner for Jules + GitHub Actions

This script executes individual experiment steps as defined in experiments/manifest.yaml.
Jules will monitor execution and iterate on failures based on AGENTS.md guidance.

Usage:
    python run_experiment.py --step <step_id> [--manifest experiments/manifest.yaml]
"""

import argparse
import json
import os
import subprocess
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('experiment_runner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ExperimentRunner:
    """Handles execution of experiment steps with validation and state tracking."""

    def __init__(self, manifest_path: str, output_dir: str = "results"):
        """
        Initialize the runner.

        Args:
            manifest_path: Path to experiments/manifest.yaml
            output_dir: Base directory for results and artifacts
        """
        self.manifest_path = Path(manifest_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load experiment manifest
        with open(self.manifest_path, 'r') as f:
            self.manifest = yaml.safe_load(f)

        logger.info(f"Loaded experiment manifest from {manifest_path}")

    def run_step(self, step_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute a single experiment step.

        Args:
            step_id: ID of the step to execute

        Returns:
            Tuple of (success: bool, state: dict)
        """
        # Find the step configuration
        step_config = None
        for step in self.manifest.get('steps', []):
            if step.get('id') == step_id:
                step_config = step
                break

        if not step_config:
            raise ValueError(f"Step '{step_id}' not found in manifest")

        logger.info(f"Executing step: {step_id}")
        logger.info(f"Name: {step_config.get('name', 'Unnamed')}")
        logger.info(f"Description: {step_config.get('description', 'No description')}")

        # Execute the step command
        # Jules will have generated the actual implementation code
        # This is a placeholder that delegates to step-specific scripts
        success, state = self._execute_step(step_config)

        # Write state.json for Jules to read
        state_file = self.output_dir / "state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

        # Run validation checks
        validation_passed = self._validate_step(step_id, step_config, state)

        # Update state with validation results
        state['validation_passed'] = validation_passed
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

        logger.info(f"Step {step_id} completed. Success: {success}, Validation: {validation_passed}")

        return success and validation_passed, state

    def _execute_step(self, step_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute the step implementation.

        Args:
            step_config: Step configuration from manifest

        Returns:
            Tuple of (success: bool, state: dict)
        """
        step_id = step_config['id']

        # In a real implementation, Jules will have generated script files
        # For now, this is a placeholder that shows the expected interface
        script_path = Path('scripts') / f'{step_id}.py'

        state = {
            'step': step_id,
            'name': step_config.get('name', ''),
            'status': 'unknown',
            'metrics': {},
            'notes': '',
            'replan_suggestion': None,
            'timestamp': time.time()
        }

        if script_path.exists():
            logger.info(f"Running script: {script_path}")

            try:
                # Set environment variables
                env = os.environ.copy()
                env['PYTHONPATH'] = str(Path.cwd())
                env['EXPERIMENT_STEP'] = step_id

                # Run the step-specific script
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=step_config.get('resources', {}).get('expected_duration_minutes', 60) * 60,
                    env=env
                )

                success = result.returncode == 0
                output = result.stdout + result.stderr

                # Save output log
                log_file = self.output_dir / "logs" / f"{step_id}.log"
                log_file.parent.mkdir(parents=True, exist_ok=True)
                with open(log_file, 'w') as f:
                    f.write(f"Step: {step_id}\n")
                    f.write(f"Exit code: {result.returncode}\n")
                    f.write("Output:\n")
                    f.write(output)
                    f.write("\n")

                state['status'] = 'ok' if success else 'failed'
                state['exit_code'] = result.returncode
                state['output_summary'] = output[:500]  # First 500 chars

                return success, state

            except subprocess.TimeoutExpired:
                logger.error(f"Step {step_id} timed out")
                state['status'] = 'timeout'
                state['replan_suggestion'] = 'Increase timeout or optimize computation'
                return False, state

            except Exception as e:
                logger.error(f"Error executing step {step_id}: {e}")
                state['status'] = 'error'
                state['notes'] = str(e)
                return False, state

        else:
            logger.warning(f"Script {script_path} not found - Jules needs to implement this step")
            state['status'] = 'not_implemented'
            state['replan_suggestion'] = f'Implement {script_path} to execute this step'
            return False, state

    def _validate_step(self, step_id: str, step_config: Dict[str, Any], state: Dict[str, Any]) -> bool:
        """
        Validate step outputs against sanity checks.

        Args:
            step_id: Step identifier
            step_config: Step configuration
            state: Current step state

        Returns:
            True if all validations pass
        """
        # Find validation rules for this step
        validations = []
        for val in self.manifest.get('validation', []):
            if val.get('step') == step_id:
                validations = val.get('checks', [])
                break

        if not validations:
            logger.info(f"No validation checks defined for step {step_id}")
            return True

        all_passed = True
        validation_results = []

        for check in validations:
            check_type = check.get('type')
            passed = False

            try:
                if check_type == 'file_exists':
                    path = Path(check['path'])
                    passed = path.exists()
                    message = f"File {path} {'exists' if passed else 'does not exist'}"

                elif check_type == 'metric':
                    path = Path(check['path'])
                    if path.exists():
                        with open(path, 'r') as f:
                            data = json.load(f)

                        key = check['key']
                        condition = check['condition']

                        if key in data:
                            value = data[key]
                            # Parse condition (e.g., "> 0.1", ">= 100")
                            if '>' in condition:
                                if '>=' in condition:
                                    threshold = float(condition.split('>=')[1].strip())
                                    passed = float(value) >= threshold
                                else:
                                    threshold = float(condition.split('>')[1].strip())
                                    passed = float(value) > threshold
                            elif '<' in condition:
                                if '<=' in condition:
                                    threshold = float(condition.split('<=')[1].strip())
                                    passed = float(value) <= threshold
                                else:
                                    threshold = float(condition.split('<')[1].strip())
                                    passed = float(value) < threshold
                            else:
                                passed = False

                            message = f"{key} = {value} {condition}: {passed}"
                        else:
                            message = f"Key '{key}' not found in {path}"
                    else:
                        message = f"Metrics file {path} does not exist"

                else:
                    message = f"Unknown validation type: {check_type}"

            except Exception as e:
                message = f"Error running validation: {e}"

            validation_results.append({
                'check': check,
                'passed': passed,
                'message': message
            })

            all_passed = all_passed and passed
            logger.info(f"Validation: {message}")

        # Save validation results
        validation_file = self.output_dir / f"validation_{step_id}.json"
        with open(validation_file, 'w') as f:
            json.dump({
                'step': step_id,
                'checks': validation_results,
                'all_passed': all_passed,
                'timestamp': time.time()
            }, f, indent=2)

        return all_passed


def main():
    """Main entry point for the experiment runner."""
    parser = argparse.ArgumentParser(description="Experiment Runner for Jules")
    parser.add_argument(
        "--step",
        required=True,
        help="Step ID to execute"
    )
    parser.add_argument(
        "--manifest",
        default="experiments/manifest.yaml",
        help="Path to experiment manifest file"
    )
    parser.add_argument(
        "--output",
        default="results",
        help="Output directory for results"
    )

    args = parser.parse_args()

    try:
        runner = ExperimentRunner(args.manifest, args.output)
        success, state = runner.run_step(args.step)

        # For Jules to read and adapt, we exit with failure if validation fails
        # This allows Jules to see the state.json and adjust the implementation
        if not success:
            logger.error(f"Step {args.step} failed")
            logger.error(f"Status: {state.get('status')}")
            if state.get('replan_suggestion'):
                logger.error(f"Suggestion: {state.get('replan_suggestion')}")
            sys.exit(1)

        logger.info(f"Step {args.step} completed successfully")

    except Exception as e:
        logger.error(f"Experiment runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
