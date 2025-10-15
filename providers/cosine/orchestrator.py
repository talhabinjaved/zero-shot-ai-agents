#!/usr/bin/env python3
"""
Cosine Experiment Orchestrator

This script orchestrates the creation and setup of computational experiments for Cosine.
It reads ideas from CSV/Excel, creates GitHub repositories with experiment templates,
and prepares them for import into Cosine where the agent will monitor CI and auto-iterate.

Usage:
    python orchestrator.py [--input ideas.csv] [--output-dir repos/] [--max-concurrent 3]

Environment Variables:
    GITHUB_TOKEN: GitHub personal access token with repo creation permissions
    GITHUB_OWNER: GitHub username or organization name

Note: Unlike Augment, Cosine doesn't have a direct API. This orchestrator sets up
repositories that users import into Cosine for monitoring and iteration.
"""

import argparse
import base64
import csv
import json
import os
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
        logging.FileHandler('cosine_orchestrator.log'),
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

    def trigger_workflow(self, repo_full_name: str, workflow_name: str, inputs: Dict[str, Any] = None) -> bool:
        """Trigger a workflow dispatch event."""
        url = f'{self.api_base}/repos/{repo_full_name}/actions/workflows/{workflow_name}/dispatches'

        payload = {
            'ref': 'main',
            'inputs': inputs or {}
        }

        response = self.session.post(url, json=payload)
        return response.status_code == 204


