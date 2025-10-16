#!/usr/bin/env python3
"""
OpenHands Experiment Orchestrator

This script orchestrates the creation and execution of computational experiments using OpenHands Cloud.
It reads ideas from CSV/Excel, creates GitHub repositories with experiment templates,
and starts OpenHands Cloud conversations to plan, execute, and interpret experiments.

Usage:
    python orchestrator.py [--input ideas.csv] [--max-concurrent 3]

Environment Variables:
    GITHUB_TOKEN: GitHub personal access token with repo creation permissions
    GITHUB_OWNER: GitHub username or organization name
    OPENHANDS_API_KEY: OpenHands Cloud API key

Note: OpenHands uses Cloud conversations for agent interactions.
This orchestrator sets up repositories and starts conversations that OpenHands monitors.
"""

import argparse
import base64
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
        logging.FileHandler('openhands_orchestrator.log'),
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
        default_branch = repo_data.get('default_branch', 'main')  # Get actual default branch
        
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


class OpenHandsClient:
    """Client for OpenHands Cloud API operations."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        self.api_base = 'https://app.all-hands.dev/api'

    def start_conversation(self, repo_full_name: str, initial_message: str) -> str:
        """
        Start a new OpenHands Cloud conversation.

        Args:
            repo_full_name: Full GitHub repository name (owner/repo)
            initial_message: Initial instruction for OpenHands

        Returns:
            Conversation ID
        """
        payload = {
            "initial_user_msg": initial_message,
            "repository": repo_full_name
        }

        response = self.session.post(f'{self.api_base}/conversations', json=payload)
        response.raise_for_status()

        conversation_id = response.json()['conversation_id']
        logger.info(f"Started OpenHands conversation: {conversation_id}")
        return conversation_id

    def send_message(self, conversation_id: str, message: str) -> bool:
        """
        Send a message to an ongoing conversation.

        Args:
            conversation_id: OpenHands conversation ID
            message: Message content

        Returns:
            Success status
        """
        payload = {
            "role": "user",
            "content": message
        }

        response = self.session.post(
            f'{self.api_base}/conversations/{conversation_id}/messages',
            json=payload
        )
        response.raise_for_status()
        return True

    def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get the current status of a conversation.

        Args:
            conversation_id: OpenHands conversation ID

        Returns:
            Conversation status data
        """
        response = self.session.get(f'{self.api_base}/conversations/{conversation_id}')
        response.raise_for_status()
        return response.json()

    def poll_conversation(self, conversation_id: str, timeout_minutes: int = 300) -> Dict[str, Any]:
        """
        Poll a conversation until it completes or times out.

        Args:
            conversation_id: OpenHands conversation ID
            timeout_minutes: Maximum time to wait (default: 300 minutes = 5 hours)

        Returns:
            Final conversation status
        """
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60

        while time.time() - start_time < timeout_seconds:
            status = self.get_conversation_status(conversation_id)
            conversation_status = status.get('status', '')

            if conversation_status in ('idle', 'completed', 'error'):
                logger.info(f"Conversation {conversation_id} finished with status: {conversation_status}")
                return status

            logger.debug(f"Conversation {conversation_id} status: {conversation_status}")
            time.sleep(30)  # Poll every 30 seconds

        logger.warning(f"Conversation {conversation_id} timed out after {timeout_minutes} minutes")
        return {'status': 'timeout', 'conversation_id': conversation_id}


