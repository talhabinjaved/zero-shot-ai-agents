#!/bin/bash
# Quick Start Script for Running AI Agent Experiments
# This script helps you set up and run the orchestrator

set -e  # Exit on any error

echo "=========================================="
echo "AI Agent Experiment Orchestrator"
echo "=========================================="
echo ""

# Check which provider to use
echo "Which AI provider do you want to use?"
echo "1) Jules (Recommended - Full API, easiest automation)"
echo "2) Augment (CLI-based automation)"
echo "3) OpenHands (Conversation API, BYO models)"
echo "4) Cosine (Manual import, CI monitoring)"
echo ""
read -p "Enter choice (1-4): " provider_choice

case $provider_choice in
  1)
    PROVIDER="jules"
    echo "Selected: Jules"
    ;;
  2)
    PROVIDER="augment"
    echo "Selected: Augment"
    ;;
  3)
    PROVIDER="openhands"
    echo "Selected: OpenHands"
    ;;
  4)
    PROVIDER="cosine"
    echo "Selected: Cosine"
    ;;
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac

echo ""
echo "=========================================="
echo "Checking Prerequisites"
echo "=========================================="
echo ""

# Check if environment variables are set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN not set"
    echo "Get from: https://github.com/settings/tokens"
    echo "Then run: export GITHUB_TOKEN='ghp_your_token'"
    exit 1
else
    echo "✅ GITHUB_TOKEN is set"
fi

if [ -z "$GITHUB_OWNER" ]; then
    echo "❌ GITHUB_OWNER not set"
    echo "Run: export GITHUB_OWNER='your-github-username'"
    exit 1
else
    echo "✅ GITHUB_OWNER is set ($GITHUB_OWNER)"
fi

# Provider-specific checks
if [ "$PROVIDER" = "jules" ]; then
    if [ -z "$JULES_API_KEY" ]; then
        echo "❌ JULES_API_KEY not set"
        echo "Get from: https://jules.google → Settings → API Keys"
        echo "Then run: export JULES_API_KEY='your_key'"
        exit 1
    else
        echo "✅ JULES_API_KEY is set"
    fi
fi

if [ "$PROVIDER" = "augment" ]; then
    if [ -z "$AUGMENT_SESSION_AUTH" ]; then
        echo "❌ AUGMENT_SESSION_AUTH not set"
        echo "Get by running: auggie --print-augment-token"
        echo "Then run: export AUGMENT_SESSION_AUTH='your_token'"
        exit 1
    else
        echo "✅ AUGMENT_SESSION_AUTH is set"
    fi
fi

if [ "$PROVIDER" = "openhands" ]; then
    if [ -z "$OPENHANDS_API_KEY" ]; then
        echo "❌ OPENHANDS_API_KEY not set"
        echo "Get from: https://app.all-hands.dev → Settings"
        echo "Then run: export OPENHANDS_API_KEY='your_key'"
        exit 1
    else
        echo "✅ OPENHANDS_API_KEY is set"
    fi
fi

echo ""
echo "=========================================="
echo "Installing Dependencies"
echo "=========================================="
echo ""

cd "providers/$PROVIDER"
echo "Installing Python dependencies for $PROVIDER..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies in venv..."
pip install -q -r requirements.txt

echo "✅ Dependencies installed in virtual environment"

echo ""
echo "=========================================="
echo "Input File Selection"
echo "=========================================="
echo ""

# Ask for input file
echo "Available data files:"
ls -1 ../../data/

echo ""
read -p "Enter input file name (default: ideas.csv): " input_file
input_file=${input_file:-ideas.csv}

INPUT_PATH="../../data/$input_file"

if [ ! -f "$INPUT_PATH" ]; then
    echo "❌ File not found: $INPUT_PATH"
    exit 1
fi

echo "✅ Using input file: $INPUT_PATH"

echo ""
echo "=========================================="
echo "Dry Run (Preview)"
echo "=========================================="
echo ""

read -p "Do you want to run a dry-run first? (Y/n): " do_dryrun
do_dryrun=${do_dryrun:-Y}

if [[ "$do_dryrun" =~ ^[Yy]$ ]]; then
    echo "Running dry-run..."
    python orchestrator.py --input "$INPUT_PATH" --dry-run
fi

echo ""
echo "=========================================="
echo "Ready to Execute!"
echo "=========================================="
echo ""
echo "This will:"
echo "  1. Read experiment ideas from $input_file"
echo "  2. Create GitHub repositories under $GITHUB_OWNER/"
echo "  3. Seed repos with experiment templates"
echo "  4. Start $PROVIDER AI agent sessions"
echo "  5. AI will plan/execute/validate experiments"
echo "  6. AI will open PRs with results"
echo ""

read -p "Continue with actual execution? (y/N): " confirm
confirm=${confirm:-N}

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Cancelled. No changes made."
    exit 0
fi

echo ""
echo "=========================================="
echo "Executing Orchestrator"
echo "=========================================="
echo ""

# Build command based on provider
if [ "$PROVIDER" = "jules" ]; then
    python orchestrator.py --input "$INPUT_PATH" --max-concurrent 1 --auto-approve
elif [ "$PROVIDER" = "augment" ]; then
    python orchestrator.py --input "$INPUT_PATH" --max-concurrent 1
elif [ "$PROVIDER" = "openhands" ]; then
    python orchestrator.py --input "$INPUT_PATH" --max-concurrent 1
elif [ "$PROVIDER" = "cosine" ]; then
    python orchestrator.py --input "$INPUT_PATH" --max-concurrent 1
fi

echo ""
echo "=========================================="
echo "✅ Complete!"
echo "=========================================="
echo ""
echo "Next steps:"

if [ "$PROVIDER" = "jules" ]; then
    echo "  1. Visit https://jules.google to monitor sessions"
    echo "  2. Check your GitHub repos for opened PRs"
    echo "  3. Review and merge PRs when ready"
elif [ "$PROVIDER" = "augment" ]; then
    echo "  1. Visit https://augmentcode.com to monitor agents"
    echo "  2. Check your GitHub repos for opened PRs"
    echo "  3. Review and merge PRs when ready"
elif [ "$PROVIDER" = "openhands" ]; then
    echo "  1. Visit https://app.all-hands.dev to monitor conversations"
    echo "  2. Check your GitHub repos for opened PRs"
    echo "  3. Review and merge PRs when ready"
elif [ "$PROVIDER" = "cosine" ]; then
    echo "  1. Import repos into your Cosine workspace"
    echo "  2. Configure CI monitoring in Project Settings"
    echo "  3. Check COSINE_SETUP.md in each repo for details"
fi

echo ""
echo "Log files created in: providers/$PROVIDER/*.log"

