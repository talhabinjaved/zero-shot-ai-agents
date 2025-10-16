#!/usr/bin/env python3
"""
Jules Experiment Orchestrator

This script orchestrates the creation and execution of computational experiments using Jules.
It reads ideas from CSV/Excel, creates GitHub repositories with experiment templates,
and starts Jules sessions via API to plan, execute, and interpret experiments.

Usage:
    python orchestrator.py [--input ideas.csv] [--max-concurrent 3]

Environment Variables:
    GITHUB_TOKEN: GitHub personal access token with repo creation permissions
    GITHUB_OWNER: GitHub username or organization name
    JULES_API_KEY: Jules API key from jules.google Settings

Note: Jules uses sessions for agent interactions via REST API.
This orchestrator sets up repositories and starts sessions that Jules executes asynchronously.
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
        logging.FileHandler('jules_orchestrator.log'),
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
            'auto_init': True  # Jules requires an initial commit
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

    def create_issue(self, repo_full_name: str, title: str, body: str, labels: List[str] = None) -> str:
        """Create a GitHub issue."""
        url = f'{self.api_base}/repos/{repo_full_name}/issues'

        payload = {
            'title': title,
            'body': body,
            'labels': labels or []
        }

        response = self.session.post(url, json=payload)
        response.raise_for_status()

        return response.json()['html_url']


class JulesClient:
    """Client for Jules REST API operations."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-Goog-Api-Key': api_key,
            'Content-Type': 'application/json'
        })
        self.api_base = 'https://jules.googleapis.com/v1alpha'

    def list_sources(self) -> List[Dict[str, Any]]:
        """List all GitHub repositories connected to Jules."""
        response = self.session.get(f'{self.api_base}/sources')
        response.raise_for_status()
        return response.json().get('sources', [])

    def create_session(self, owner: str, repo: str, prompt: str, title: str,
                      starting_branch: str = 'main',
                      require_plan_approval: bool = False,
                      auto_create_pr: bool = False) -> str:
        """
        Create a new Jules session.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            prompt: Initial prompt for Jules
            title: Session title
            starting_branch: Git branch to use (default: 'main')
            require_plan_approval: Whether to require manual plan approval
            auto_create_pr: Whether to automatically create PR

        Returns:
            Session ID
        """
        source_name = f'sources/github/{owner}/{repo}'

        payload = {
            'prompt': prompt,
            'title': title,
            'sourceContext': {
                'source': source_name,
                'githubRepoContext': {
                    'startingBranch': starting_branch
                }
            }
        }

        if require_plan_approval:
            payload['requirePlanApproval'] = True

        if auto_create_pr:
            payload['automationMode'] = 'AUTO_CREATE_PR'

        try:
            response = self.session.post(f'{self.api_base}/sessions', json=payload)
            response.raise_for_status()

            session_data = response.json()
            session_id = session_data.get('id')
            
            if not session_id:
                # Try to extract from name field (format: "sessions/123456")
                name = session_data.get('name', '')
                if '/' in name:
                    session_id = name.split('/')[-1]
            
            logger.info(f"Created Jules session: {session_id}")
            logger.info(f"Session URL: https://jules.google.com/session/{session_id}")
            return session_id
            
        except requests.HTTPError as e:
            logger.error(f"Failed to create Jules session: {e}")
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text[:500]}")
            logger.error(f"Request payload: {json.dumps(payload, indent=2)[:500]}")
            raise

    def list_activities(self, session_id: str) -> List[Dict[str, Any]]:
        """
        List activities for a session.

        Args:
            session_id: Jules session ID

        Returns:
            List of activity objects
        """
        response = self.session.get(f'{self.api_base}/sessions/{session_id}/activities?pageSize=50')
        response.raise_for_status()
        return response.json().get('activities', [])

    def approve_plan(self, session_id: str) -> bool:
        """
        Approve a plan for a session.

        Args:
            session_id: Jules session ID

        Returns:
            Success status
        """
        response = self.session.post(f'{self.api_base}/sessions/{session_id}:approvePlan')
        response.raise_for_status()
        logger.info(f"Approved plan for session: {session_id}")
        return True

    def send_message(self, session_id: str, message: str) -> bool:
        """
        Send a message to an ongoing session.

        Args:
            session_id: Jules session ID
            message: Message content

        Returns:
            Success status
        """
        payload = {
            'prompt': message
        }

        response = self.session.post(
            f'{self.api_base}/sessions/{session_id}:sendMessage',
            json=payload
        )
        response.raise_for_status()
        logger.info(f"Sent message to session: {session_id}")
        return True

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get session details including outputs (PR URL, etc).

        Args:
            session_id: Jules session ID

        Returns:
            Session data
        """
        response = self.session.get(f'{self.api_base}/sessions/{session_id}')
        response.raise_for_status()
        return response.json()


class JulesOrchestrator:
    """Main orchestrator for creating and managing experiment repositories for Jules."""

    def __init__(self, config: RepoConfig, jules_api_key: str):
        self.config = config
        self.github = GitHubClient(config.token, config.owner)
        self.jules = JulesClient(jules_api_key)

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

    def create_experiment_repo(self, idea: ExperimentIdea) -> Tuple[str, str, str]:
        """Create a GitHub repository for an experiment idea.
        
        Returns:
            Tuple of (full_name, repo_name, default_branch)
        """
        # Generate a clean repo name with provider suffix
        repo_name = slugify(idea.title, max_length=70, word_boundary=True)  # Leave room for "-jules"
        if len(repo_name) == 0:
            repo_name = f"experiment-{int(time.time())}"
        
        # Append provider name to avoid conflicts when running same experiment on multiple providers
        repo_name = f"{repo_name}-jules"

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

            # Wait for repository initialization
            time.sleep(2)

            return repo_info['full_name'], repo_name, repo_info['default_branch']

        except requests.HTTPError as e:
            if e.response.status_code == 422:  # Repository already exists
                logger.warning(f"Repository {self.config.owner}/{repo_name} already exists, using existing")
                full_name = f"{self.config.owner}/{repo_name}"
                
                # Get the existing repo's default branch
                existing_repo_info = self.github.get_repo(full_name)
                default_branch = existing_repo_info['default_branch']
                logger.info(f"Existing repository default branch: {default_branch}")
                
                return full_name, repo_name, default_branch
            else:
                raise

    def seed_repository(self, repo_full_name: str, idea: ExperimentIdea):
        """Seed the repository with experiment templates and configuration for Jules."""
        logger.info(f"Seeding repository: {repo_full_name}")

        # Create temporary directory for file operations
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir) / 'repo'

            # Copy template files to the repository
            self._copy_template_files(repo_full_name, idea)

            # Customize experiment configuration
            self._customize_experiments(repo_full_name, idea)

            logger.info(f"Repository {repo_full_name} seeded successfully for Jules")

    def _copy_template_files(self, repo_full_name: str, idea: ExperimentIdea):
        """Copy template files to the repository for Jules integration."""
        template_dir = Path(__file__).parent / 'templates'

        # Files to copy from templates
        template_files = {
            'AGENTS.md': 'AGENTS.md',
            'experiments.yaml': 'experiments/manifest.yaml',
            'runner.py': 'scripts/run_experiment.py',
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
                'jules_ready': True
            }, indent=2),
            'experiments/config.yaml': self._generate_config(idea),
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
        """Customize the experiments manifest based on the idea."""
        if idea.has_experiments and idea.experiments:
            # Use the provided experiments configuration
            self.github.put_file(
                repo_full_name,
                'experiments/manifest.yaml',
                idea.experiments,
                'add pre-defined experiments manifest'
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
            'tqdm',
            'pytest'
        ]

        if idea.requirements:
            # Add idea-specific requirements
            additional_reqs = [req.strip() for req in idea.requirements.split(',')]
            base_reqs.extend(additional_reqs)

        return '\n'.join(base_reqs) + '\n'

    def _generate_config(self, idea: ExperimentIdea) -> str:
        """Generate experiment config.yaml."""
        config = {
            'random_seed': 42,
            'log_level': 'INFO',
            'output_dir': 'results',
            'cache_dir': '.cache'
        }

        if idea.data_url:
            config['data_url'] = idea.data_url

        return yaml.safe_dump(config, sort_keys=False)

    def _generate_readme_template(self, idea: ExperimentIdea) -> str:
        """Generate a README template for Jules-managed repos."""
        pipeline_type = "pre-defined experiments" if idea.has_experiments else "AI-planned experiments"
        
        return f'''# {idea.title}

{idea.idea or "Experiment repository managed by Jules."}

## Overview

This repository contains a computational experiment designed to validate the idea: **{idea.title}**.

**Pipeline Type:** {pipeline_type}

{f"**Pre-defined Experiments:** This idea includes specific experiments to execute." if idea.has_experiments else "**AI Planning:** Jules will analyze the idea and generate a comprehensive experiment plan."}

## Jules Integration

This repository is configured for Jules asynchronous agent:

1. **Jules session** started automatically via API
2. **Plan approval** required before execution (configurable)
3. **CI monitoring** Jules watches workflow runs and reads state.json
4. **Auto-iteration** Jules adapts based on validation failures

## Experiment Results

Results and state will be stored in the `results/` directory:
- `results/state.json` - Current step status and metrics
- `results/validation_*.json` - Validation results per step
- `results/logs/` - Execution logs

## Getting Started

Jules will:
1. Review AGENTS.md and manifest.yaml
2. {f"Validate and implement the provided experiment plan" if idea.has_experiments else "Design and implement a comprehensive experiment plan from scratch"}
3. Trigger CI workflows and monitor results
4. Iterate on failures based on state.json feedback
5. Generate final README and RESULTS.md

## Generated by Jules Orchestrator

This repository was automatically created and configured using the Jules experiment orchestrator.
Pipeline: {pipeline_type}
Jules will handle the iterative improvement and final documentation generation.
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
.cache/

# Results - Keep important outputs, ignore temp files
results/**/*.pkl
results/**/*.h5
results/**/*.pt
results/**/*.pth
results/**/*.ckpt
results/**/cache/
results/**/__pycache__/

# But KEEP these important files:
!results/**/*.json
!results/**/*.md
!results/**/*.csv
!results/**/*.png
!results/**/*.jpg
!results/**/*.svg
!results/**/*.html
!results/**/RESULTS.md
!results/**/EXPERIMENT_STATUS.md

# Artifacts (alternate directory) - same rules
artifacts/**/*.pkl
artifacts/**/*.h5
artifacts/**/*.pt
artifacts/**/*.pth
artifacts/**/*.ckpt
artifacts/**/cache/
artifacts/**/__pycache__/

!artifacts/**/*.json
!artifacts/**/*.md
!artifacts/**/*.csv
!artifacts/**/*.png
!artifacts/**/*.jpg
!artifacts/**/*.svg
!artifacts/**/*.html
!artifacts/**/RESULTS.md
!artifacts/**/EXPERIMENT_STATUS.md

# Jules
.jules/
'''

    def _generate_results_quality_requirements(self) -> str:
        """Generate comprehensive requirements for high-quality RESULTS.md"""
        return """