class OpenHandsOrchestrator:
    """Main orchestrator for creating and managing experiment repositories for OpenHands."""

    def __init__(self, config: RepoConfig, openhands_api_key: str):
        self.config = config
        self.github = GitHubClient(config.token, config.owner)
        self.openhands = OpenHandsClient(openhands_api_key)

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
        # Generate a clean repo name with provider suffix
        repo_name = slugify(idea.title, max_length=70, word_boundary=True)  # Leave room for "-openhands"
        if len(repo_name) == 0:
            repo_name = f"experiment-{int(time.time())}"
        
        # Append provider name to avoid conflicts when running same experiment on multiple providers
        repo_name = f"{repo_name}-openhands"

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
                private=True
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
            f'# {repo_full_name.split("/")[1]}\n\nInitializing experiment repository for OpenHands...\n',
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
        """Seed the repository with experiment templates and configuration for OpenHands."""
        logger.info(f"Seeding repository: {repo_full_name}")

        # Create temporary directory for file operations
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir) / 'repo'

            # Copy template files to the repository
            self._copy_template_files(repo_full_name, idea)

            # Customize experiment configuration
            self._customize_experiments(repo_full_name, idea)

            logger.info(f"Repository {repo_full_name} seeded successfully for OpenHands")

    def _copy_template_files(self, repo_full_name: str, idea: ExperimentIdea):
        """Copy template files to the repository for OpenHands integration."""
        template_dir = Path(__file__).parent / 'templates'

        # Files to copy from templates
        template_files = {
            'AGENTS.md': 'AGENTS.md',
            'microagent_repo.md': '.openhands/microagents/repo.md',
            'experiments.yaml': 'experiments/experiments.yaml',
            'runner.py': 'runner.py',
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
                'openhands_ready': True
            }, indent=2),
            'README.template.md': self._generate_readme_template(idea),
            '.gitignore': self._generate_gitignore()
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
        """Generate a README template for OpenHands-managed repos."""
        pipeline_type = "pre-defined experiments" if idea.has_experiments else "AI-planned experiments"
        
        return f'''# {idea.title}

{idea.idea or "Experiment repository managed by OpenHands."}

## Overview

This repository contains a computational experiment designed to validate the idea: **{idea.title}**.

**Pipeline Type:** {pipeline_type}

{f"**Pre-defined Experiments:** This idea includes specific experiments to execute." if idea.has_experiments else "**AI Planning:** OpenHands will analyze the idea and generate a comprehensive experiment plan."}

The experiments are {"provided in" if idea.has_experiments else "planned and defined in"} `experiments/experiments.yaml` and executed via GitHub Actions.
OpenHands monitors the CI pipeline and automatically iterates on any failures.

## OpenHands Integration

This repository is configured for OpenHands Cloud monitoring:

1. **Import** this repository into OpenHands Cloud
2. **Start a conversation** with the initial experiment planning prompt
3. **Monitor CI steps** that OpenHands will watch and iterate on
4. **Let OpenHands** handle the iterative improvement and final README generation

## Experiment Results

Results and artifacts will be stored in the `artifacts/` directory after experiment execution.

## Getting Started

1. Import this repository into OpenHands Cloud
2. Start a conversation with the experiment planning prompt
3. Push changes to trigger monitored workflows
4. OpenHands will monitor and iterate automatically

## Generated by OpenHands Orchestrator

This repository was automatically created and configured using the OpenHands experiment orchestrator.
Pipeline: {pipeline_type}
OpenHands will handle the iterative improvement and final README generation.
'''

    def _generate_gitignore(self) -> str:
        """Generate .gitignore content - SELECTIVE to commit important artifacts."""
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

# Experiments - SELECTIVE IGNORING
# Ignore large binary files but KEEP important results
artifacts/**/*.pkl
artifacts/**/*.h5
artifacts/**/*.pt
artifacts/**/*.pth
artifacts/**/*.ckpt
artifacts/**/*.model
artifacts/**/*.bin
artifacts/**/*.weights

# KEEP these artifact files (override above patterns)
!artifacts/**/*.json
!artifacts/**/*.yaml
!artifacts/**/*.yml
!artifacts/**/*.md
!artifacts/**/*.txt
!artifacts/**/*.csv
!artifacts/**/*.png
!artifacts/**/*.jpg
!artifacts/**/*.svg

# Cache
.cache/
*.log

