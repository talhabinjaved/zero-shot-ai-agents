#!/usr/bin/env python3
"""
Augment Experiment Orchestrator

This script orchestrates the creation and execution of computational experiments using Augment.
It reads ideas from CSV/Excel, creates GitHub repositories, seeds them with experiment templates,
and uses Augment CLI to plan, execute, and interpret experiments.

Usage:
    python orchestrator.py [--input ideas.csv] [--output-dir repos/] [--max-concurrent 3]

Environment Variables:
    GITHUB_TOKEN: GitHub personal access token with repo creation permissions
    GITHUB_OWNER: GitHub username or organization name
    AUGMENT_SESSION_AUTH: Augment session authentication token
"""

import argparse
import base64
import csv
import json
import os
import shutil
import subprocess
import sys
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

import pandas as pd
import requests
import yaml
from slugify import slugify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ExperimentIdea:
    """Represents an experiment idea from the input CSV/Excel."""
    title: str
    idea: str  # Main idea/description field
    has_experiments: bool  # True if experiments are pre-defined, False if AI should plan
    experiments: Optional[str] = None  # Pre-defined experiments YAML (if has_experiments is True)
    data_url: Optional[str] = None
    requirements: Optional[str] = None


@dataclass
class RepoConfig:
    """Configuration for repository creation and management."""
    owner: str
    token: str
    base_dir: Path
    private: bool = True
    max_concurrent: int = 3


class GitHubClient:
    """Client for GitHub REST API operations."""

    def __init__(self, token: str, owner: str):
        self.token = token
        self.owner = owner
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        })
        self.api_base = 'https://api.github.com'

    def create_repo(self, name: str, description: str = "", private: bool = True) -> Dict[str, Any]:
        """Create a new GitHub repository and return repo data including default branch."""
        url = f'{self.api_base}/orgs/{self.owner}/repos'
        if self._is_user_account():
            url = f'{self.api_base}/user/repos'

        payload = {
            'name': name,
            'description': description,
            'private': private,
            'auto_init': False
        }

        response = self.session.post(url, json=payload)
        response.raise_for_status()

        repo_data = response.json()
        full_name = repo_data['full_name']
        default_branch = repo_data.get('default_branch', 'main')
        
        logger.info(f"Created repository: {full_name}")
        logger.info(f"Default branch: {default_branch}")
        
        return {
            'full_name': full_name,
            'default_branch': default_branch,
            'repo_data': repo_data
        }

    def _is_user_account(self) -> bool:
        """Check if the owner is a user account vs organization."""
        url = f'{self.api_base}/users/{self.owner}'
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()['type'] == 'User'
    
    def get_repo(self, repo_full_name: str) -> Dict[str, Any]:
        """Get repository information including default branch."""
        url = f'{self.api_base}/repos/{repo_full_name}'
        response = self.session.get(url)
        response.raise_for_status()
        
        repo_data = response.json()
        return {
            'full_name': repo_data['full_name'],
            'default_branch': repo_data.get('default_branch', 'main'),
            'repo_data': repo_data
        }

    def put_file(self, repo_full_name: str, path: str, content: str, message: str) -> Dict[str, Any]:
        """Create or update a file in the repository."""
        url = f'{self.api_base}/repos/{repo_full_name}/contents/{path}'

        # Encode content as base64
        content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        payload = {
            'message': message,
            'content': content_b64
        }

        # Check if file exists and get its SHA if it does
        try:
            existing = self.session.get(url)
            if existing.status_code == 200:
                sha = existing.json()['sha']
                payload['sha'] = sha
                logger.debug(f"File {path} exists, updating with SHA {sha[:7]}...")
        except Exception:
            # File doesn't exist, we'll create it
            pass

        response = self.session.put(url, json=payload)
        response.raise_for_status()

        return response.json()

    def get_workflow_runs(self, repo_full_name: str, workflow_name: str = None) -> List[Dict[str, Any]]:
        """Get workflow runs for a repository."""
        url = f'{self.api_base}/repos/{repo_full_name}/actions/runs'
        params = {'per_page': 10}
        if workflow_name:
            params['workflow_name'] = workflow_name

        response = self.session.get(url, params=params)
        response.raise_for_status()

        return response.json()['workflow_runs']

    def trigger_workflow(self, repo_full_name: str, workflow_name: str, inputs: Dict[str, Any] = None) -> bool:
        """Trigger a workflow dispatch event."""
        url = f'{self.api_base}/repos/{repo_full_name}/actions/workflows/{workflow_name}/dispatches'

        payload = {
            'ref': 'main',
            'inputs': inputs or {}
        }

        response = self.session.post(url, json=payload)
        return response.status_code == 204


