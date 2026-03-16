# Contributing to Engram-AI

First off, thank you for considering contributing to Engram-AI! Every contribution helps make AI agents learn better from their experiences.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)
- [Architecture Overview](#architecture-overview)

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior via GitHub Issues.

## How Can I Contribute?

### Reporting Bugs

- Use the [Bug Report](https://github.com/kajaha06251020/Engram-AI/issues/new?template=bug_report.md) template
- Include Python version, OS, and steps to reproduce
- Include the full error traceback if applicable

### Suggesting Features

- Use the [Feature Request](https://github.com/kajaha06251020/Engram-AI/issues/new?template=feature_request.md) template
- Check the [roadmap](README.md#roadmap) first — your idea might already be planned!
- Explain the use case and why existing features don't cover it

### Your First Code Contribution

Look for issues labeled [`good first issue`](https://github.com/kajaha06251020/Engram-AI/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) — these are specifically designed for newcomers.

**Examples of good first contributions:**
- Adding new keyword patterns for valence detection (JP, EN, or other languages!)
- Writing tests for untested CLI commands
- Improving documentation or translations
- Adding type hints to existing code

### Adding Language Support

Engram-AI's valence detection supports Japanese and English keywords. Adding your language is a great first contribution! See `src/engram_ai/core/recorder.py` for the keyword patterns.

## Development Setup

### Prerequisites

- Python 3.10+
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/kajaha06251020/Engram-AI.git
cd Engram-AI

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in development mode
pip install -e ".[dev]"

# Verify setup
pytest
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/core/test_recorder.py

# Run specific test
pytest tests/core/test_recorder.py::test_record_complete_experience -v
```

### Linting

```bash
# Check code style
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

## Development Workflow

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Write tests first** (TDD is encouraged)
4. **Implement** your changes
5. **Run tests** and **lint**:
   ```bash
   pytest && ruff check src/ tests/
   ```
6. **Commit** with a clear message:
   ```bash
   git commit -m "feat: add Korean valence keywords"
   ```
7. **Push** and **create a Pull Request**

### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for |
|--------|---------|
| `feat:` | New features |
| `fix:` | Bug fixes |
| `test:` | Adding or updating tests |
| `docs:` | Documentation changes |
| `refactor:` | Code changes that neither fix bugs nor add features |
| `chore:` | Maintenance tasks |

## Pull Request Process

1. Update documentation if your change affects the public API
2. Add tests for new functionality
3. Ensure all tests pass and ruff reports no issues
4. Fill in the PR template with a clear description
5. Link any related issues

### PR Review

- A maintainer will review your PR within a few days
- Be open to feedback — we aim for constructive, respectful reviews
- Small, focused PRs are reviewed faster than large ones

## Style Guide

### Python

- **Formatter/Linter**: Ruff (config in `pyproject.toml`)
- **Type hints**: Use them for public APIs
- **Models**: Pydantic BaseModel for all data models
- **Abstract classes**: ABC for extensible interfaces
- **Testing**: pytest, TDD encouraged

### Code Organization

```
src/engram_ai/
├── models/       # Pydantic data models
├── events/       # EventBus and event constants
├── storage/      # Storage abstraction + ChromaDB
├── llm/          # LLM abstraction + Claude
├── adapters/     # Agent config adapters (Claude Code)
├── core/         # Business logic (Recorder, Querier, etc.)
├── forge.py      # Main facade
├── cli.py        # Click CLI
└── mcp.py        # MCP server
```

### Key Principles

- **YAGNI** — Don't build what isn't needed yet
- **DRY** — But don't over-abstract
- **Single Responsibility** — Each file/class does one thing
- **Extensibility via ABCs** — `BaseStorage`, `BaseLLM`, `BaseAdapter`

## Architecture Overview

```
Forge (facade) → Recorder, Querier, Crystallizer, Evolver
                       ↓           ↓            ↓
                   EventBus    Storage (ChromaDB)  LLM (Claude)
                                                   Adapter (Claude Code)
```

**Want to add a new storage backend?** Implement `BaseStorage`.
**Want to add OpenAI support?** Implement `BaseLLM`.
**Want to support a new agent platform?** Implement `BaseAdapter`.

## Questions?

- Open a [Discussion](https://github.com/kajaha06251020/Engram-AI/discussions) for questions
- Check existing issues before creating new ones
- Join our [Discord](https://discord.gg/engram-ai) for real-time help

---

Thank you for contributing to Engram-AI!