# OpenHands
.openhands/
'''

    def _generate_results_quality_requirements(self) -> str:
        """
        Generate detailed requirements for publication-quality RESULTS.md.
        This ensures OpenHands produces comprehensive, visual, and insightful results.
        """
        return """
═══════════════════════════════════════════════════════════════════
CRITICAL: RESULTS.MD QUALITY REQUIREMENTS
═══════════════════════════════════════════════════════════════════

Your RESULTS.md MUST be publication-quality with:

1. VISUALIZATIONS (MANDATORY):
   - Create matplotlib/seaborn plots for ALL key metrics
   - Save plots to artifacts/plots/ directory as PNG files
   - Embed ALL plots in RESULTS.md using relative paths
   
   Required plot types:
   • Bar charts comparing model/approach performance
   • Line plots showing training curves or trends over time
   • Confusion matrices for classification tasks
   • ROC curves for binary classification
   • Scatter plots for correlation analysis
   • Heatmaps for feature importance or correlation matrices
   
   Example code for creating plots:
   ```python
   import matplotlib.pyplot as plt
   import seaborn as sns
   
   # Bar chart example
   plt.figure(figsize=(10, 6))
   plt.bar(model_names, accuracies)
   plt.xlabel('Model')
   plt.ylabel('Accuracy')
   plt.title('Model Comparison')
   plt.savefig('artifacts/plots/model_comparison.png')
   
   # Learning curves example
   plt.figure(figsize=(10, 6))
   plt.plot(epochs, train_loss, label='Train')
   plt.plot(epochs, val_loss, label='Validation')
   plt.xlabel('Epoch')
   plt.ylabel('Loss')
   plt.legend()
   plt.savefig('artifacts/plots/learning_curves.png')
   ```
   
   Then in RESULTS.md, use this format:
   ```markdown
   ## Results

   ### Model Performance
   ![Model Comparison](artifacts/plots/model_comparison.png)

   The bar chart shows...

   ### Training Progress
   ![Learning Curves](artifacts/plots/learning_curves.png)

   The learning curves indicate...
   ```

2. COMPREHENSIVE METRICS:
   Create a detailed metrics table with:
   • Primary metrics (accuracy, F1, RMSE, etc.)
   • Secondary metrics (precision, recall, AUC, etc.)
   • Performance metrics (training time, inference time, memory)
   • Statistical significance (p-values, confidence intervals)
   
   Example table format:
   ```markdown
   | Model | Accuracy | F1-Score | Precision | Recall | Train Time | Inference Time |
   |-------|----------|----------|-----------|--------|------------|----------------|
   | Model A | 0.95 | 0.94 | 0.96 | 0.92 | 120s | 0.5ms |
   | Model B | 0.92 | 0.91 | 0.89 | 0.93 | 45s | 0.2ms |
   ```

3. DEEP ANALYSIS:
   • Error Analysis: What types of inputs cause failures?
   • Comparative Insights: Why does one approach outperform another?
   • Trade-offs: Speed vs accuracy, complexity vs performance
   • Limitations: What doesn't work well? Edge cases?
   • Unexpected Findings: Surprises in the data or results

4. IMPLEMENTATION DETAILS:
   • Hyperparameters used
   • Data preprocessing steps
   • Model architectures or algorithm details
   • Random seeds and reproducibility info

5. CLEAR NEXT STEPS:
   • Specific improvements to try
   • Follow-up experiments
   • Deployment considerations
   • Open questions

REMEMBER: A good RESULTS.md tells a complete story with data, visuals, and insights!
"""

    def start_openhands_conversation(self, repo_full_name: str, idea: ExperimentIdea) -> str:
        """Start an OpenHands Cloud conversation for the experiment."""
        logger.info(f"Starting OpenHands conversation for {repo_full_name}")
        logger.info(f"  Pipeline type: {'Pre-defined experiments' if idea.has_experiments else 'AI planning required'}")

        # Get results quality requirements
        results_requirements = self._generate_results_quality_requirements()

        if idea.has_experiments:
            # Pre-defined experiments - OpenHands should validate and implement
            initial_prompt = f"""
You are managing a computational experiment repository at {repo_full_name}.

The experiment idea is: "{idea.title}"
Description: {idea.idea}

IMPORTANT: This idea comes with PRE-DEFINED EXPERIMENTS in experiments/experiments.yaml.

═══════════════════════════════════════════════════════════════════
WORKFLOW - EXECUTE IN THIS ORDER:
═══════════════════════════════════════════════════════════════════

PHASE 1: SETUP & VALIDATION
1. Review AGENTS.md and .openhands/microagents/repo.md for guidance
2. Examine experiments/experiments.yaml to understand the experiment plan
3. Validate that all experiment steps are clear and achievable
4. Check requirements.txt and install dependencies

PHASE 2: IMPLEMENTATION
5. Implement all missing code/scripts for experiment steps
6. Create data preparation scripts if needed
7. Implement baseline and main experiment code
8. Add proper error handling and logging

PHASE 3: EXECUTION
9. Run the experiment pipeline step by step
10. Monitor for failures and fix sanity check issues
11. Collect all metrics and outputs
12. Generate visualizations (MANDATORY - see requirements below)

PHASE 4: ANALYSIS & DOCUMENTATION
13. Analyze results thoroughly
14. Create RESULTS.md with visualizations, metrics, and insights
15. Update README.md with comprehensive findings
16. Document limitations and next steps

{results_requirements}

Start by examining the pre-defined experiment plan and implementing the required code.
"""
        else:
            # AI needs to plan experiments from scratch
            initial_prompt = f"""
You are managing a computational experiment repository at {repo_full_name}.

The experiment idea is: "{idea.title}"
Description: {idea.idea}

IMPORTANT: You need to DESIGN THE EXPERIMENT PLAN from scratch.

═══════════════════════════════════════════════════════════════════
WORKFLOW - EXECUTE IN THIS ORDER:
═══════════════════════════════════════════════════════════════════

PHASE 1: PLANNING
1. Review AGENTS.md and .openhands/microagents/repo.md for guidance
2. Analyze the idea thoroughly - what is the research question?
3. Design a rigorous experiment plan with:
   • Clear hypothesis and success criteria
   • Baseline/control experiments for comparison
   • Main experimental approaches
   • Ordered steps with dependencies
   • Sanity checks for each step
4. Create experiments/experiments.yaml with your complete plan

PHASE 2: IMPLEMENTATION
5. Implement all code and scripts needed for the experiments
6. Create data preparation and preprocessing scripts
7. Implement baseline implementation (simple approach)
8. Implement main experimental approaches
9. Add proper error handling and logging

PHASE 3: EXECUTION
10. Run the experiment pipeline step by step
11. Monitor CI workflow and fix any failures
12. Collect comprehensive metrics and outputs
13. Generate visualizations (MANDATORY - see requirements below)

PHASE 4: ANALYSIS & DOCUMENTATION
14. Compare baseline vs experimental approaches
15. Perform deep analysis of results
16. Create RESULTS.md with visualizations, metrics, and insights
17. Update README.md with comprehensive findings
18. Document limitations and next steps

{results_requirements}

Start by designing a comprehensive experiment plan from the ground up.
"""

        conversation_id = self.openhands.start_conversation(repo_full_name, initial_prompt)
        return conversation_id

    def monitor_conversation(self, conversation_id: str, timeout_minutes: int = 300) -> Dict[str, Any]:
        """Monitor an OpenHands conversation until completion (default: 300 minutes = 5 hours)."""
        logger.info(f"Monitoring OpenHands conversation: {conversation_id}")

        final_status = self.openhands.poll_conversation(conversation_id, timeout_minutes)

        if final_status.get('status') == 'timeout':
            logger.warning(f"Conversation {conversation_id} monitoring timed out")
        else:
            logger.info(f"Conversation {conversation_id} completed with status: {final_status.get('status')}")

        return final_status

    def process_idea(self, idea: ExperimentIdea) -> Dict[str, Any]:
        """Process a single experiment idea from start to finish."""
        logger.info(f"Processing idea: {idea.title}")

        try:
            # 1. Create repository
            repo_full_name, default_branch = self.create_experiment_repo(idea)
            logger.info(f"Repository default branch: {default_branch}")

            # 2. Seed with templates for OpenHands
            self.seed_repository(repo_full_name, idea)

            # 3. Start OpenHands conversation
            conversation_id = self.start_openhands_conversation(repo_full_name, idea)

            # 4. Monitor conversation (optional - can run asynchronously)
            # In production, you might want to monitor or just return the conversation ID
            # conversation_status = self.monitor_conversation(conversation_id)

            return {
                'idea': idea.title,
                'repo': repo_full_name,
                'status': 'conversation_started',
                'conversation_id': conversation_id,
                'openhands_ready': True,
                'instructions': f'OpenHands conversation started. Monitor at: https://app.all-hands.dev/conversations/{conversation_id}'
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
    parser = argparse.ArgumentParser(description="OpenHands Experiment Orchestrator")
    parser.add_argument(
        '--input',
        default='../../data/ideas.csv',
        help='Path to CSV/Excel file with experiment ideas'
    )
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=3,
        help='Maximum number of concurrent repository operations'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )
    parser.add_argument(
        '--monitor-timeout',
        type=int,
        default=300,
        help='Timeout in minutes for monitoring conversations (default: 300 = 5 hours)'
    )

    args = parser.parse_args()

    # Validate environment
    github_token = os.environ.get('GITHUB_TOKEN')
    github_owner = os.environ.get('GITHUB_OWNER')
    openhands_api_key = os.environ.get('OPENHANDS_API_KEY')

    if not all([github_token, github_owner, openhands_api_key]):
        logger.error("Missing required environment variables:")
        logger.error("  GITHUB_TOKEN: GitHub personal access token")
        logger.error("  GITHUB_OWNER: GitHub username or organization")
        logger.error("  OPENHANDS_API_KEY: OpenHands Cloud API key")
        sys.exit(1)

    # Setup configuration
    config = RepoConfig(
        owner=github_owner,
        token=github_token,
        max_concurrent=args.max_concurrent
    )

    # Initialize orchestrator
    orchestrator = OpenHandsOrchestrator(config, openhands_api_key)

    if args.dry_run:
        logger.info("DRY RUN MODE - No actual changes will be made")
        return

    try:
        # Load ideas
        ideas = orchestrator.load_ideas(args.input)

        # Process ideas
        logger.info(f"Starting batch processing of {len(ideas)} ideas for OpenHands")
        results = orchestrator.run_batch(ideas)

        # Summarize results
        successful = [r for r in results if r.get('status') == 'conversation_started']
        failed = [r for r in results if r.get('status') != 'conversation_started']

        logger.info(f"Batch processing completed:")
        logger.info(f"  OpenHands conversations started: {len(successful)}")
        logger.info(f"  Failed: {len(failed)}")

        if successful:
            logger.info("Started conversations:")
            for result in successful:
                logger.info(f"  - {result['repo']}: {result.get('conversation_id', 'N/A')}")

        if failed:
            logger.warning("Failed repositories:")
            for result in failed:
                logger.warning(f"  - {result['idea']}: {result.get('error', 'Unknown error')}")

        logger.info("\nNext steps:")
        logger.info("1. Monitor OpenHands conversations at https://app.all-hands.dev")
        logger.info("2. OpenHands will iterate on CI failures automatically")
        logger.info("3. Check generated artifacts and final READMEs in repositories")

    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

