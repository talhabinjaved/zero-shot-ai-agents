Of course. Here is a guide on how to structure a single repository to test and compare the four providers: Augment, Jules, Cosine, and OpenHands.

### **Repository Structure**

This structure isolates the logic for each provider while sharing a common set of ideas.

```
/
├── ideas.csv
├── .gitignore
├── README.md
│
├── augment/
│   ├── orchestrator.py
│   ├── AGENTS.md
│   ├── templates/
│   │   ├── experiments.yaml
│   │   ├── harness.py
│   │   └── workflow.yml
│   └── requirements.txt
│
├── jules/
│   ├── orchestrator.py
│   ├── AGENTS.md
│   ├── templates/
│   │   ├── experiments.yaml
│   │   ├── runner.py
│   │   └── workflow.yml
│   └── requirements.txt
│
├── cosine/
│   ├── orchestrator.py
│   ├── templates/
│   │   ├── experiments.yaml
│   │   ├── executor.py
│   │   └── workflow.yml
│   └── requirements.txt
│
└── openhands/
    ├── orchestrator.py
    ├── AGENTS.md
    ├── templates/
    │   ├── microagent_repo.md
    │   ├── experiments.yaml
    │   ├── runner.py
    │   └── workflow.yml
    └── requirements.txt
```

### **File-by-File Setup**

#### 1. **Root Directory**

*   **`ideas.csv`**: This is the master file of ideas that each provider's script will read from.
    ```csv
    title,description,experiments_yaml
    "Analyze Stock Market Trends","Use historical data to predict future stock movements.",""
    "Build a Recommendation Engine","Create a simple movie recommendation system.",""
    ```

*   **`.gitignore`**: A standard Python gitignore to keep the repository clean.
    ```
    __pycache__/
    *.pyc
    .venv
    .env
    ```

*   **`README.md`**: This is the main entry point for your project. It will explain how to set up and run the tests for each provider.

#### 2. **Provider Directories (`augment/`, `jules/`, `cosine/`, `openhands/`)**

Each of these directories will contain the necessary files to run the orchestration for that specific provider.

*   **`orchestrator.py`**: This is the main Python script for each provider, adapted from the provided documentation. It will read `ideas.csv`, create repositories, and interact with the respective provider's API or CLI.

*   **`AGENTS.md`**: Where applicable (Augment, Jules, OpenHands), this file will contain the instructions for the agent.

*   **`templates/`**: This subdirectory will hold the boilerplate files that the `orchestrator.py` script will push to the newly created GitHub repositories.
    *   `experiments.yaml`: A template for the experiment plan.
    *   `harness.py` / `runner.py` / `executor.py`: The script that runs the experiments within the GitHub Actions workflow.
    *   `workflow.yml`: The GitHub Actions workflow file.
    *   `microagent_repo.md` (for OpenHands): Specific instructions for the OpenHands microagent.

*   **`requirements.txt`**: The Python dependencies for each orchestrator script.
    ```
    pandas
    requests
    pyyaml
    python-slugify
    jinja2
    ```

### **How to Use the Repository**

1.  **Clone the repository.**
2.  **Set up the environment variables** for each provider as specified in their respective documentation (e.g., `GITHUB_TOKEN`, `AUGMENT_SESSION_AUTH`, `JULES_API_KEY`, `OPENHANDS_API_KEY`).
3.  **Install the necessary CLI tools** for each provider (e.g., `auggie`, `jules`, `cos`).
4.  **Navigate to the directory of the provider you want to test** (e.g., `cd augment`).
5.  **Install the Python dependencies**: `pip install -r requirements.txt`.
6.  **Run the orchestrator script**: `python orchestrator.py`.

By following this structure, you can systematically test and compare the capabilities of each provider from a single, organized repository.