class AugmentClient:
    """Client for interacting with Augment CLI."""

    def __init__(self, session_auth: str):
        self.session_auth = session_auth

    def run_command(self, instruction: str, cwd: Optional[Path] = None,
                   extra_env: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
        """
        Execute an Augment CLI command.

        Args:
            instruction: The natural language instruction for Augment
            cwd: Working directory for the command
            extra_env: Additional environment variables

        Returns:
            Tuple of (exit_code, output)
        """
        env = os.environ.copy()
        env['AUGMENT_SESSION_AUTH'] = self.session_auth
        if extra_env:
            env.update(extra_env)

        cmd = ['auggie', '--print', instruction]

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=18000,  # 5 hour timeout for individual commands (planning can be slow)
                env=env
            )

            output = result.stdout + result.stderr
            logger.info(f"Auggie command completed with exit code {result.returncode}")

            return result.returncode, output

        except subprocess.TimeoutExpired:
            logger.error("Auggie command timed out")
            return -1, "Command timed out after 5 hours"

        except FileNotFoundError:
            logger.error("Auggie CLI not found. Please install with: npm install -g @augmentcode/auggie")
            return -1, "Auggie CLI not installed"


class ExperimentOrchestrator:
    """Main orchestrator for creating and managing experiment repositories."""

    def __init__(self, config: RepoConfig, augment_auth: str):
        self.config = config
        self.github = GitHubClient(config.token, config.owner)
        self.augment = AugmentClient(augment_auth)
        self.active_repos: Dict[str, Dict[str, Any]] = {}

    def load_ideas(self, input_path: str) -> List[ExperimentIdea]:
        """
        Load experiment ideas from CSV or Excel file.
        
        Expected columns:
        - title: Experiment title
        - has_experiments: Boolean (True/1 if experiments provided, False/0 if AI should plan)
        - idea: Description of the idea
        - experiments: Pre-defined experiments YAML (optional, used when has_experiments is True)
        """
        if input_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(input_path)
        else:
            df = pd.read_csv(input_path)

        ideas = []
        for _, row in df.iterrows():
            # Parse has_experiments column (handle various boolean representations)
            has_experiments_raw = row.get('has_experiments', False)
            if isinstance(has_experiments_raw, str):
                has_experiments = has_experiments_raw.lower() in ('true', '1', 'yes', 'y')
            else:
                has_experiments = bool(has_experiments_raw)
            
            idea = ExperimentIdea(
                title=str(row.get('title', f'Idea_{len(ideas)}')),
                idea=str(row.get('idea', '')),
                has_experiments=has_experiments,
                experiments=row.get('experiments') if has_experiments else None,
                data_url=row.get('data_url'),
                requirements=row.get('requirements')
            )
            ideas.append(idea)

        logger.info(f"Loaded {len(ideas)} experiment ideas")
        logger.info(f"  - {sum(1 for i in ideas if i.has_experiments)} with pre-defined experiments")
        logger.info(f"  - {sum(1 for i in ideas if not i.has_experiments)} requiring AI planning")
        return ideas

    def create_experiment_repo(self, idea: ExperimentIdea) -> Tuple[str, str]:
        """Create a GitHub repository for an experiment idea.
        
        Returns:
            Tuple of (full_name, default_branch)
        """
        # Generate a clean repo name
        repo_name = slugify(idea.title, max_length=80, word_boundary=True)
        if len(repo_name) == 0:
            repo_name = f"experiment-{int(time.time())}"

        # Ensure uniqueness
        base_name = repo_name
        counter = 1
        while f"{self.config.owner}/{repo_name}" in self.active_repos:
            repo_name = f"{base_name}-{counter}"
            counter += 1

        try:
            repo_info = self.github.create_repo(
                repo_name,
                description=idea.idea[:140],  # GitHub description limit
                private=self.config.private
            )

            # Initialize main branch
            default_branch = self._initialize_repo(repo_info['full_name'], repo_info['default_branch'])

            return repo_info['full_name'], default_branch

        except requests.HTTPError as e:
            if e.response.status_code == 422:  # Repository already exists
                logger.warning(f"Repository {self.config.owner}/{repo_name} already exists, using existing")
                full_name = f"{self.config.owner}/{repo_name}"
                
                # Get the existing repo's default branch
                existing_repo_info = self.github.get_repo(full_name)
                default_branch = existing_repo_info['default_branch']
                logger.info(f"Existing repository default branch: {default_branch}")
                
                return full_name, default_branch
            else:
                raise

    def _initialize_repo(self, repo_full_name: str, expected_branch: str = 'main') -> str:
        """Initialize a repository with basic structure.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            expected_branch: Expected default branch name
            
        Returns:
            Actual default branch name
        """
        # Create a basic README first to establish the main branch
        self.github.put_file(
            repo_full_name,
            'README.md',
            f'# {repo_full_name.split("/")[1]}\n\nInitializing experiment repository...\n',
            'chore: initialize repository'
        )
        
        # After first commit, fetch the actual default branch name
        time.sleep(1)  # Give GitHub a moment to process
        repo_info = self.github.get_repo(repo_full_name)
        actual_branch = repo_info['default_branch']
        
        if actual_branch != expected_branch:
            logger.info(f"Repository initialized with '{actual_branch}' branch (expected '{expected_branch}')")
        
        return actual_branch

    def clone_repository(self, repo_full_name: str, local_path: Path, branch: str = 'main') -> bool:
        """Clone a GitHub repository to local path.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            local_path: Local path to clone to
            branch: Branch to clone
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use token in clone URL for authentication
            clone_url = f"https://{self.config.token}@github.com/{repo_full_name}.git"
            
            cmd = ['git', 'clone', '-b', branch, clone_url, str(local_path)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"Cloned repository {repo_full_name} to {local_path}")
                return True
            else:
                logger.error(f"Failed to clone repository: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            return False

    def commit_and_push(self, local_path: Path, message: str) -> bool:
        """Commit all changes and push to remote.
        
        Args:
            local_path: Local repository path
            message: Commit message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Configure git user
            subprocess.run(['git', 'config', 'user.name', 'Augment Orchestrator'], 
                         cwd=local_path, check=True)
            subprocess.run(['git', 'config', 'user.email', 'orchestrator@augment.dev'], 
                         cwd=local_path, check=True)
            
            # Add all files
            subprocess.run(['git', 'add', '.'], cwd=local_path, check=True)
            
            # Check if there are changes to commit
            status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                         cwd=local_path, capture_output=True, text=True)
            
            if not status_result.stdout.strip():
                logger.info("No changes to commit")
                return True
            
            # Commit changes
            subprocess.run(['git', 'commit', '-m', message], cwd=local_path, check=True)
            
            # Push to remote
            subprocess.run(['git', 'push'], cwd=local_path, check=True)
            
            logger.info(f"Committed and pushed changes: {message}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error committing/pushing changes: {e}")
            return False

    def seed_repository(self, repo_full_name: str, idea: ExperimentIdea, local_path: Path):
        """Seed the repository with experiment templates and configuration.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            idea: Experiment idea
            local_path: Local path where repo is cloned
        """
        logger.info(f"Seeding repository: {repo_full_name}")

        # Copy template files to local repository
        self._copy_template_files_local(local_path, idea)

        # Customize experiment configuration
        self._customize_experiments_local(local_path, idea)

        logger.info(f"Repository {repo_full_name} seeded successfully")

    def _copy_template_files_local(self, local_path: Path, idea: ExperimentIdea):
        """Copy template files to local repository clone."""
        template_dir = Path(__file__).parent / 'templates'
        repo_name = local_path.name

        # Files to copy from templates
        template_files = {
            'AGENTS.md': 'AGENTS.md',
            'experiments.yaml': 'experiments.yaml',
            'harness.py': 'harness.py',
            'workflow.yml': '.github/workflows/run-experiments.yml'
        }

        for template_file, repo_path in template_files.items():
            template_path = template_dir / template_file
            if template_path.exists():
                with open(template_path, 'r') as f:
                    content = f.read()

                # Basic templating - replace placeholders
                content = content.replace('{{REPO_NAME}}', repo_name)
                content = content.replace('{{IDEA_TITLE}}', idea.title)
                content = content.replace('{{IDEA_DESCRIPTION}}', idea.idea or '')

                # Write to local file
                dest_path = local_path / repo_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_path, 'w') as f:
                    f.write(content)

        # Add additional scaffold files
        scaffold_files = {
            'requirements.txt': self._generate_requirements(idea),
            'experiments/idea.json': json.dumps({
                'title': idea.title,
                'idea': idea.idea,
                'has_experiments': idea.has_experiments,
                'experiments': idea.experiments,
                'data_url': idea.data_url,
                'timestamp': time.time()
            }, indent=2),
            'README.template.md': self._generate_readme_template(idea),
            '.gitignore': self._generate_gitignore()
        }

        for file_path, content in scaffold_files.items():
            dest_path = local_path / file_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, 'w') as f:
                f.write(content)

    def _customize_experiments_local(self, local_path: Path, idea: ExperimentIdea):
        """Customize the experiments.yaml based on the idea in local clone."""
        if idea.has_experiments and idea.experiments:
            # Use the provided experiments configuration
            experiments_path = local_path / 'experiments.yaml'
            with open(experiments_path, 'w') as f:
                f.write(idea.experiments)

    def _generate_requirements(self, idea: ExperimentIdea) -> str:
        """Generate requirements.txt content."""
        base_reqs = [
            'pandas',
            'numpy',
            'matplotlib',
            'seaborn',
            'scikit-learn',
            'jupyter',
            'pyyaml',
            'tqdm'
        ]

        if idea.requirements:
            # Add idea-specific requirements
            additional_reqs = [req.strip() for req in idea.requirements.split(',')]
            base_reqs.extend(additional_reqs)

        return '\n'.join(base_reqs) + '\n'

    def _generate_readme_template(self, idea: ExperimentIdea) -> str:
        """Generate a README template."""
        pipeline_type = "pre-defined experiments" if idea.has_experiments else "AI-planned experiments"
        
        return f'''# {idea.title}

{idea.idea or "Experiment repository generated by Augment orchestrator."}

## Overview

This repository contains a computational experiment designed to validate the idea: **{idea.title}**.

**Pipeline Type:** {pipeline_type}

{f"**Pre-defined Experiments:** This idea includes specific experiments to execute." if idea.has_experiments else "**AI Planning:** Augment will analyze the idea and generate a comprehensive experiment plan."}

## Experiments

The experiments are {"provided in" if idea.has_experiments else "planned and defined in"} `experiments.yaml` and executed using GitHub Actions workflows.

## Results

Results and artifacts will be stored in the `artifacts/` directory after experiment execution.

## Getting Started

1. Review the experiment plan in `experiments.yaml`
2. Run experiments using GitHub Actions or locally
3. Check results in `artifacts/` directory

## Generated by Augment Orchestrator

This repository was automatically created and configured using the Augment experiment orchestrator.
Pipeline: {pipeline_type}
'''

    def _generate_gitignore(self) -> str:
        """Generate .gitignore content."""
        return '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.venv
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Experiments
artifacts/
.cache/
*.log
'''

    def plan_experiment(self, repo_full_name: str, idea: ExperimentIdea, local_path: Path) -> bool:
        """Use Augment to plan the experiment.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            idea: Experiment idea
            local_path: Local path where repo is cloned
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Planning experiment for {repo_full_name}")

        if idea.has_experiments:
            # Idea has pre-defined experiments - ask Augment to validate and enhance
            instruction = f"""
            Review the pre-defined experiments in experiments.yaml and AGENTS.md files.

            This idea comes with PRE-DEFINED EXPERIMENTS. Your task:
            1. Review and validate the provided experiment plan
            2. Ensure all steps have proper sanity checks and resource requirements
            3. Implement any missing scripts or helper functions needed
            4. Add any necessary configuration files
            5. Enhance the plan if you spot opportunities for improvement
            6. Create all implementation files and documentation

            Focus on executing the provided plan faithfully while ensuring it's production-ready.
            
            NOTE: Do not attempt to commit or push changes - the orchestrator will handle that automatically.
            """
        else:
            # AI needs to create the experiment plan from scratch
            instruction = f"""
            Review the AGENTS.md file and the idea description in experiments/idea.json.

            This idea REQUIRES YOU TO PLAN THE EXPERIMENTS. Your task:
            1. Analyze the experiment idea thoroughly
            2. Design a comprehensive, step-by-step experiment plan
            3. Create experiments.yaml with ordered steps, dependencies, and sanity checks
            4. Ensure each step has clear resource requirements and validation criteria
            5. Add baseline/control experiments for comparison
            6. Implement necessary scripts and configuration files
            7. Generate comprehensive documentation and README content

            Focus on creating a rigorous, reproducible experiment that validates the core hypothesis.
            Generate the full experiment plan from scratch based on the idea.
            
            NOTE: Do not attempt to commit or push changes - the orchestrator will handle that automatically.
            """

        exit_code, output = self.augment.run_command(instruction, cwd=local_path)

        if exit_code == 0:
            logger.info(f"Experiment planning completed for {repo_full_name}")
            logger.info(f"Augment output: {output[:500]}...")  # Log first 500 chars
            return True
        else:
            logger.error(f"Experiment planning failed for {repo_full_name}: {output}")
            return False

    def execute_experiment(self, repo_full_name: str) -> bool:
        """Execute the experiment using GitHub Actions."""
        logger.info(f"Executing experiment for {repo_full_name}")

        # Trigger the workflow
        success = self.github.trigger_workflow(
            repo_full_name,
            'run-experiments.yml',
            inputs={'idea_title': repo_full_name.split('/')[1]}
        )

        if success:
            logger.info(f"Workflow triggered for {repo_full_name}")
            return True
        else:
            logger.error(f"Failed to trigger workflow for {repo_full_name}")
            return False

    def monitor_experiment(self, repo_full_name: str, timeout_minutes: int = 120) -> Dict[str, Any]:
        """Monitor experiment execution and return results."""
        logger.info(f"Monitoring experiment for {repo_full_name}")

        start_time = time.time()
        timeout_seconds = timeout_minutes * 60

        while time.time() - start_time < timeout_seconds:
            # Check workflow runs
            runs = self.github.get_workflow_runs(repo_full_name, 'run-experiments.yml')

            if runs:
                latest_run = runs[0]  # Most recent run
                status = latest_run['status']
                conclusion = latest_run.get('conclusion')

                logger.info(f"Workflow status: {status}, conclusion: {conclusion}")

                if status == 'completed':
                    return {
                        'status': 'completed',
                        'conclusion': conclusion,
                        'run_id': latest_run['id'],
                        'html_url': latest_run['html_url']
                    }

            time.sleep(30)  # Check every 30 seconds

        return {
            'status': 'timeout',
            'message': f'Monitoring timed out after {timeout_minutes} minutes'
        }

    def generate_final_readme(self, repo_full_name: str, local_path: Path) -> bool:
        """Use Augment to generate a final polished README.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            local_path: Local path where repo is cloned
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Generating final README for {repo_full_name}")

        instruction = f"""
        Review the completed experiments and results.

        Your task:
        1. Analyze all artifacts in the artifacts/ directory
        2. Read experiment results and sanity check outputs
        3. Generate a comprehensive, professional README.md that includes:
           - Clear abstract/hypothesis
           - Methods and experimental setup
           - Results with metrics, visualizations, and statistical analysis
           - Error bars and confidence intervals where applicable
           - Limitations and assumptions
           - Concrete next steps for improvement
        4. Create RESULTS.md with detailed findings
        5. Update any necessary documentation

        Make it suitable for sharing with stakeholders and investors.
        
        NOTE: Do not attempt to commit or push - the orchestrator handles that automatically.
        """

        exit_code, output = self.augment.run_command(instruction, cwd=local_path)

        if exit_code == 0:
            logger.info(f"Final README generated for {repo_full_name}")
            return True
        else:
            logger.error(f"Failed to generate final README for {repo_full_name}: {output}")
            return False

    def process_idea(self, idea: ExperimentIdea) -> Dict[str, Any]:
        """Process a single experiment idea from start to finish."""
        logger.info(f"Processing idea: {idea.title}")

        local_clone_path = None
        try:
            # 1. Create repository
            repo_full_name, default_branch = self.create_experiment_repo(idea)
            logger.info(f"Repository default branch: {default_branch}")

            # 2. Clone repository locally
            local_clone_path = self.config.base_dir / slugify(idea.title, max_length=80)
            local_clone_path.mkdir(parents=True, exist_ok=True)
            
            clone_success = self.clone_repository(repo_full_name, local_clone_path, default_branch)
            if not clone_success:
                return {
                    'idea': idea.title,
                    'repo': repo_full_name,
                    'status': 'clone_failed',
                    'error': 'Failed to clone repository'
                }

            # 3. Seed with templates (locally)
            self.seed_repository(repo_full_name, idea, local_clone_path)

            # 4. Commit and push templates
            commit_success = self.commit_and_push(local_clone_path, 'chore: seed repository with experiment templates')
            if not commit_success:
                logger.warning("Failed to push initial templates, continuing anyway...")

            # 5. Plan experiment with Augment (runs in local directory)
            planning_success = self.plan_experiment(repo_full_name, idea, local_clone_path)
            
            # 5.5 ALWAYS commit Augment's work (even if it failed partially)
            # Augment CLI doesn't auto-commit, so we must save its work manually
            logger.info("Saving Augment's work to GitHub...")
            commit_msg = (
                'feat: experiment planning and scripts (via Augment)' 
                if planning_success 
                else 'chore: save partial experiment planning (Augment incomplete)'
            )
            
            commit_result = self.commit_and_push(local_clone_path, commit_msg)
            if commit_result:
                logger.info("Successfully pushed Augment's changes to GitHub")
            else:
                logger.warning("Failed to push Augment's changes, but continuing...")
            
            # Now check if planning was successful
            if not planning_success:
                return {
                    'idea': idea.title,
                    'repo': repo_full_name,
                    'status': 'planning_failed',
                    'error': 'Experiment planning failed (partial work saved to GitHub)'
                }

            # 6. Execute experiment
            execution_success = self.execute_experiment(repo_full_name)
            if not execution_success:
                return {
                    'idea': idea.title,
                    'repo': repo_full_name,
                    'status': 'execution_failed',
                    'error': 'Failed to trigger workflow'
                }

            # 7. Monitor execution
            execution_result = self.monitor_experiment(repo_full_name)

            if execution_result['status'] == 'timeout':
                return {
                    'idea': idea.title,
                    'repo': repo_full_name,
                    'status': 'timeout',
                    'error': execution_result['message']
                }

            if execution_result.get('conclusion') != 'success':
                # Attempt to fix issues with Augment
                self._handle_execution_failure(repo_full_name, execution_result, local_clone_path)
                
                # Commit any fixes Augment made
                logger.info("Committing fixes from execution failure handler...")
                self.commit_and_push(local_clone_path, 'fix: attempt to resolve execution failures (via Augment)')
                
                return {
                    'idea': idea.title,
                    'repo': repo_full_name,
                    'status': 'execution_failed',
                    'workflow_url': execution_result.get('html_url')
                }

            # 8. Generate final README
            readme_success = self.generate_final_readme(repo_full_name, local_clone_path)
            
            # 8.5 Commit final README updates
            if readme_success:
                logger.info("Committing final README and documentation...")
                self.commit_and_push(local_clone_path, 'docs: add final README and results documentation')

            return {
                'idea': idea.title,
                'repo': repo_full_name,
                'status': 'completed',
                'workflow_url': execution_result.get('html_url'),
                'readme_generated': readme_success
            }

        except Exception as e:
            logger.error(f"Error processing idea {idea.title}: {e}")
            
            # Try to save any work Augment did before the exception
            if local_clone_path and local_clone_path.exists():
                try:
                    logger.info("Exception occurred - attempting to save any uncommitted work...")
                    self.commit_and_push(local_clone_path, f'chore: save work before error (exception: {str(e)[:50]})')
                except Exception as commit_error:
                    logger.warning(f"Could not save uncommitted work: {commit_error}")
            
            return {
                'idea': idea.title,
                'status': 'error',
                'error': str(e)
            }
        finally:
            # Clean up local clone
            if local_clone_path and local_clone_path.exists():
                try:
                    shutil.rmtree(local_clone_path)
                    logger.info(f"Cleaned up local clone at {local_clone_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up local clone: {e}")

    def _handle_execution_failure(self, repo_full_name: str, execution_result: Dict[str, Any], local_path: Path):
        """Handle execution failures by asking Augment to diagnose and fix.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            execution_result: Result from workflow execution
            local_path: Local path where repo is cloned
        """
        logger.info(f"Handling execution failure for {repo_full_name}")

        instruction = f"""
        The workflow run failed: {execution_result.get('html_url')}

        Your task:
        1. Review the workflow logs and artifacts
        2. Identify the root cause of the failure
        3. Fix any code, configuration, or dependency issues
        4. Adjust experiment parameters if needed
        5. Document the fixes and update relevant files

        Focus on getting the experiments to run successfully.
        
        NOTE: Do not attempt to commit or push - the orchestrator handles that automatically.
        """

        self.augment.run_command(instruction, cwd=local_path)

    def run_batch(self, ideas: List[ExperimentIdea]) -> List[Dict[str, Any]]:
        """Process multiple ideas with concurrency control."""
        results = []

        # Process ideas with concurrency limit
        active_processes = {}

        for idea in ideas:
            # Wait if at concurrency limit
            while len(active_processes) >= self.config.max_concurrent:
                # Check for completed processes
                completed = []
                for idea_title, future in active_processes.items():
                    if future.done():
                        try:
                            result = future.result()
                            results.append(result)
                        except Exception as e:
                            results.append({
                                'idea': idea_title,
                                'status': 'error',
                                'error': str(e)
                            })
                        completed.append(idea_title)

                # Remove completed processes
                for completed_idea in completed:
                    del active_processes[completed_idea]

                if len(active_processes) >= self.config.max_concurrent:
                    time.sleep(5)

            # Start processing this idea
            # Note: In a real implementation, you'd use concurrent.futures or similar
            # For now, we'll process sequentially to keep it simple
            result = self.process_idea(idea)
            results.append(result)

        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Augment Experiment Orchestrator")
    parser.add_argument(
        '--input',
        default='../ideas.csv',
        help='Path to CSV/Excel file with experiment ideas'
    )
    parser.add_argument(
        '--output-dir',
        default='/Users/talhadev/Projects/temps/augment/repos',
        help='Directory to store local repository clones'
    )
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=3,
        help='Maximum number of concurrent repository operations'
    )
    parser.add_argument(
        '--private',
        action='store_true',
        default=True,
        help='Create private repositories'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )

    args = parser.parse_args()

    # Validate environment
    github_token = os.environ.get('GITHUB_TOKEN')
    github_owner = os.environ.get('GITHUB_OWNER')
    augment_auth = os.environ.get('AUGMENT_SESSION_AUTH')

    if not all([github_token, github_owner, augment_auth]):
        logger.error("Missing required environment variables:")
        logger.error("  GITHUB_TOKEN: GitHub personal access token")
        logger.error("  GITHUB_OWNER: GitHub username or organization")
        logger.error("  AUGMENT_SESSION_AUTH: Augment session authentication")
        sys.exit(1)

    # Setup configuration
    config = RepoConfig(
        owner=github_owner,
        token=github_token,
        base_dir=Path(args.output_dir),
        private=args.private,
        max_concurrent=args.max_concurrent
    )

    # Initialize orchestrator
    orchestrator = ExperimentOrchestrator(config, augment_auth)

    if args.dry_run:
        logger.info("DRY RUN MODE - No actual changes will be made")
        return

    try:
        # Load ideas
        ideas = orchestrator.load_ideas(args.input)

        # Process ideas
        logger.info(f"Starting batch processing of {len(ideas)} ideas")
        results = orchestrator.run_batch(ideas)

        # Summarize results
        successful = [r for r in results if r.get('status') == 'completed']
        failed = [r for r in results if r.get('status') != 'completed']

        logger.info(f"Batch processing completed:")
        logger.info(f"  Successful: {len(successful)}")
        logger.info(f"  Failed: {len(failed)}")

        if successful:
            logger.info("Successful repositories:")
            for result in successful:
                logger.info(f"  - {result['repo']}: {result.get('workflow_url', 'N/A')}")

        if failed:
            logger.warning("Failed repositories:")
            for result in failed:
                logger.warning(f"  - {result['idea']}: {result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
