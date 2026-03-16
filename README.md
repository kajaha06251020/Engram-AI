<div align="center">

<img src="https://raw.githubusercontent.com/kajaha06251020/Engram-AI/main/docs/assets/logo.svg" alt="Engram-AI Logo" width="200"/>

# Engram-AI

### Experience-Driven Memory Infrastructure for AI Agents

[![PyPI version](https://img.shields.io/pypi/v/engram-ai?style=flat-square&color=blue)](https://pypi.org/project/engram-ai/)
[![Python](https://img.shields.io/pypi/pyversions/engram-ai?style=flat-square)](https://pypi.org/project/engram-ai/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/kajaha06251020/Engram-AI/tests.yml?style=flat-square&label=tests)](https://github.com/kajaha06251020/Engram-AI/actions)
[![codecov](https://img.shields.io/codecov/c/github/kajaha06251020/Engram-AI?style=flat-square)](https://codecov.io/gh/kajaha06251020/Engram-AI)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square)](https://github.com/astral-sh/ruff)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)
[![GitHub Stars](https://img.shields.io/github/stars/kajaha06251020/Engram-AI?style=flat-square)](https://github.com/kajaha06251020/Engram-AI/stargazers)
[![Discord](https://img.shields.io/badge/Discord-join%20chat-7289DA?style=flat-square&logo=discord&logoColor=white)](https://discord.gg/engram-ai)

**[English](#what-is-engram-ai)** | **[日本語](docs/i18n/README_ja.md)** | **[中文](docs/i18n/README_zh.md)** | **[한국어](docs/i18n/README_ko.md)** | **[Español](docs/i18n/README_es.md)**

---

*Current AI memory stores text. Engram-AI creates **scars** — causal structures that let agents learn from what they did and what happened.*

</div>

## What is Engram-AI?

Most AI memory systems work like a **diary** — they store text facts: *"The user prefers Python"*, *"The API uses REST"*. But real learning doesn't come from memorizing facts. It comes from **experience**.

Engram-AI gives AI agents **experiential memory**. Instead of storing what the agent *knows*, it stores what the agent *did*, what *happened*, and whether the outcome was *good or bad*:

```
Action:   Used Optional[str] for API response field
Context:  Designing REST API response model
Outcome:  User rejected it — "no null values in responses"
Valence:  -0.8 (negative experience)
```

Over time, these experiences **crystallize** into skills — generalized rules the agent learns from patterns in its own history:

```
Skill:    "Avoid Optional types in API response models"
Confidence: 0.85
Evidence: 5 experiences (3 negative, 2 positive)
```

Then skills **evolve** into the agent's configuration, making the agent permanently better:

```markdown
<!-- engram-ai:start -->
## Engram-AI: Learned Skills
- Avoid Optional types in API response models (confidence: 0.85)
- Use descriptive variable names in test files (confidence: 0.92)
<!-- engram-ai:end -->
```

## Why Engram-AI?

| Feature | Traditional Memory (Mem0, etc.) | Engram-AI |
|---------|-------------------------------|-----------|
| **What it stores** | Text facts ("user likes X") | Causal structures (action → context → outcome) |
| **How it learns** | Retrieval of stored text | Pattern crystallization from experiences |
| **Learning signal** | None | Valence (-1.0 to +1.0) per experience |
| **Agent improvement** | Manual prompt tuning | Automatic skill evolution into config |
| **Memory model** | Diary entries | Neural engrams (scars from experience) |

## Quick Start

### Installation

```bash
pip install engram-ai
```

### As a Python Library

```python
from engram_ai import Forge

forge = Forge()

# Record an experience
forge.record(
    action="Used list comprehension for data transform",
    context="Processing CSV with 10k rows",
    outcome="Fast and readable, user approved",
    valence=0.9,
)

# Query past experiences
result = forge.query("data transformation approach")
print(result["best"])   # Positive experiences
print(result["avoid"])  # Negative experiences

# Crystallize patterns into skills
skills = forge.crystallize()

# Evolve agent config with learned skills
forge.evolve(config_path="./CLAUDE.md")
```

### With Claude Code (Recommended)

One command to set up automatic experience recording:

```bash
# Install and configure
pip install engram-ai
engram-ai setup

# That's it! Engram-AI now:
# 1. Records experiences via hooks (PostToolUse, UserPromptSubmit)
# 2. Exposes tools via MCP server (query, crystallize, evolve)
# 3. Detects outcome valence from your reactions (keyword + LLM)
```

After setup, your Claude Code agent automatically:
- **Records** every tool use as a pending experience
- **Detects** whether your response was positive/negative
- **Learns** patterns from accumulated experiences
- **Evolves** its own CLAUDE.md with learned skills

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Forge (Facade)                     │
├──────────┬──────────┬──────────────┬────────────────┤
│ Recorder │ Querier  │ Crystallizer │    Evolver     │
├──────────┴──────────┴──────────────┴────────────────┤
│                    EventBus                          │
├─────────────────┬───────────────────────────────────┤
│  Storage Layer  │          LLM Layer                │
│  (ChromaDB)     │     (Claude API)                  │
├─────────────────┴───────────────────────────────────┤
│              Adapters (Claude Code)                  │
└─────────────────────────────────────────────────────┘
```

**Core Operations:**

| Operation | What it does |
|-----------|-------------|
| **Record** | Store an experience (action + context + outcome + valence) |
| **Query** | Find relevant past experiences, partitioned into "best" and "avoid" |
| **Crystallize** | Cluster similar experiences and extract skill patterns via LLM |
| **Evolve** | Write learned skills to agent config (CLAUDE.md) |

## CLI Reference

```bash
engram-ai setup          # Auto-configure for Claude Code
engram-ai status         # Show experience/skill counts
engram-ai query "topic"  # Search past experiences
engram-ai crystallize    # Extract skills from experiences
engram-ai evolve         # Write skills to CLAUDE.md
engram-ai serve          # Start MCP server
```

## MCP Tools

When running as an MCP server, Engram-AI exposes these tools:

| Tool | Description |
|------|-------------|
| `engram_record` | Record an experience with valence |
| `engram_query` | Search past experiences |
| `engram_crystallize` | Extract skills from patterns |
| `engram_evolve` | Write skills to config |
| `engram_status` | Show statistics |

## How It Works

### Two-Phase Recording

```
PostToolUse Hook          UserPromptSubmit Hook
     │                           │
     ▼                           ▼
Record Pending ──────────► Complete with Valence
(action + context)         (outcome + valence detection)
     │                           │
     ▼                           ▼
pending.jsonl              ChromaDB Storage
```

### Valence Detection (Tiered)

1. **Keyword matching** (free) — Detects positive/negative patterns in JP + EN
2. **LLM fallback** (API call) — When keywords don't match
3. **Default 0.3** — Mildly positive assumption when both fail

### Crystallization Pipeline

```
Experiences ──► Cluster by similarity ──► LLM extracts pattern ──► Skill
                (ChromaDB cosine)         (per cluster)            (rule + confidence)
```

## Roadmap

Engram-AI v0.1 is the foundation. The architecture supports these planned features:

- [ ] **Emotion tagging** — Richer affect beyond valence
- [ ] **Experience chains** — Linked sequences of related experiences
- [ ] **Forgetting curves** — Time-weighted relevance decay
- [ ] **Skill marketplace** — Share learned skills across agents
- [ ] **Cross-agent transfer** — Transfer learning between agent instances
- [ ] **Multi-LLM support** — OpenAI, local models, etc.
- [ ] **Dashboard** — Web UI for experience/skill visualization
- [ ] **Reward shaping policies** — Custom valence strategies
- [ ] **Hierarchical memory** — Episode → skill → meta-skill layers
- [ ] **Privacy controls** — Selective memory, user-controlled deletion

See [full roadmap](docs/specs/2026-03-17-engram-ai-v0.1-design.md) for all 20 planned features.

## Contributing

We welcome contributions from everyone! See our [Contributing Guide](CONTRIBUTING.md) for details.

**Quick start for contributors:**

```bash
git clone https://github.com/kajaha06251020/Engram-AI.git
cd Engram-AI
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
pytest
```

Check out our [good first issues](https://github.com/kajaha06251020/Engram-AI/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to get started!

## Community

- [GitHub Discussions](https://github.com/kajaha06251020/Engram-AI/discussions) — Questions, ideas, show & tell
- [Discord](https://discord.gg/engram-ai) — Real-time chat
- [Issues](https://github.com/kajaha06251020/Engram-AI/issues) — Bug reports and feature requests

## Star History

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=kajaha06251020/Engram-AI&type=Date)](https://star-history.com/#kajaha06251020/Engram-AI&Date)

</div>

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

<div align="center">

**If Engram-AI helps your AI agents learn from experience, please give it a star!**

<a href="https://github.com/kajaha06251020/Engram-AI/stargazers">
  <img src="https://img.shields.io/github/stars/kajaha06251020/Engram-AI?style=social" alt="GitHub Stars"/>
</a>

</div>
