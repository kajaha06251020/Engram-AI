<div align="center">

<img src="https://raw.githubusercontent.com/kajaha06251020/Engram-AI/main/docs/assets/logo.svg" alt="Engram-AI Logo" width="200"/>

# Engram-AI

### Experience-Driven Memory Infrastructure for AI Agents

[![PyPI version](https://img.shields.io/pypi/v/engram-forge?style=flat-square&color=blue)](https://pypi.org/project/engram-forge/)
[![Python](https://img.shields.io/pypi/pyversions/engram-forge?style=flat-square)](https://pypi.org/project/engram-forge/)
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

---

## Table of Contents

- [What is Engram-AI?](#what-is-engram-ai)
- [Why Engram-AI?](#why-engram-ai)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Sample Programs](#sample-programs)
- [API Reference](#api-reference)
- [CLI Reference](#cli-reference)
- [MCP Server](#mcp-server)
- [Without an Anthropic API Key](#without-an-anthropic-api-key)
- [Multi-Project Support](#multi-project-support)
- [Architecture](#architecture)
- [Web Dashboard](#web-dashboard)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

---

## What is Engram-AI?

Most AI memory systems work like a **diary** — they store text facts: *"The user prefers Python"*, *"The API uses REST"*. But real learning doesn't come from memorizing facts. It comes from **experience**.

Engram-AI gives AI agents **experiential memory**. Instead of storing what the agent *knows*, it stores what the agent *did*, what *happened*, and whether the outcome was *good or bad*:

```
Action:   Used Optional[str] for API response field
Context:  Designing REST API response model
Outcome:  User rejected it — "no null values in responses"
Valence:  -0.8  ← negative experience
```

Over time, experiences **crystallize** into skills — generalized rules extracted from patterns:

```
Skill:      "Avoid Optional types in API response models"
Confidence: 0.85
Evidence:   5 experiences (4 negative, 1 positive)
```

Skills then **evolve** into the agent's configuration, making it permanently better:

```markdown
<!-- engram-forge:start -->
## Engram-AI: Learned Skills
- Avoid Optional types in API response models (confidence: 0.85)
- Use descriptive variable names in test files (confidence: 0.92)
<!-- engram-forge:end -->
```

---

## Why Engram-AI?

| Feature | Traditional Memory (Mem0, etc.) | Engram-AI |
|---------|-------------------------------|-----------|
| **What it stores** | Text facts ("user likes X") | Causal structures (action → context → outcome) |
| **How it learns** | Retrieval of stored text | Pattern crystallization from experiences |
| **Learning signal** | None | Valence (−1.0 to +1.0) per experience |
| **Agent improvement** | Manual prompt tuning | Automatic skill evolution into config |
| **Memory model** | Diary entries | Neural engrams (scars from experience) |
| **API key required** | Usually | No — core features work without one |

---

## Installation

Choose the extras that match your use case:

| Command | What it adds | When to use |
|---------|-------------|------------|
| `pip install engram-forge` | Core (ChromaDB + CLI) | Embedding in your app without LLM |
| `pip install "engram-forge[claude]"` | + Anthropic SDK | LLM-powered crystallization & valence |
| `pip install "engram-forge[mcp]"` | + MCP server | Claude Code / MCP client integration |
| `pip install "engram-forge[dashboard]"` | + FastAPI + Uvicorn | Web UI for visualization |
| `pip install "engram-forge[full]"` | Everything above | Recommended for most users |
| `pip install "engram-forge[full,dev]"` | + pytest, ruff | Development |

---

## Quick Start

### Option A — With Claude Code (zero-config)

```bash
pip install "engram-forge[full]"
engram-forge setup        # writes MCP config + hooks to ~/.claude/settings.json
```

Restart Claude Code. That's it. Engram-AI now:

1. **Records** every tool use as a pending experience (PostToolUse hook)
2. **Detects** whether your response was positive/negative (UserPromptSubmit hook)
3. **Crystallizes** patterns into skills after every session
4. **Evolves** CLAUDE.md automatically with learned rules

### Option B — As a Python Library

```python
from engram_ai import Forge

# Defaults: ChromaDB at ~/.engram-ai/data, LLM from ANTHROPIC_API_KEY env
forge = Forge()

# Record an experience
exp = forge.record(
    action="Used list comprehension for data transform",
    context="Processing CSV with 10k rows in pandas pipeline",
    outcome="Fast and readable — user approved it immediately",
    valence=0.9,
)
print(exp.id)  # uuid

# Query past experiences for a new task
result = forge.query("data transformation approach")
for exp, score in result["best"]:
    print(f"  [{score:.2f}] Do: {exp.action}")
for exp, score in result["avoid"]:
    print(f"  [{score:.2f}] Avoid: {exp.action}")

# Crystallize patterns into reusable skills
skills = forge.crystallize(min_experiences=3, min_confidence=0.7)
for skill in skills:
    print(f"  Learned: {skill.rule}  (confidence={skill.confidence:.2f})")

# Write skills into an agent config file
record = forge.evolve(config_path="./CLAUDE.md")
if record:
    print(f"Updated config: {record.diff}")
```

---

## Sample Programs

The [`examples/`](examples/) directory contains ready-to-run scripts.

### 1 · Basic record / query / crystallize / evolve

```python
# examples/01_basic.py
from engram_ai import Forge

forge = Forge(storage_path="/tmp/engram-demo")

# --- Record a few experiences ---
pairs = [
    ("Used f-strings for formatting",     "Writing Python utility script",      "Readable and fast",          0.8),
    ("Used % formatting for strings",     "Writing Python utility script",      "Hard to read, user rewrote", -0.7),
    ("Used f-strings in log messages",    "Adding debug logging to API server", "Clear output, approved",     0.9),
    ("Used str.format() in log messages", "Adding debug logging to API server", "Verbose, asked to simplify", -0.5),
]
for action, context, outcome, valence in pairs:
    forge.record(action=action, context=context, outcome=outcome, valence=valence)

# --- Query ---
print("=== Query: string formatting ===")
result = forge.query("string formatting in Python", k=3)
for exp, score in result["best"]:
    print(f"  DO    [{score:.2f}]  {exp.action}")
for exp, score in result["avoid"]:
    print(f"  AVOID [{score:.2f}]  {exp.action}")

# --- Crystallize ---
print("\n=== Skills ===")
skills = forge.crystallize(min_experiences=2, min_confidence=0.5)
for skill in skills:
    print(f"  {skill.rule}  (confidence={skill.confidence:.2f})")

# --- Evolve ---
forge.evolve(config_path="/tmp/AGENT.md")
print("\nWrote skills to /tmp/AGENT.md")
```

### 2 · Teach a rule directly (no experiences needed)

```python
# examples/02_teach.py
from engram_ai import Forge

forge = Forge(storage_path="/tmp/engram-teach")

# Directly inject a known rule — useful for bootstrapping
skill = forge.teach(
    rule="Always validate user input at the API boundary",
    context_pattern="handling HTTP requests",
    skill_type="positive",
    confidence=0.95,
)
print(f"Taught: {skill.rule}")

# Teach an anti-pattern
anti = forge.teach(
    rule="Never use eval() on user-supplied strings",
    context_pattern="executing dynamic code",
    skill_type="anti",
    confidence=1.0,
)
print(f"Anti-pattern: {anti.rule}")
```

### 3 · Warn before a risky action

```python
# examples/03_warn.py
from engram_ai import Forge

forge = Forge(storage_path="/tmp/engram-warn")

# Seed some past failures
forge.record(
    action="Ran DELETE without WHERE clause",
    context="Database cleanup script",
    outcome="Wiped entire table — had to restore from backup",
    valence=-1.0,
)
forge.record(
    action="Executed raw SQL from user input",
    context="Search feature implementation",
    outcome="SQL injection vulnerability found in review",
    valence=-0.9,
)

# Before executing a new action, check for past failures
warnings = forge.warn(
    action="Run DELETE query on production database",
    context="Database maintenance",
    threshold=0.5,
)
if warnings:
    print("WARNING — past issues with similar actions:")
    for w in warnings:
        print(f"  [{w.valence:.1f}] {w.outcome}")
else:
    print("No past issues found.")
```

### 4 · Multi-project management

```python
# examples/04_multi_project.py
from pathlib import Path
from engram_ai import Forge, ProjectManager

pm = ProjectManager(base_path=Path("/tmp/engram-projects"))

# Each project has its own isolated memory
frontend = pm.get_forge("frontend")
backend  = pm.get_forge("backend")

frontend.record(
    action="Used Tailwind utility classes for layout",
    context="Building responsive card component",
    outcome="Fast iteration, designer approved",
    valence=0.85,
)

backend.record(
    action="Used SQLAlchemy ORM for complex join",
    context="Dashboard query with 5 tables",
    outcome="N+1 query issue — rewrote with raw SQL",
    valence=-0.6,
)

print("Projects:", pm.list_projects())   # ['backend', 'frontend']

fe_skills = frontend.crystallize(min_experiences=1, min_confidence=0.5)
print(f"Frontend skills: {len(fe_skills)}")
```

### 5 · Use without an Anthropic API key

```python
# examples/05_no_api_key.py
# Core features work with keyword-based valence and clustering.
# No API key, no anthropic package required — just: pip install engram-forge
from engram_ai.llm.base import BaseLLM
from engram_ai import Forge

class NoLLM(BaseLLM):
    """Stub LLM — disables LLM-powered features."""
    def generate(self, prompt: str) -> str:
        raise NotImplementedError
    def extract_experience(self, messages: list) -> dict | None:
        return None

forge = Forge(llm=NoLLM(), storage_path="/tmp/engram-nokey")

forge.record(
    action="Used pytest fixtures for test setup",
    context="Writing integration tests",
    outcome="Tests are clean and reusable — great",
    valence=0.8,
)

result = forge.query("testing patterns")
print("best:", [(e.action, s) for e, s in result["best"]])

# crystallize() falls back to keyword clustering (no LLM call)
skills = forge.crystallize(min_experiences=1, min_confidence=0.4)
print("skills:", [s.rule for s in skills])
```

### 6 · Observe a conversation and auto-record

```python
# examples/06_observe.py  — requires pip install "engram-forge[claude]"
from engram_ai import Forge

forge = Forge()   # uses ANTHROPIC_API_KEY from env

messages = [
    {"role": "user",      "content": "Can you refactor this function to use a generator?"},
    {"role": "assistant", "content": "Sure — here's the generator version..."},
    {"role": "user",      "content": "Perfect, much cleaner. Thanks!"},
]

result = forge.observe(messages, max_turns=3, crystallize_threshold=5)
if result["recorded"]:
    print(f"Recorded: {result['recorded'].action}")
if result["crystallized"]:
    print(f"New skills: {[s.rule for s in result['crystallized']]}")
```

> See [`examples/`](examples/) for all runnable scripts.

---

## API Reference

### `Forge` — Main Entry Point

```python
from engram_ai import Forge

forge = Forge(
    storage_path="/path/to/data",   # default: ~/.engram-ai/data
    llm=my_llm,                     # BaseLLM instance; None = keyword-only mode
    anthropic_api_key="sk-...",     # alternative to passing llm=
)
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `record` | `(action, context, outcome, valence) → Experience` | Store a completed experience |
| `query` | `(context, k=5) → {"best": [...], "avoid": [...]}` | Retrieve top-k relevant experiences |
| `teach` | `(rule, context_pattern, skill_type, confidence) → Skill` | Directly inject a skill |
| `warn` | `(action, context, threshold=0.6) → list[Experience]` | Get past failures for similar actions |
| `crystallize` | `(min_experiences=3, min_confidence=0.7) → list[Skill]` | Extract skill patterns |
| `evolve` | `(config_path) → EvolutionRecord \| None` | Write skills to agent config |
| `observe` | `(messages, max_turns=3, crystallize_threshold=5) → dict` | Auto-record from conversation |
| `status` | `() → dict` | Return stats (experience count, skill count, …) |
| `detect_conflicts` | `() → list[tuple[Skill, Skill]]` | Find conflicting skill pairs |
| `merge_skills` | `(skill_a_id, skill_b_id) → Skill` | Merge two conflicting skills |
| `apply_decay` | `() → list[Skill]` | Apply time-based confidence decay |
| `on` | `(event_name, callback)` | Subscribe to internal events |

### Extension Points

Swap in your own storage or LLM backend:

```python
from engram_ai.storage import BaseStorage
from engram_ai.llm import BaseLLM
from engram_ai import Forge

class MyStorage(BaseStorage):
    # implement store_experience, query_experiences, store_skill, …
    ...

class MyLLM(BaseLLM):
    def generate(self, prompt: str) -> str:
        return call_my_model(prompt)

forge = Forge(storage=MyStorage(), llm=MyLLM())
```

---

## CLI Reference

```bash
engram-forge setup [--uvx]    # Configure Claude Code (MCP + hooks)
engram-forge setup-hooks       # Register hooks only (no MCP)
engram-forge status            # Show experience / skill counts
engram-forge query "topic"     # Search past experiences
engram-forge crystallize       # Extract skills from experiences
engram-forge evolve            # Write skills to CLAUDE.md
engram-forge serve             # Start MCP server (stdio)
engram-forge dashboard         # Launch web UI (default: http://127.0.0.1:3333)
engram-forge decay             # Apply time-based confidence decay
engram-forge conflicts         # List conflicting skill pairs
engram-forge merge <id_a> <id_b>  # Merge two skills
projects list                  # List all projects
projects delete <name>         # Delete a project
```

**Project scoping:**

```bash
engram-forge -p frontend query "CSS layout"
engram-forge -p backend crystallize
```

---

## MCP Server

When running as an MCP server (`engram-forge serve`), all 10 tools are available to any MCP-compatible client:

| Tool | Key Inputs | Output |
|------|-----------|--------|
| `engram_record` | action, context, outcome, valence, project? | Experience ID |
| `engram_query` | context, k=5, project? | `{best: [...], avoid: [...]}` |
| `engram_crystallize` | min_experiences, min_confidence, project? | Skill list |
| `engram_evolve` | config_path, project? | Diff string |
| `engram_teach` | rule, context_pattern, skill_type, confidence, project? | Skill object |
| `engram_observe` | messages, max_turns, crystallize_threshold, project? | `{recorded, crystallized}` |
| `engram_status` | project? | Stats dict |
| `engram_conflicts` | project? | Conflicting skill pairs |
| `engram_merge` | skill_a_id, skill_b_id, project? | Merged Skill |
| `engram_decay` | project? | Updated skills list |

**Claude Code registration** (done automatically by `engram-forge setup`):

```json
// ~/.claude/settings.json
{
  "mcpServers": {
    "engram-forge": {
      "command": "engram-forge",
      "args": ["serve"]
    }
  }
}
```

**Or with uvx (no pip install required):**

```bash
engram-forge setup --uvx
```

```json
{
  "mcpServers": {
    "engram-forge": {
      "command": "uvx",
      "args": ["engram-forge[mcp]", "serve"]
    }
  }
}
```

---

## Without an Anthropic API Key

All core features degrade gracefully — no API key required for basic use:

| Feature | With API key | Without API key |
|---------|-------------|----------------|
| `record()` valence | LLM sentiment analysis | Keyword matching (JP + EN) |
| `query()` | ChromaDB vector search | Same — unaffected |
| `crystallize()` | LLM extracts pattern names | Keyword-frequency clustering |
| `observe()` | Full extraction | Disabled — returns error with install hint |
| All other tools | Full | Full |

**Keyword valence detection** recognizes common positive/negative signals in English and Japanese out of the box. For precise sentiment analysis, add the `claude` extra:

```bash
pip install "engram-forge[claude]"
export ANTHROPIC_API_KEY=sk-...
```

---

## Multi-Project Support

Engram-AI supports isolated memory namespaces per project:

```python
from pathlib import Path
from engram_ai import ProjectManager

pm = ProjectManager(base_path=Path("~/.engram-ai/data"))

# Each project is completely isolated
frontend_forge = pm.get_forge("my-app/frontend")
backend_forge  = pm.get_forge("my-app/backend")

print(pm.list_projects())          # ['my-app/frontend', 'my-app/backend']
pm.delete_project("my-app/old")    # clean up
```

Via CLI:

```bash
engram-forge -p my-app/frontend query "React component patterns"
engram-forge -p my-app/backend  crystallize
```

Via MCP (all tools accept an optional `project` parameter):

```
engram_record(action="...", context="...", outcome="...", valence=0.8, project="my-app/frontend")
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Forge (Facade)                        │
├──────────┬──────────┬────────────────┬───────────────────────┤
│ Recorder │ Querier  │  Crystallizer  │        Evolver        │
├──────────┴──────────┴────────────────┴───────────────────────┤
│                         EventBus                             │
├────────────────────────┬────────────────────────────────────┤
│    Storage Layer        │            LLM Layer               │
│    (ChromaDB)          │  (Claude API / custom BaseLLM)     │
├────────────────────────┴────────────────────────────────────┤
│              Adapters  (Claude Code · Cursor · Gemini …)    │
└─────────────────────────────────────────────────────────────┘
```

### Two-Phase Recording (Claude Code hooks)

```
PostToolUse Hook              UserPromptSubmit Hook
       │                               │
       ▼                               ▼
 record_pending()  ──────────►  complete_pending()
 (action + context)              (outcome + valence detection)
       │                               │
       ▼                               ▼
  pending.jsonl                  ChromaDB Storage
```

### Valence Detection (tiered)

1. **Keyword matching** — free, works offline, JP + EN patterns
2. **LLM fallback** — Claude API call when keywords are ambiguous
3. **Default 0.3** — mild positive assumption when both fail

### Crystallization Pipeline

```
Experiences ──► Cluster by similarity ──► Extract pattern ──► Skill
                  (ChromaDB cosine)       (LLM or keyword)    (rule + confidence)
```

---

## How It Works — End-to-End Example

```
Day 1  forge.record("Used Optional[str]", "API design", "Rejected by user", -0.8)
Day 2  forge.record("Used Optional[str]", "Config model", "User said avoid nulls", -0.7)
Day 3  forge.record("Used str | None",    "API design", "Accepted — modern style", 0.6)
       ↓ crystallize()
       Skill: "Avoid Optional[str] in models — use 'X | None' syntax"  confidence=0.72
       ↓ evolve("CLAUDE.md")
       → CLAUDE.md updated with learned rule
Day 4  forge.query("API response model design")
       → best: ["Used str | None …"]  avoid: ["Used Optional[str] …"]
```

---

## Web Dashboard

```bash
pip install "engram-forge[dashboard]"
engram-forge dashboard --port 3333
# → http://127.0.0.1:3333
```

| Page | What you see |
|------|-------------|
| **Overview** | Stats cards, valence trend chart, neural graph preview, recent experiences |
| **Experiences** | Searchable / filterable table with expandable detail rows |
| **Skills** | Card grid with confidence bars, one-click crystallize / evolve |
| **Graph** | Force-directed neural graph — hexagon skill nodes, circle experience nodes |

Real-time WebSocket updates — new experiences and skills appear instantly without refresh.

---

## Roadmap

- [x] Core record / query / crystallize / evolve loop
- [x] Two-phase hook-based recording for Claude Code
- [x] MCP server (10 tools)
- [x] Web dashboard with real-time graph
- [x] Multi-project support
- [x] pip + uvx distribution (`engram-forge`)
- [x] Smithery MCP registry
- [ ] Multi-LLM support (OpenAI, Ollama, local models)
- [ ] Skill marketplace — share learned skills across agents
- [ ] Emotion tagging — richer affect beyond scalar valence
- [ ] Experience chains — linked sequences of related experiences
- [ ] Forgetting curves — time-weighted relevance decay
- [ ] Cross-agent transfer — share memory between agent instances
- [ ] Hierarchical memory — episode → skill → meta-skill layers
- [ ] Privacy controls — selective memory, user-controlled deletion

---

## Contributing

We welcome contributions from everyone! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

```bash
git clone https://github.com/kajaha06251020/Engram-AI.git
cd Engram-AI
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[full,dev]"
pytest
ruff check src/ tests/
```

Check out [good first issues](https://github.com/kajaha06251020/Engram-AI/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to get started.

---

## Community

- [GitHub Discussions](https://github.com/kajaha06251020/Engram-AI/discussions) — Questions, ideas, show & tell
- [Discord](https://discord.gg/engram-ai) — Real-time chat
- [Issues](https://github.com/kajaha06251020/Engram-AI/issues) — Bug reports and feature requests

---

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
