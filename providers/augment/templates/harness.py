#!/usr/bin/env python3
"""
Experiment Harness for GitHub Actions

This script executes individual experiment steps as defined in experiments.yaml.
It handles sanity checking, retry logic, and artifact management.

Usage:
    python harness.py --step <step_name> --config experiments.yaml [--output artifacts/]
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
        logging.FileHandler('harness.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ExperimentHarness:
    """Handles execution of experiment steps with sanity checking and retries."""

    def __init__(self, config_path: str, output_dir: str = "artifacts"):
        """
        Initialize the harness.

        Args:
            config_path: Path to experiments.yaml
            output_dir: Base directory for artifacts
        """
        self.config_path = Path(config_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load experiment configuration
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        logger.info(f"Loaded experiment config from {config_path}")

    def run_step(self, step_name: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute a single experiment step.

        Args:
            step_name: Name of the step to execute

        Returns:
            Tuple of (success: bool, results: dict)
        """
        if step_name not in [s['name'] for s in self.config.get('steps', [])]:
            raise ValueError(f"Step '{step_name}' not found in experiment config")

        step_config = next(s for s in self.config['steps'] if s['name'] == step_name)
        logger.info(f"Executing step: {step_name}")
        logger.info(f"Description: {step_config.get('description', 'No description')}")

        # Execute with retry logic
        max_retries = step_config.get('retry', 1)
        timeout_minutes = step_config.get('timeout_minutes', 60)

        for attempt in range(max_retries + 1):
            logger.info(f"Attempt {attempt + 1}/{max_retries + 1} for step {step_name}")

            try:
                success, output, exit_code = self._execute_command(
                    step_config['cmd'],
                    timeout_minutes=timeout_minutes
                )

                # Run sanity checks
                sanity_passed, sanity_results = self._run_sanity_checks(
                    step_config.get('sanity', []),
                    step_name
                )

                # Log results
                result = {
                    'step': step_name,
                    'attempt': attempt + 1,
                    'success': success,
                    'exit_code': exit_code,
                    'sanity_passed': sanity_passed,
                    'sanity_results': sanity_results,
                    'output': output,
                    'timestamp': time.time()
                }

                # Save step results
                self._save_step_results(step_name, attempt, result)

                if success and sanity_passed:
                    logger.info(f"Step {step_name} completed successfully")
                    return True, result
                else:
                    logger.warning(f"Step {step_name} failed sanity checks or execution")
                    if attempt < max_retries:
                        logger.info("Retrying after backoff...")
                        time.sleep(10 * (attempt + 1))  # Exponential backoff

            except Exception as e:
                logger.error(f"Error executing step {step_name}: {e}")
                if attempt == max_retries:
                    result = {
                        'step': step_name,
                        'attempt': attempt + 1,
                        'success': False,
                        'error': str(e),
                        'timestamp': time.time()
                    }
                    self._save_step_results(step_name, attempt, result)

        logger.error(f"Step {step_name} failed after {max_retries + 1} attempts")
        return False, result

    def _execute_command(self, cmd: str, timeout_minutes: int = 60) -> Tuple[bool, str, int]:
        """
        Execute a shell command with timeout.

        Args:
            cmd: Command to execute
            timeout_minutes: Timeout in minutes

        Returns:
            Tuple of (success: bool, output: str, exit_code: int)
        """
        logger.info(f"Running command: {cmd}")

        try:
            # Set environment variables for the command
            env = os.environ.copy()
            env['PYTHONPATH'] = str(Path.cwd())

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_minutes * 60,
                cwd=Path.cwd(),
                env=env
            )

            success = result.returncode == 0
            output = result.stdout + result.stderr

            logger.info(f"Command completed with exit code {result.returncode}")

            # Save command output to log file
            log_file = self.output_dir / f"logs" / f"step_{cmd.split()[0]}_{int(time.time())}.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'w') as f:
                f.write(f"Command: {cmd}\n")
                f.write(f"Exit code: {result.returncode}\n")
                f.write(f"Output:\n{output}\n")

            return success, output, result.returncode

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout_minutes} minutes")
            return False, f"Timeout after {timeout_minutes} minutes", -1

    def _run_sanity_checks(self, sanity_checks: List[Dict], step_name: str) -> Tuple[bool, List[Dict]]:
        """
        Run sanity checks for a step.

        Args:
            sanity_checks: List of sanity check configurations
            step_name: Name of the step

        Returns:
            Tuple of (all_passed: bool, results: list of check results)
        """
        results = []

        for check in sanity_checks:
            check_result = self._run_single_sanity_check(check)
            results.append(check_result)

        all_passed = all(r['passed'] for r in results)

        # Save sanity results
        sanity_file = self.output_dir / f"sanity_{step_name}.json"
        with open(sanity_file, 'w') as f:
            json.dump({
                'step': step_name,
                'checks': results,
                'all_passed': all_passed,
                'timestamp': time.time()
            }, f, indent=2)

        return all_passed, results

    def _run_single_sanity_check(self, check: Dict) -> Dict:
        """
        Run a single sanity check.

        Args:
            check: Sanity check configuration

        Returns:
            Check result dictionary
        """
        check_type = check.get('type', '')

        try:
            if check_type == 'file_exists':
                path = Path(check['path'])
                passed = path.exists()
                message = f"File {path} {'exists' if passed else 'does not exist'}"

            elif check_type == 'json_value':
                path = Path(check['path'])
                if not path.exists():
                    passed = False
                    message = f"JSON file {path} does not exist"
                else:
                    with open(path, 'r') as f:
                        data = json.load(f)

                    key = check['key']
                    operator = check['operator']
                    expected_value = check['value']

                    if key not in data:
                        passed = False
                        message = f"Key '{key}' not found in {path}"
                    else:
                        actual_value = data[key]

                        # Type conversion for comparison
                        if isinstance(expected_value, str) and expected_value.replace('.', '').isdigit():
                            if '.' in expected_value:
                                expected_value = float(expected_value)
                                actual_value = float(actual_value) if isinstance(actual_value, (int, float, str)) else actual_value
                            else:
                                expected_value = int(expected_value)
                                actual_value = int(actual_value) if isinstance(actual_value, (int, float, str)) else actual_value

                        # Perform comparison
                        if operator == '>=':
                            passed = actual_value >= expected_value
                        elif operator == '>':
                            passed = actual_value > expected_value
                        elif operator == '<=':
                            passed = actual_value <= expected_value
                        elif operator == '<':
                            passed = actual_value < expected_value
                        elif operator == '==':
                            passed = actual_value == expected_value
                        elif operator == '!=':
                            passed = actual_value != expected_value
                        else:
                            passed = False

                        message = f"{key} = {actual_value} {operator} {expected_value}: {passed}"

            else:
                passed = False
                message = f"Unknown check type: {check_type}"

        except Exception as e:
            passed = False
            message = f"Error running check: {e}"

        return {
            'type': check_type,
            'config': check,
            'passed': passed,
            'message': message,
            'timestamp': time.time()
        }

    def _save_step_results(self, step_name: str, attempt: int, result: Dict):
        """Save step execution results to artifacts directory."""
        results_dir = self.output_dir / "step_results"
        results_dir.mkdir(parents=True, exist_ok=True)

        result_file = results_dir / f"{step_name}_attempt_{attempt + 1}.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

    def run_all_steps(self) -> Dict[str, Any]:
        """
        Run all steps in the experiment plan.

        Returns:
            Summary of all step results
        """
        results = {}
        stop_on_fail = self.config.get('stop_on_fail', True)

        for step in self.config.get('steps', []):
            step_name = step['name']
            logger.info(f"Starting step: {step_name}")

            success, step_result = self.run_step(step_name)
            results[step_name] = step_result

            if not success and stop_on_fail:
                logger.error(f"Stopping execution due to failure in step: {step_name}")
                break

        # Run post-processing if all steps succeeded
        if all(r.get('success', False) and r.get('sanity_passed', False) for r in results.values()):
            self._run_post_process()

        # Save overall results
        overall_results = {
            'experiment_config': str(self.config_path),
            'steps': results,
            'completed_at': time.time(),
            'all_success': all(r.get('success', False) and r.get('sanity_passed', False) for r in results.values())
        }

        results_file = self.output_dir / "experiment_results.json"
        with open(results_file, 'w') as f:
            json.dump(overall_results, f, indent=2, default=str)

        return overall_results

    def _run_post_process(self):
        """Run post-processing steps if defined."""
        post_process = self.config.get('post_process', [])
        for step in post_process:
            logger.info(f"Running post-process step: {step['name']}")
            try:
                success, output, exit_code = self._execute_command(
                    step['cmd'],
                    timeout_minutes=step.get('timeout_minutes', 30)
                )
                if not success:
                    logger.warning(f"Post-process step {step['name']} failed")
            except Exception as e:
                logger.error(f"Error in post-process step {step['name']}: {e}")


def main():
    """Main entry point for the harness script."""
    parser = argparse.ArgumentParser(description="Experiment Harness for GitHub Actions")
    parser.add_argument(
        "--config",
        default="experiments.yaml",
        help="Path to experiments configuration file"
    )
    parser.add_argument(
        "--step",
        help="Specific step to run (if not provided, runs all steps)"
    )
    parser.add_argument(
        "--output",
        default="artifacts",
        help="Output directory for artifacts"
    )

    args = parser.parse_args()

    try:
        harness = ExperimentHarness(args.config, args.output)

        if args.step:
            success, result = harness.run_step(args.step)
            sys.exit(0 if success else 1)
        else:
            results = harness.run_all_steps()
            success = results.get('all_success', False)
            logger.info(f"Experiment completed. Success: {success}")
            sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Harness execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