class CosineOrchestrator:
    """Main orchestrator for creating and managing experiment repositories for Cosine."""

    def __init__(self, config: RepoConfig):
        self.config = config
        self.github = GitHubClient(config.token, config.owner)

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
        existing_repos = []  # In a real implementation, you might cache this
        while f"{self.config.owner}/{repo_name}" in existing_repos:
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
            f'# {repo_full_name.split("/")[1]}\n\nInitializing experiment repository for Cosine...\n',
            'chore: initialize repository'
        )
        
        # After first commit, fetch the actual default branch name
        time.sleep(1)  # Give GitHub a moment to process
        repo_info = self.github.get_repo(repo_full_name)
        actual_branch = repo_info['default_branch']
        
        if actual_branch != expected_branch:
            logger.info(f"Repository initialized with '{actual_branch}' branch (expected '{expected_branch}')")
        
        return actual_branch

    def seed_repository(self, repo_full_name: str, idea: ExperimentIdea):
        """Seed the repository with experiment templates and configuration for Cosine."""
        logger.info(f"Seeding repository: {repo_full_name}")

        # Create temporary directory for file operations
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir) / 'repo'

            # Copy template files to the repository
            self._copy_template_files(repo_full_name, idea)

            # Customize experiment configuration
            self._customize_experiments(repo_full_name, idea)

            logger.info(f"Repository {repo_full_name} seeded successfully for Cosine")

    def _copy_template_files(self, repo_full_name: str, idea: ExperimentIdea):
        """Copy template files to the repository for Cosine integration."""
        template_dir = Path(__file__).parent / 'templates'

        # Files to copy from templates
        template_files = {
            'experiments.yaml': 'experiments/experiments.yaml',
            'executor.py': 'executor.py',
            'workflow.yml': '.github/workflows/run-experiments.yml'
        }

        for template_file, repo_path in template_files.items():
            template_path = template_dir / template_file
            if template_path.exists():
                with open(template_path, 'r') as f:
                    content = f.read()

                # Basic templating - replace placeholders
                content = content.replace('{{REPO_NAME}}', repo_full_name.split('/')[1])
                content = content.replace('{{IDEA_TITLE}}', idea.title)
                content = content.replace('{{IDEA_DESCRIPTION}}', idea.idea or '')

                self.github.put_file(
                    repo_full_name,
                    repo_path,
                    content,
                    f'add {repo_path}'
                )

        # Add additional scaffold files
        scaffold_files = {
            'requirements.txt': self._generate_requirements(idea),
            'experiments/idea.json': json.dumps({
                'title': idea.title,
                'idea': idea.idea,
                'has_experiments': idea.has_experiments,
                'experiments': idea.experiments,
                'data_url': idea.data_url,
                'timestamp': time.time(),
                'cosine_ready': True
            }, indent=2),
            'README.template.md': self._generate_readme_template(idea),
            '.gitignore': self._generate_gitignore(),
            'COSINE_SETUP.md': self._generate_cosine_setup_instructions(repo_full_name, idea)
        }

        for file_path, content in scaffold_files.items():
            self.github.put_file(
                repo_full_name,
                file_path,
                content,
                f'add {file_path}'
            )

    def _customize_experiments(self, repo_full_name: str, idea: ExperimentIdea):
        """Customize the experiments.yaml based on the idea."""
        if idea.has_experiments and idea.experiments:
            # Use the provided experiments configuration
            self.github.put_file(
                repo_full_name,
                'experiments/experiments.yaml',
                idea.experiments,
                'add pre-defined experiments configuration'
            )

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
        """Generate a README template for Cosine-managed repos."""
        pipeline_type = "pre-defined experiments" if idea.has_experiments else "AI-planned experiments"
        
        return f'''# {idea.title}

{idea.idea or "Experiment repository managed by Cosine AI."}

## Overview

This repository contains a computational experiment designed to validate the idea: **{idea.title}**.

**Pipeline Type:** {pipeline_type}

{f"**Pre-defined Experiments:** This idea includes specific experiments to execute." if idea.has_experiments else "**AI Planning:** Cosine will analyze the idea and generate a comprehensive experiment plan."}

The experiments are {"provided in" if idea.has_experiments else "planned and defined in"} `experiments/experiments.yaml` and executed via GitHub Actions.
Cosine monitors the CI pipeline and automatically iterates on any failures.

## Cosine Integration

This repository is configured for Cosine AI monitoring:

1. **Import** this repository into your Cosine workspace
2. **Configure CI monitoring** in Project Settings → Workflows
3. **Monitor the steps** Cosine will watch: `run_step`, `run_pipeline`, etc.
4. **Let Cosine iterate** automatically when CI steps fail

## Experiment Results

Results and artifacts will be stored in the `artifacts/` directory after experiment execution.

## Getting Started

1. Import this repository into Cosine
2. Configure CI monitoring in Cosine Project Settings
3. Push changes to trigger experiments
4. Cosine will monitor and iterate automatically

## Generated by Cosine Orchestrator

This repository was automatically created and configured using the Cosine experiment orchestrator.
Pipeline: {pipeline_type}
Cosine will handle the iterative improvement and final README generation.
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

# Cosine
.cosine/
'''

    def _generate_cosine_setup_instructions(self, repo_full_name: str, idea: ExperimentIdea) -> str:
        """Generate setup instructions for Cosine users."""
        return f'''# Cosine Setup Instructions for {repo_full_name}

## Overview
This repository has been prepared for Cosine AI monitoring and iteration. Follow these steps to set up automated experiment execution.

## Step 1: Import Repository
1. Go to your Cosine workspace
2. Click "Import Repository"
3. Select this repository: `{repo_full_name}`

## Step 2: Configure CI Monitoring
In your Cosine Project Settings → Workflows:

### Required CI Steps to Monitor:
- `run_step` (individual experiment steps)
- `run_pipeline` (complete experiment pipeline)
- `validate` (configuration validation)

### Optional CI Steps:
- `run_large_scale` (for resource-intensive experiments)
- `deploy_site` (for Instant Sites deployment)

## Step 3: Configure Auto-Iteration
- Enable "Auto-accept" for low-touch iterations
- Set "Think" mode for complex problem-solving
- Configure retry limits and backoff strategies

## Experiment Structure
```
experiments/experiments.yaml    # Experiment plan and sanity checks
executor.py                     # CI execution script
.github/workflows/             # GitHub Actions workflows
artifacts/                      # Results and logs (generated)
```

## Idea Summary
**Title:** {idea.title}
**Description:** {idea.idea or "No description provided"}
**Pipeline Type:** {"Pre-defined experiments" if idea.has_experiments else "AI planning required"}

## Monitoring
Once configured, Cosine will:
1. Monitor CI workflow execution
2. Automatically iterate when steps fail sanity checks
3. Generate comprehensive READMEs with results
4. Create polished documentation for stakeholders

## Troubleshooting
- Check CI logs in GitHub Actions
- Review `artifacts/` directory for detailed results
- Ensure all CI steps are properly configured in Cosine settings

---
*Generated by Cosine Orchestrator*
'''

    def setup_cosine_monitoring(self, repo_full_name: str) -> bool:
        """Prepare repository for Cosine monitoring (log instructions for user)."""
        logger.info(f"Repository {repo_full_name} ready for Cosine import")
        logger.info("User needs to:")
        logger.info("1. Import repository into Cosine workspace")
        logger.info("2. Configure CI monitoring in Project Settings")
        logger.info("3. Enable auto-iteration features")
        return True

    def trigger_initial_workflow(self, repo_full_name: str) -> bool:
        """Optionally trigger an initial workflow to test setup."""
        logger.info(f"Triggering initial validation workflow for {repo_full_name}")

        success = self.github.trigger_workflow(
            repo_full_name,
            'run-experiments.yml',
            inputs={'config_file': 'experiments/experiments.yaml'}
        )

        if success:
            logger.info(f"Initial workflow triggered for {repo_full_name}")
        else:
            logger.warning(f"Failed to trigger initial workflow for {repo_full_name}")

        return success

    def process_idea(self, idea: ExperimentIdea) -> Dict[str, Any]:
        """Process a single experiment idea from start to finish."""
        logger.info(f"Processing idea: {idea.title}")

        try:
            # 1. Create repository
            repo_full_name, default_branch = self.create_experiment_repo(idea)
            logger.info(f"Repository default branch: {default_branch}")

            # 2. Seed with templates for Cosine
            self.seed_repository(repo_full_name, idea)

            # 3. Prepare for Cosine monitoring
            cosine_ready = self.setup_cosine_monitoring(repo_full_name)

            # 4. Optionally trigger initial validation
            workflow_triggered = self.trigger_initial_workflow(repo_full_name)

            return {
                'idea': idea.title,
                'repo': repo_full_name,
                'status': 'cosine_ready',
                'cosine_ready': cosine_ready,
                'workflow_triggered': workflow_triggered,
                'setup_instructions': f'Check COSINE_SETUP.md in {repo_full_name} for detailed instructions'
            }

        except Exception as e:
            logger.error(f"Error processing idea {idea.title}: {e}")
            return {
                'idea': idea.title,
                'status': 'error',
                'error': str(e)
            }

    def run_batch(self, ideas: List[ExperimentIdea]) -> List[Dict[str, Any]]:
        """Process multiple ideas with concurrency control."""
        results = []

        for idea in ideas:
            result = self.process_idea(idea)
            results.append(result)

        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Cosine Experiment Orchestrator")
    parser.add_argument(
        '--input',
        default='../ideas.csv',
        help='Path to CSV/Excel file with experiment ideas'
    )
    parser.add_argument(
        '--output-dir',
        default='./cosine_repos',
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
        '--trigger-workflows',
        action='store_true',
        help='Trigger initial validation workflows after setup'
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

    if not all([github_token, github_owner]):
        logger.error("Missing required environment variables:")
        logger.error("  GITHUB_TOKEN: GitHub personal access token")
        logger.error("  GITHUB_OWNER: GitHub username or organization")
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
    orchestrator = CosineOrchestrator(config)

    if args.dry_run:
        logger.info("DRY RUN MODE - No actual changes will be made")
        return

    try:
        # Load ideas
        ideas = orchestrator.load_ideas(args.input)

        # Process ideas
        logger.info(f"Starting batch processing of {len(ideas)} ideas for Cosine")
        results = orchestrator.run_batch(ideas)

        # Summarize results
        successful = [r for r in results if r.get('status') == 'cosine_ready']
        failed = [r for r in results if r.get('status') != 'cosine_ready']

        logger.info(f"Batch processing completed:")
        logger.info(f"  Cosine-ready: {len(successful)}")
        logger.info(f"  Failed: {len(failed)}")

        if successful:
            logger.info("Cosine-ready repositories:")
            for result in successful:
                logger.info(f"  - {result['repo']}: {result.get('setup_instructions', 'Ready for import')}")

        if failed:
            logger.warning("Failed repositories:")
            for result in failed:
                logger.warning(f"  - {result['idea']}: {result.get('error', 'Unknown error')}")

        logger.info("\nNext steps:")
        logger.info("1. Import each repository into your Cosine workspace")
        logger.info("2. Configure CI monitoring in Cosine Project Settings")
        logger.info("3. Enable auto-iteration and auto-accept features")
        logger.info("4. Push changes to trigger monitored workflows")

    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