CRITICAL REQUIREMENTS FOR RESULTS.MD:

Your RESULTS.md MUST be comprehensive and publication-quality. Include ALL of the following:

1. **Visualizations (REQUIRED)**
   - Create plots in artifacts/plots/ directory
   - Embed them in RESULTS.md using markdown image syntax: `![Description](artifacts/plots/filename.png)`
   - Required plots:
     * Model comparison bar chart (all metrics side-by-side)
     * Learning curves (training vs validation over time)
     * Error distribution plot (where models fail)
     * Confusion matrix (if classification task)
     * Feature importance plot (what matters most)
   - Use matplotlib/seaborn, save as PNG files
   - Make plots publication-ready (labels, titles, legends)

2. **Comprehensive Metrics Table**
   - Include ALL models and ALL metrics in markdown tables
   - Add standard deviations where applicable
   - Show statistical significance (p-values if you ran tests)
   - Format example:
     | Model | Metric1 | Metric2 | Metric3 |
     |-------|---------|---------|---------|
     | Baseline | X.XX ± Y.YY | ... | ... |
     | Advanced | X.XX ± Y.YY | ... | ... |

3. **Deep Analysis (NOT just surface-level)**
   - **Error Analysis**: What did each model get wrong and WHY?
   - **Comparative Insights**: WHY does one model outperform another?
   - **Feature Analysis**: Which features/patterns matter most?
   - **Edge Cases**: Where do models struggle? Provide specific examples
   - **Statistical Validation**: Are differences statistically significant?

