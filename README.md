# AI Agent Experiment Orchestration System

A comprehensive framework for orchestrating AI coding agents (Jules, OpenHands, Augment, Cosine) across multiple computational experiments using cloud-only infrastructure.

## 📁 Repository Structure

```
├── data/                    # Data files (ideas.csv, etc.)
├── docs/                    # Documentation
│   ├── README.md           # Detailed documentation
│   ├── QUICKSTART.md       # Quick start guide
│   ├── TEST.md            # Testing guide
│   └── ...
├── providers/              # Provider-specific orchestrators
│   ├── jules/             # Jules orchestrator
│   ├── openhands/         # OpenHands orchestrator
│   ├── augment/           # Augment orchestrator
│   └── cosine/            # Cosine orchestrator
├── tests/                 # Test suite
│   ├── integration/       # Integration tests
│   ├── providers/         # Provider-specific tests
│   └── fixtures/          # Test data
├── scripts/               # Utility scripts
├── env.example           # Environment variables template
└── .gitignore
```

## 🚀 Quick Start

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for detailed setup instructions.

## 📖 Documentation

- **[Full Documentation](docs/README.md)** - Complete system overview
- **[Testing Guide](docs/TEST.md)** - How to test the system
- **[CSV Format](docs/CSV_FORMAT.md)** - Input data format
- **[Provider Comparison](docs/PROVIDER_COMPARISON.md)** - Choose the right agent

## 🎯 Features

- **Multi-Provider Support**: Jules, OpenHands, Augment, Cosine
- **Dual Pipeline**: AI-planned experiments + pre-defined experiments
- **Cloud-Only**: No local compute required
- **GitHub Integration**: Automatic repository creation and management
- **Comprehensive Testing**: Full test suite included
- **Production Ready**: Error handling, logging, retry logic

## 📋 Requirements

- Python 3.8+
- GitHub Personal Access Token (repo scope)
- Provider API keys (see docs/TEST.md)

## 🏃‍♂️ Usage

```bash
# Set environment variables
export GITHUB_TOKEN=ghp_your_token
export GITHUB_OWNER=your_username
export JULES_API_KEY=your_key

# Run with Jules (recommended)
cd providers/jules
python orchestrator.py --input ../../data/ideas.csv --max-concurrent 1
```

## 🤝 Contributing

1. Read the [testing guide](docs/TEST.md)
2. Run the full test suite
3. Submit pull requests

## 📄 License

See individual provider documentation for licensing terms.