4. **Implementation Details**
   - Link to key code files: [Model Architecture](scripts/experiment.py#L10-L50)
   - Mention important hyperparameters used
   - Note any data preprocessing choices
   - Reproducibility: random seeds, library versions

5. **Conclusions & Next Steps**
   - Clear recommendations based on data
   - Specific next steps (not vague suggestions)
   - Known limitations and how to address them
   - Expected improvements from proposed changes

VISUALIZATION EXAMPLES:
```python
# In your experiment scripts, create plots like:
import matplotlib.pyplot as plt

# Model comparison
plt.figure(figsize=(10, 6))
plt.bar(model_names, accuracies)
plt.title('Model Performance Comparison')
plt.xlabel('Model')
plt.ylabel('Accuracy')
plt.savefig('artifacts/plots/model_comparison.png')

# Learning curves
plt.figure(figsize=(10, 6))
plt.plot(epochs, train_loss, label='Train')
plt.plot(epochs, val_loss, label='Validation')
plt.title('Learning Curves')
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

REMEMBER: A good RESULTS.md tells a complete story with data, visuals, and insights!
"""

    def start_jules_session(self, repo_full_name: str, idea: ExperimentIdea,
                           default_branch: str = 'main',
                           require_plan_approval: bool = True) -> str:
        """Start a Jules session for the experiment."""
        logger.info(f"Starting Jules session for {repo_full_name}")
        logger.info(f"  Pipeline type: {'Pre-defined experiments' if idea.has_experiments else 'AI planning required'}")
        logger.info(f"  Using branch: {default_branch}")

        owner, repo = repo_full_name.split('/')

        # Create comprehensive prompt for Jules based on pipeline type
        if idea.has_experiments:
            # Pre-defined experiments - Jules should validate and implement
            prompt = f"""
            Project: {idea.title}

            Idea: {idea.idea}

            IMPORTANT: This idea comes with PRE-DEFINED EXPERIMENTS.

            Goal:
            Review the experiments defined in experiments/manifest.yaml and execute them step-by-step.
            For each step:
            1. Validate the experiment design is sound
            2. Implement the code in scripts/ or src/
            3. Run the CI workflow with: gh workflow run run-experiments.yml -f step=<id>
            4. Read results/state.json for status, metrics, and any replan_suggestion
            5. If validation fails, adjust the implementation (code, hyperparams) and retry once
            6. Only proceed to next step when validation passes

            When all steps complete successfully:
            - Compile RESULTS.md with comprehensive findings (see requirements below)
            - Upgrade README with: abstract, methods, results, error bars, limitations, next steps
            - Open a PR with all changes

            {self._generate_results_quality_requirements()}

            Execute the provided experiment plan faithfully. Sequential dependency between steps is critical.
            """
        else:
            # AI needs to plan experiments from scratch
            prompt = f"""
            Project: {idea.title}

            Idea: {idea.idea}

            IMPORTANT: You need to DESIGN THE EXPERIMENT PLAN from scratch.

            Goal:
            1. Analyze the idea and design a comprehensive experiment plan
            2. Create experiments/manifest.yaml with ordered steps, dependencies, and sanity checks
            3. Include baseline/control experiments for comparison
            4. For each step you design:
               - Implement the code in scripts/ or src/
               - Run the CI workflow with: gh workflow run run-experiments.yml -f step=<id>
               - Read results/state.json for status, metrics, and any replan_suggestion
               - If validation fails, adjust the plan or implementation and retry once
               - Only proceed to next step when validation passes

            When all steps complete successfully:
            - Compile RESULTS.md with comprehensive findings (see requirements below)
            - Upgrade README with: abstract, methods, results, error bars, limitations, next steps
            - Open a PR with all changes

            {self._generate_results_quality_requirements()}

            Design a rigorous, falsifiable experiment plan. Sequential dependency between steps is critical.
            """

        session_id = self.jules.create_session(
            owner=owner,
            repo=repo,
            prompt=prompt,
            title=f"Experiment: {idea.title}",
            starting_branch=default_branch,
            require_plan_approval=require_plan_approval,
            auto_create_pr=True
        )

        return session_id

    def monitor_session(self, session_id: str, timeout_minutes: int = 300) -> Dict[str, Any]:
        """
        Monitor a Jules session until completion or timeout.

        Args:
            session_id: Jules session ID
            timeout_minutes: Maximum time to wait (default: 300 minutes = 5 hours)

        Returns:
            Final session status
        """
        logger.info(f"Monitoring Jules session: {session_id}")

        start_time = time.time()
        timeout_seconds = timeout_minutes * 60

        plan_approved = False

        while time.time() - start_time < timeout_seconds:
            # Get current activities
            activities = self.jules.list_activities(session_id)

            # Check if plan was generated and needs approval
            has_plan = any('planGenerated' in str(a) for a in activities)

            if has_plan and not plan_approved:
                logger.info(f"Plan generated for session {session_id}, approving...")
                self.jules.approve_plan(session_id)
                plan_approved = True

            # Check session status
            session = self.jules.get_session(session_id)

            # Jules sessions don't have a simple 'completed' status in the same way
            # We check for PR URL in outputs as a completion signal
            outputs = session.get('outputs', {})
            pr_url = outputs.get('pullRequest', {}).get('url')

            if pr_url:
                logger.info(f"Session {session_id} created PR: {pr_url}")
                return {
                    'status': 'completed',
                    'session_id': session_id,
                    'pr_url': pr_url
                }

            logger.debug(f"Session {session_id} still in progress...")
            time.sleep(30)  # Poll every 30 seconds

        logger.warning(f"Session {session_id} monitoring timed out after {timeout_minutes} minutes")
        return {
            'status': 'timeout',
            'session_id': session_id
        }

    def process_idea(self, idea: ExperimentIdea, require_plan_approval: bool = True) -> Dict[str, Any]:
        """Process a single experiment idea from start to finish."""
        logger.info(f"Processing idea: {idea.title}")

        try:
            # 1. Create repository
            repo_full_name, repo_name, default_branch = self.create_experiment_repo(idea)

            # 2. Seed with templates for Jules
            self.seed_repository(repo_full_name, idea)

            # Wait for Jules to index the new repository
            logger.info("Waiting for Jules to index repository...")
            time.sleep(20)  # Initial wait increased to 20 seconds
            
            # Verify the repository is available as a source (REQUIRED)
            max_retries = 6  # Increased from 3 to 6 attempts
            repository_indexed = False
            
            for attempt in range(max_retries):
                try:
                    sources = self.jules.list_sources()
                    source_names = [s.get('name', '') for s in sources]
                    expected_source = f'sources/github/{repo_full_name}'
                    
                    if expected_source in source_names:
                        logger.info(f"✓ Repository indexed and available as source")
                        repository_indexed = True
                        break
                    else:
                        if attempt < max_retries - 1:
                            wait_time = 15  # Increased from 10 to 15 seconds between retries
                            logger.warning(f"Repository not yet indexed, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Repository not indexed after {max_retries} attempts")
                            raise Exception(
                                f"Repository {repo_full_name} is not available in Jules sources after waiting. "
                                f"This usually means:\n"
                                f"1. The Jules GitHub App doesn't have access to this repository\n"
                                f"2. The repository is still being indexed (try again in a few minutes)\n"
                                f"3. There's an issue with the Jules service\n\n"
                                f"Please ensure the Jules GitHub App is installed with access to 'All repositories' "
                                f"or specifically includes this repository."
                            )
                except Exception as e:
                    if "not available in Jules sources" in str(e):
                        raise  # Re-raise our custom exception
                    logger.warning(f"Could not verify repository indexing: {e}")
                    # Don't break - keep trying
                    if attempt < max_retries - 1:
                        time.sleep(15)
            
            # Only proceed if repository is indexed
            if not repository_indexed:
                raise Exception(f"Repository {repo_full_name} was never successfully indexed by Jules")

            # 3. Start Jules session
            session_id = self.start_jules_session(
                repo_full_name,
                idea,
                default_branch=default_branch,
                require_plan_approval=require_plan_approval
            )

            # 4. Monitor session (optional - can run asynchronously)
            # In production, you might want to monitor or just return the session ID
            # session_result = self.monitor_session(session_id)

            return {
                'idea': idea.title,
                'repo': repo_full_name,
                'status': 'session_started',
                'session_id': session_id,
                'jules_ready': True,
                'instructions': f'Jules session started. Monitor at: https://jules.google (session: {session_id})'
            }

        except Exception as e:
            logger.error(f"Error processing idea {idea.title}: {e}")
            return {
                'idea': idea.title,
                'status': 'error',
                'error': str(e)
            }

    def run_batch(self, ideas: List[ExperimentIdea], require_plan_approval: bool = True) -> List[Dict[str, Any]]:
        """
        Process multiple ideas with concurrency control.

        Args:
            ideas: List of experiment ideas
            require_plan_approval: Whether to require plan approval for each session

        Returns:
            List of processing results
        """
        results = []

        for idea in ideas:
            result = self.process_idea(idea, require_plan_approval=require_plan_approval)
            results.append(result)

            # Respect Jules quotas (avoid hitting concurrent session limits)
            # Free: 3 concurrent, Pro: 15 concurrent, Ultra: 60 concurrent
            if len([r for r in results if r.get('status') == 'session_started']) >= self.config.max_concurrent:
                logger.info(f"Reached concurrent limit ({self.config.max_concurrent}), pausing...")
                time.sleep(5)

        return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Jules Experiment Orchestrator")
    parser.add_argument(
        '--input',
        default='../ideas.csv',
        help='Path to CSV/Excel file with experiment ideas'
    )
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=3,
        help='Maximum number of concurrent Jules sessions (Free: 3, Pro: 15, Ultra: 60)'
    )
    parser.add_argument(
        '--auto-approve',
        action='store_true',
        help='Automatically approve plans (skip plan approval step)'
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
    jules_api_key = os.environ.get('JULES_API_KEY')

    if not all([github_token, github_owner, jules_api_key]):
        logger.error("Missing required environment variables:")
        logger.error("  GITHUB_TOKEN: GitHub personal access token")
        logger.error("  GITHUB_OWNER: GitHub username or organization")
        logger.error("  JULES_API_KEY: Jules API key from jules.google Settings")
        logger.error("\nNote: Install Jules GitHub App with 'All repositories' access")
        logger.error("so new repos are automatically available as sources.")
        sys.exit(1)

    # Setup configuration
    config = RepoConfig(
        owner=github_owner,
        token=github_token,
        max_concurrent=args.max_concurrent
    )

    # Initialize orchestrator
    orchestrator = JulesOrchestrator(config, jules_api_key)

    if args.dry_run:
        logger.info("DRY RUN MODE - No actual changes will be made")
        return

    try:
        # Load ideas
        ideas = orchestrator.load_ideas(args.input)

        # Process ideas
        logger.info(f"Starting batch processing of {len(ideas)} ideas for Jules")
        logger.info(f"Max concurrent sessions: {args.max_concurrent}")
        logger.info(f"Plan approval: {'auto' if args.auto_approve else 'required'}")

        results = orchestrator.run_batch(
            ideas,
            require_plan_approval=not args.auto_approve
        )

        # Summarize results
        successful = [r for r in results if r.get('status') == 'session_started']
        failed = [r for r in results if r.get('status') != 'session_started']

        logger.info(f"\nBatch processing completed:")
        logger.info(f"  Jules sessions started: {len(successful)}")
        logger.info(f"  Failed: {len(failed)}")

        if successful:
            logger.info("\nStarted sessions:")
            for result in successful:
                logger.info(f"  - {result['repo']}: {result.get('session_id', 'N/A')}")

        if failed:
            logger.warning("\nFailed repositories:")
            for result in failed:
                logger.warning(f"  - {result['idea']}: {result.get('error', 'Unknown error')}")

        logger.info("\nNext steps:")
        logger.info("1. Monitor Jules sessions at https://jules.google")
        logger.info("2. Approve plans if plan approval is enabled")
        logger.info("3. Jules will iterate on CI failures automatically via state.json")
        logger.info("4. Check generated PRs and final READMEs when sessions complete")

        logger.info("\nQuota information:")
        logger.info(f"  Current concurrent sessions: {len(successful)}")
        logger.info("  Free tier: 15 tasks/day, 3 concurrent")
        logger.info("  Pro tier: 100 tasks/day, 15 concurrent")
        logger.info("  Ultra tier: 300 tasks/day, 60 concurrent")

    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

